from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import cv2,numpy as np,json,io
src=Path('assets/winter_depth.jpg')
out=Path('assets/winter-motion');out.mkdir(parents=True,exist_ok=True)
orig=np.array(Image.open(src).convert('RGB'))
H,W=orig.shape[:2]
# The original repository art is a higher-resolution master (941x1672).
# Normalize only the animated layers to a common image-space reference.
if (W,H)!=(864,1536):
 orig=np.array(Image.fromarray(orig,'RGB').resize((864,1536),Image.Resampling.LANCZOS))
 H,W=orig.shape[:2]
base=orig.copy()
manifest={'width':W,'height':H,'base':'winter_depth_animated_base.webp','lanterns':[],'falls':[],'trees':[],'aurora':None}
def polygon(w,h,pts,blur):
 a=Image.new('L',(w,h),0)
 ImageDraw.Draw(a).polygon(pts,fill=255)
 return np.asarray(a.filter(ImageFilter.GaussianBlur(blur)),dtype='uint8')
def save_frames(name,rect,frames,alpha):
 x,y,w,h=rect
 atlas=Image.new('RGBA',(8*w,h))
 for i,frame in enumerate(frames):
  p=Image.fromarray(np.dstack([frame,alpha]),'RGBA')
  atlas.paste(p,(i*w,0))
 fn='winter_'+name+'.webp'
 atlas.save(out/fn,format='WEBP',quality=89,method=5)
 return fn
lamps=[
 ([27,196,57,72],[29,1],[(28,2),(22,10),(20,16),(17,22),(13,25),(8,31),(11,36),(14,39),(14,60),(19,67),(36,68),(44,59),(44,37),(49,32),(43,27),(37,24),(35,17),(33,12)]),
 ([687,542,51,88],[26,3],[(24,2),(21,15),(20,22),(13,29),(8,34),(3,42),(12,45),(12,70),(19,80),(37,81),(44,70),(44,43),(49,40),(44,34),(35,28),(31,21),(30,11)]),
 ([770,1085,79,109],[40,3],[(42,2),(36,15),(36,23),(29,29),(17,36),(11,45),(17,50),(18,88),(28,99),(52,101),(63,89),(63,51),(73,45),(62,39),(52,29),(47,25),(45,12)]),
 ([121,1208,76,97],[36,3],[(37,2),(30,11),(30,19),(21,26),(13,34),(7,39),(14,44),(15,76),(26,86),(49,87),(62,76),(62,43),(68,38),(57,32),(48,23),(42,20),(41,10)])]
for i,(rect,pivot,pts) in enumerate(lamps):
 x,y,w,h=rect
 a=polygon(w,h,pts,1.25)
 fn='winter_lantern_'+str(i)+'.webp'
 Image.fromarray(np.dstack([orig[y:y+h,x:x+w],a]),'RGBA').save(out/fn,format='WEBP',quality=92,method=5)
 hole=np.zeros((H,W),dtype='uint8')
 hole[y:y+h,x:x+w][a>32]=255
 hole=cv2.dilate(hole,np.ones((3,3),'uint8'),iterations=1)
 base=cv2.inpaint(base,hole,7,cv2.INPAINT_TELEA)
 manifest['lanterns'].append({'file':fn,'rect':rect,'pivot':pivot,'phase':i*1.43})
# Aurora is separated from the SAME sky pixels, with no new painted light curtains.
rect=[145,0,514,554];x,y,w,h=rect;sky=orig[y:y+h,x:x+w]
hsv=cv2.cvtColor(sky,cv2.COLOR_RGB2HSV)
r,g,b=[sky[:,:,i].astype('float32') for i in range(3)]
xx,yy=np.meshgrid(np.arange(x,x+w),np.arange(y,y+h))
cyan=(b>r+23)&(g>r+11)&(g>67)&(b>110)&(hsv[:,:,1]>45)
purple=(b>g+14)&(r>g+8)&(b>85)&(hsv[:,:,1]>36)&(yy>195)
region=(((xx<475)&(yy<380))|((xx>350)&(xx<620)&(yy>220)&(yy<553)))&~(((xx-561)**2+(yy-158)**2)<110**2)
mask=cv2.GaussianBlur(np.uint8((cyan|purple)&region)*255,(0,0),sigmaX=14)
mask=np.uint8(np.clip(mask.astype('float32')*.74,0,205))
base[y:y+h,x:x+w]=np.uint8(np.clip(base[y:y+h,x:x+w].astype('float32')*(1-.49*mask[:,:,None]/255),0,255))
fn='winter_aurora.webp';Image.fromarray(np.dstack([sky,mask]),'RGBA').save(out/fn,format='WEBP',quality=90,method=5)
manifest['aurora']={'file':fn,'rect':rect}
falls=[
 ([645,404,207,248],[(13,7),(197,5),(192,53),(160,172),(138,227),(88,247),(53,226),(42,113),(12,51)],0),
 ([508,694,176,219],[(12,6),(168,3),(161,44),(145,133),(132,207),(56,218),(39,175),(26,62)],2),
 ([349,1128,122,155],[(7,6),(116,1),(109,57),(100,146),(22,154),(17,102),(3,33)],5)]
for i,(rect,pts,phase) in enumerate(falls):
 x,y,w,h=rect;patch=orig[y:y+h,x:x+w]
 poly=polygon(w,h,pts,8).astype('float32')
 rr,gg,bb=[patch[:,:,j].astype('float32') for j in range(3)]
 wet=cv2.GaussianBlur(np.uint8(((bb>rr+10)&(gg>rr-4)&(bb>103)&(gg>100))|((gg>167)&(bb>177)))*255,(0,0),sigmaX=5)
 alpha=np.uint8(poly*wet/255)
 Y,X=np.mgrid[0:h,0:w].astype('float32');frames=[]
 for fi in range(8):
  shift=2.5*np.sin(Y*.045+fi*np.pi/4+phase)*np.sin(np.pi*X/w)
  dy=(fi*2.2)%17.6
  sy=(Y-dy*(.35+.65*np.sin(np.pi*Y/h))).astype('float32')
  frames.append(cv2.remap(patch,(X+shift).astype('float32'),sy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101))
 manifest['falls'].append({'file':save_frames('waterfall_'+str(i),rect,frames,alpha),'rect':rect,'phase':phase,'frames':8})
trees=[
 ([725,228,139,214],5.8,0),([750,726,114,239],5.0,2),
 ([133,969,124,193],4.5,3),([505,436,80,128],3.1,5)]
for i,(rect,amp,phase) in enumerate(trees):
 x,y,w,h=rect;patch=orig[y:y+h,x:x+w]
 Y,X=np.mgrid[0:h,0:w].astype('float32')
 fade=np.power(1-Y/max(1,h-1),1.65)
 frames=[]
 for fi in range(8):
  delta=amp*np.sin(2*np.pi*fi/8+phase)*fade+amp*.25*np.sin(2*np.pi*fi/8+Y*.046)*fade
  frames.append(cv2.remap(patch,(X-delta).astype('float32'),Y,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101))
 alpha=np.uint8(255*np.minimum.reduce([np.clip(X/13,0,1),np.clip((w-1-X)/13,0,1),np.clip(Y/14,0,1),np.clip((h-1-Y)/16,0,1)]))
 manifest['trees'].append({'file':save_frames('tree_'+str(i),rect,frames,alpha),'rect':rect,'phase':phase,'frames':8})
Image.fromarray(base,'RGB').save(out/manifest['base'],format='WEBP',quality=91,method=5)
(out/'winter_motion_manifest.json').write_text(json.dumps(manifest,indent=2))
print('Created',len(list(out.iterdir())),'animation assets, bytes:',sum(x.stat().st_size for x in out.iterdir()))
