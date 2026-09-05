# -*- coding: utf-8 -*-
"""AI編集の「拡大・縮小」ゲージ。コントラストと同じように動かせて、保存にも効くこと。"""
import time, base64, io
from common import Browser, Report
from PIL import Image

b = Browser(9405, 1200, 1000); r = Report()
b.ev("localStorage.clear()"); time.sleep(0.3)

print("■ ゲージとして並んでいる")
r.expect("拡大・縮小がある", "zoom" in (b.ev("ADJ_SLIDERS.map(s=>s.k).join(',')") or ""),
         b.ev("ADJ_SLIDERS.map(s=>s.k).join(',')"))
r.check("名前", b.ev("(ADJ_SLIDERS.find(s=>s.k==='zoom')||{}).label"), "拡大・縮小")
r.check("下限は50%", b.ev("(ADJ_SLIDERS.find(s=>s.k==='zoom')||{}).min"), 50)
r.check("上限は300%", b.ev("(ADJ_SLIDERS.find(s=>s.k==='zoom')||{}).max"), 300)
r.check("%で表示する", b.ev("fmtAdj(ADJ_SLIDERS.find(s=>s.k==='zoom'), 120)"), "120%")
r.check("コントラストは符号付きのまま", b.ev("fmtAdj(ADJ_SLIDERS.find(s=>s.k==='contrast'), 12)"), "+12")

print("■ 何もしない値は 100%")
r.check("はじめは100", b.ev("ADJ_DEFAULT.zoom"), 100)
r.check("100なら「調整なし」扱い", b.ev("isAdjNeutral({bright:0,contrast:0,sat:0,warm:0,sharp:0,rot:0,zoom:100})"), True)
r.check("拡大していれば調整あり扱い", b.ev("isAdjNeutral({bright:0,contrast:0,sat:0,warm:0,sharp:0,rot:0,zoom:120})"), False)
r.check("縮小でも調整あり扱い", b.ev("isAdjNeutral({bright:0,contrast:0,sat:0,warm:0,sharp:0,rot:0,zoom:80})"), False)
r.check("古い保存（拡大が無い）も調整なし扱い",
        b.ev("isAdjNeutral({bright:0,contrast:0,sat:0,warm:0,sharp:0,rot:0})"), True)
r.check("古い保存はゲージで100に見える", b.ev("adjVal({contrast:10}, 'zoom')"), 100)
r.check("コントラストは0のまま", b.ev("adjVal({}, 'contrast')"), 0)
r.check("行き過ぎた値は範囲に収める", b.ev("adjZoom({zoom:9999})"), 300)
r.check("小さすぎる値も収める", b.ev("adjZoom({zoom:1})"), 50)

print("■ 実際に絵が変わる")
# 中央に黒い四角を置いた白い画像を作る
b.ev(r"""
window.__mk = () => new Promise(res => {
  const c = document.createElement('canvas'); c.width = 100; c.height = 100;
  const x = c.getContext('2d');
  x.fillStyle = '#fff'; x.fillRect(0,0,100,100);
  x.fillStyle = '#000'; x.fillRect(40,40,20,20);     // 中央に20x20の黒
  c.toBlob(b => res(b), 'image/png');
});
window.__px = async (blob) => {
  const bmp = await createImageBitmap(blob);
  const c = document.createElement('canvas'); c.width = bmp.width; c.height = bmp.height;
  c.getContext('2d').drawImage(bmp, 0, 0);
  const d = c.getContext('2d').getImageData(0,0,c.width,c.height).data;
  let dark = 0;
  for(let i=0;i<d.length;i+=4) if(d[i] < 128) dark++;
  return {w:c.width, h:c.height, dark};
};
'ok'""")

base = b.ev("(async()=>{ window.__b = await __mk(); return JSON.stringify(await __px(window.__b)); })()")
import json
base = json.loads(base)
r.check("元は100x100", f"{base['w']}x{base['h']}", "100x100")
r.check("黒い部分は400画素", base["dark"], 400)

big = json.loads(b.ev("(async()=>JSON.stringify(await __px(await zoomBlob(window.__b, 200))))()"))
r.check("拡大しても大きさは変わらない", f"{big['w']}x{big['h']}", "100x100")
r.expect("2倍にすると黒い部分がおよそ4倍になる", 1500 < big["dark"] < 1750, f"{big['dark']}画素")

small = json.loads(b.ev("(async()=>JSON.stringify(await __px(await zoomBlob(window.__b, 50))))()"))
r.check("縮小しても大きさは変わらない", f"{small['w']}x{small['h']}", "100x100")
r.expect("半分にすると黒い部分がおよそ1/4になる", 60 < small["dark"] < 140, f"{small['dark']}画素")

print("■ 縮小したときの余白は白（出品写真の背景に合わせる）")
corner = b.ev("""(async()=>{
  const blob = await zoomBlob(window.__b, 50);
  const bmp = await createImageBitmap(blob);
  const c = document.createElement('canvas'); c.width=bmp.width; c.height=bmp.height;
  c.getContext('2d').drawImage(bmp,0,0);
  const d = c.getContext('2d').getImageData(0,0,1,1).data;
  return d[0]+','+d[1]+','+d[2];
})()""")
r.check("左上の隅は白", corner, "255,255,255")

print("■ 100%なら何もしない")
same = b.ev("(async()=>{ const out = await zoomBlob(window.__b, 100); return out === window.__b; })()")
r.check("同じものをそのまま返す（無駄に作り直さない）", same, True)

print("■ リセットで100%に戻る")
b.ev("photoAdjust[0] = {bright:10, contrast:20, sat:0, warm:0, sharp:0, rot:0, zoom:180}; 'ok'")
r.check("拡大が入っている", b.ev("getAdj(0).zoom"), 180)
b.ev("resetPhotoAdj(0)"); time.sleep(0.3)
r.check("リセットで100に戻る", b.ev("getAdj(0).zoom"), 100)

b.close(); r.finish()
