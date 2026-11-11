"""Functional v1.7 checks; run with Python Playwright and Chromium/WebKit."""
import functools
import http.server
import json
import os
from pathlib import Path
import shutil
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = Path(os.environ.get('FROSTY_TEST_ARTIFACTS', '/tmp/frosty-v1.7-tests'))
ARTIFACTS.mkdir(parents=True, exist_ok=True)

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
url = f'http://127.0.0.1:{server.server_port}'
# Instrument only the response served to this test; production exposes no test hooks.
source = (ROOT / 'FROSTY_v1_7_index.html').read_text()
hook = '''window.__test={step:update, get:()=>({p:{...p},score,collected,camera,scene}),
 set:(data)=>{if(data.p)p={...p,...data.p};if(data.platforms)platforms=data.platforms;
 if(data.tokens)tokens=data.tokens;if(data.camera!==undefined)camera=data.camera;},
 render, start};'''
source = source.replace('requestAnimationFrame(frame);})();', hook + 'requestAnimationFrame(frame);})();')

try:
    with sync_playwright() as pw:
        for name in ['desktop', 'iphone']:
            engine = pw.chromium if name == 'desktop' or os.environ.get('FROSTY_MOBILE_ENGINE') == 'chromium' else pw.webkit
            options = {'headless': True}
            if engine.name == 'chromium' and shutil.which('chromium'):
                options['executable_path'] = shutil.which('chromium')
            browser = engine.launch(**options)
            config = {'viewport': {'width': 1440, 'height': 900}} if name == 'desktop' else pw.devices['iPhone 13']
            context = browser.new_context(**config)
            page = context.new_page()
            errors, failed = [], []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('response', lambda r: failed.append(r.url) if r.status >= 400 else None)
            page.route('**/FROSTY_v1_7_index.html', lambda route: route.fulfill(status=200, content_type='text/html', body=source))
            page.goto(url, wait_until='networkidle')
            page.wait_for_url('**/FROSTY_v1_7_index.html')
            assert 'v1.7' in page.title()
            assert page.locator('#menu').is_visible()
            assert page.locator('h1').first.bounding_box()['y'] >= 0
            page.click('#play');assert page.locator('#hud').is_visible()
            page.click('#pause');page.click('#toMenu')
            assert page.locator('img').evaluate_all('(xs)=>xs.every(i=>i.complete&&i.naturalWidth>0)')
            # Verify alpha transparency and sprite borders in the actual browser decoder.
            alpha = page.evaluate('''async()=>{const out=[];for(const n of ['a','b','c']){
              const i=new Image();i.src='assets/rock_'+n+'.png?v=1.7';await i.decode();
              const c=document.createElement('canvas');c.width=i.width;c.height=i.height;
              const x=c.getContext('2d');x.drawImage(i,0,0);const d=x.getImageData(0,0,c.width,c.height).data;
              let clear=0;for(let k=3;k<d.length;k+=4)if(d[k]===0)clear++;
              out.push(clear/(c.width*c.height));}return out}''')
            assert all(v > .30 for v in alpha), alpha
            page.screenshot(path=str(ARTIFACTS / f'{name}-menu.png'))
            page.click('#settingsBtn')
            page.select_option('#steer', 'touch' if name == 'desktop' else 'swipe')
            page.select_option('#mode', 'manual')
            page.locator('#musicVol').fill('40');page.locator('#musicVol').dispatch_event('input')
            page.click('#back');page.click('[data-char=lunar]');page.click('#play')
            assert page.locator('#hud').is_visible()
            # Deterministic physics checks within a single task, before RAF can intervene.
            result = page.evaluate('''()=>{const t=window.__test;const pl={x:50,y:400,w:250,boost:false,kind:0};
              t.set({camera:0,platforms:[pl],tokens:[],p:{x:150,y:363,vy:2,vx:0,h:72,onGround:false}});
              t.step(1);if(!t.get().p.onGround)throw Error('Manual landing failed');
              dispatchEvent(new KeyboardEvent('keydown',{key:' '}));t.step(1);
              if(t.get().p.vy>=0)throw Error('Manual jump failed');dispatchEvent(new KeyboardEvent('keyup',{key:' '}));
              document.querySelector('#mode').value='auto';pl.boost=true;
              t.set({platforms:[pl],p:{x:150,y:363,vy:2,vx:0,onGround:false}});t.step(1);
              if(t.get().p.vy!==-17.5)throw Error('Booster failed');
              pl.boost=false;t.set({platforms:[pl],p:{x:150,y:363,vy:2,onGround:false}});t.step(1);
              if(t.get().p.vy!==-12.7)throw Error('Auto jump failed');
              const before=t.get().collected;t.set({tokens:[{x:150,y:300,got:false,phase:0}],p:{x:150,y:300,vy:0}});t.step(0);
              if(t.get().collected!==before+1)throw Error('Coin failed');return t.get()}''')
            if name == 'desktop':
                before = page.evaluate('window.__test.get().p.x')
                page.keyboard.down('ArrowRight');page.wait_for_timeout(120);page.keyboard.up('ArrowRight')
                assert page.evaluate('window.__test.get().p.x') > before
            else:
                page.evaluate('''()=>{document.querySelector('#game').dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,pointerId:1,clientX:100}));
                document.dispatchEvent(new PointerEvent('pointermove',{bubbles:true,pointerId:1,clientX:180}));}''')
                before = page.evaluate('window.__test.get().p.x');page.wait_for_timeout(120)
                assert page.evaluate('window.__test.get().p.x') > before
                page.evaluate("document.dispatchEvent(new PointerEvent('pointerup',{pointerId:1}))")
            page.click('#pause');assert page.locator('#paused').is_visible()
            before = page.evaluate('window.__test.get().p.y');page.wait_for_timeout(150)
            assert page.evaluate('window.__test.get().p.y') == before
            page.click('#resume');assert page.locator('#paused').is_hidden()
            page.evaluate('window.__test.start();window.__test.render(performance.now())')
            page.screenshot(path=str(ARTIFACTS / f'{name}-game.png'))
            page.click('#muteHud');assert page.locator('#muteHud').get_attribute('aria-pressed') == 'true'
            page.click('#pause');page.click('#toMenu');page.reload(wait_until='networkidle')
            page.click('#settingsBtn');assert page.locator('#musicVol').input_value() == '40'
            assert page.locator('#muteSettings').get_attribute('aria-pressed') == 'true'
            assert not errors, errors
            assert not failed, failed
            print(json.dumps({'target': name, 'engine': engine.name, 'status': 'PASS', 'transparent_fraction': alpha, 'errors': errors, 'failed_requests': failed}))
            context.close();browser.close()
finally:
    server.shutdown()
