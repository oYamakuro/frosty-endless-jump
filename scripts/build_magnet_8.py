from PIL import Image, ImageFilter
import cairosvg, io, math, os
os.makedirs("assets",exist_ok=True)
base=Image.open(io.BytesIO(cairosvg.svg2png(url="assets/frost_magnet_vector.svg",output_width=180,output_height=180))).convert("RGBA")
sheet=Image.new("RGBA",(128*8,128))
for i in range(8):
    a=2*math.pi*i/8
    w=max(8,round(112*abs(math.cos(a))))
    face=base if math.cos(a)>=0 else base.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    face=face.resize((w,112),Image.Resampling.LANCZOS)
    layer=Image.new("RGBA",(128,128))
    layer.alpha_composite(face,((128-w)//2,8))
    if i in (2,6):
        edge=Image.new("RGBA",(128,128))
        from PIL import ImageDraw
        d=ImageDraw.Draw(edge)
        d.rounded_rectangle((59,13,69,115),radius=4,fill=(80,213,255,255),outline=(230,250,255,255),width=2)
        layer=Image.alpha_composite(layer,edge)
    glow=layer.filter(ImageFilter.GaussianBlur(6))
    glow.putalpha(glow.getchannel("A").point(lambda p:round(p*.55)))
    out=Image.alpha_composite(glow,layer)
    sheet.alpha_composite(out,(128*i,0))
sheet.save("assets/frost_magnet_8frames.png",optimize=True)
