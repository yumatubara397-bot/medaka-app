"""ラベルの長さ（余白）／分割されない設定／ランク→数量の自動移動 を検証する。"""
import time
from common import Browser, Report

b = Browser(9368, 1200, 1300); r = Report()
b.ev("localStorage.clear();switchTab('register')"); time.sleep(0.6)
b.ev("""
window.__sent=[];
window.TepraBridge={
  status(){ return JSON.stringify({ok:true,connected:true,printer:'SR-R5600P',tapeMM:24}); },
  connect(){ return JSON.stringify({ok:true,connected:true}); },
  print(j){ window.__sent.push({m:null,l:JSON.parse(j)}); return JSON.stringify({ok:true,printed:1}); },
  printWithMargin(j,m){ window.__sent.push({m:m,l:JSON.parse(j)}); return JSON.stringify({ok:true,printed:1}); }
};
TepraLink._kind=null;""")
b.ev("renderRegisterPanel()"); time.sleep(1.0)

print("■ 余白（ラベルの長さ）の設定")
r.check("既定は6mm", b.ev("tepraMarginMM()"), 6)
r.expect("設定欄が出ている", b.ev("!!document.getElementById('tepraMargin')"), "")
r.check("欄の値も6", b.ev("document.getElementById('tepraMargin').value"), "6")
b.ev("setTepraMarginMM(12)"); time.sleep(0.6)
r.check("変えられる", b.ev("tepraMarginMM()"), 12)
r.check("覚えている", b.ev("localStorage.getItem('medaka_tepra_margin')"), "12")
b.ev("setTepraMarginMM(99)"); time.sleep(0.4)
r.check("大きすぎる値は20に収める", b.ev("tepraMarginMM()"), 20)
b.ev("setTepraMarginMM(0)"); time.sleep(0.4)

print("■ Androidへ余白を渡す")
b.ev("""{ regSel.mode='fish'; regSel.breed=regMasters().breeds.find(x=>x.name==='幹之');
  regSel.rank='特上'; regSel.qtyMode='pair'; regSel.qtyN=1; regSel.step=4; renderRegisterPanel(); }""")
time.sleep(0.5)
b.ev("window.__sent=[]; document.getElementById('regDoRegister').click()"); time.sleep(1.8)
r.check("余白つきで送る", b.ev("window.__sent[0].m"), 0)
b.ev("setTepraMarginMM(10)"); time.sleep(0.4)
b.ev("""{ const l=regItems(); l.forEach(x=>x.tepraExportedAt=null); saveRegItems(l);
   window.__sent=[]; tepraPrintPending(); }""")
time.sleep(1.8)
r.check("変えた余白が反映される", b.ev("window.__sent[0].m"), 10)

print("■ 古いアプリ（余白に対応していない）でも動く")
b.ev("delete window.TepraBridge.printWithMargin;")
b.ev("""{ const l=regItems(); l.forEach(x=>x.tepraExportedAt=null); saveRegItems(l);
   window.__sent=[]; tepraPrintPending(); }""")
time.sleep(1.8)
r.check("従来の呼び方に落ちる", b.ev("window.__sent.length"), 1)
r.check("ラベルの中身は同じ", b.ev("window.__sent[0].l[0].lines[0]"), "幹之")

print("■ Windowsへ送る内容（分割されない設定・余白）")
b.ev("setTepraMarginMM(8)"); time.sleep(0.4)
png = b.ev("TepraWin.makePng(['幹之','特上 1ペア','MD-1'], 128)")
r.expect("画像が作れる", bool(png) and len(png) > 500, f"{len(png or '')}文字")
size = b.ev("""(async()=>{ const b64=TepraWin.makePng(['幹之','特上 1ペア','MD-1'],128);
  const bin=atob(b64); const buf=new Uint8Array(bin.length);
  for(let i=0;i<bin.length;i++) buf[i]=bin.charCodeAt(i);
  const bmp=await createImageBitmap(new Blob([buf],{type:'image/png'}));
  return {w:bmp.width,h:bmp.height}; })()""")
r.check("高さはテープの印字ドット数", size["h"], 128)
r.expect("短すぎるラベルにならない（設定した長さ以上）", size["w"] >= 128 * 1.8,
         f"{size['w']}px（テープ幅の {size['w']/128:.1f}倍 ＝ 約{size['w']/180*25.4:.0f}mm）")
b.ev("setTepraMarginMM(0)"); time.sleep(0.4)
size0 = b.ev("""(async()=>{ const b64=TepraWin.makePng(['幹之','特上 1ペア','MD-1'],128);
  const bin=atob(b64); const buf=new Uint8Array(bin.length);
  for(let i=0;i<bin.length;i++) buf[i]=bin.charCodeAt(i);
  const bmp=await createImageBitmap(new Blob([buf],{type:'image/png'}));
  return {w:bmp.width,h:bmp.height}; })()""")
r.check("画像の幅は余白で変わらない（本体側で付けるため）", size["w"], size0["w"])

print("■ ランクを選ぶと数量の項目へ自動で進む")
b.ev("""{ regSel.mode='fish'; regSel.breed=regMasters().breeds.find(x=>x.name==='夜桜');
   regSel.rank=''; regSel.step=2; renderRegisterPanel(); }""")
time.sleep(0.8)
r.check("いまはランクの画面", b.ev("regSel.step"), 2)
r.expect("ランクのホイールが出ている", b.ev("!!document.getElementById('wheelRank')"), "")
b.ev("[...document.querySelectorAll('#wheelRank .wheel-item')].find(e=>e.textContent==='上物').click()")
time.sleep(1.0)
r.check("ランクが決まる", b.ev("regSel.rank"), "上物")
r.check("数量の画面（③）へ進む", b.ev("regSel.step"), 3)
r.expect("数量のホイールが出ている", b.ev("!!document.getElementById('wheelQty')"), "")
r.expect("ランクのホイールはもう無い", not b.ev("!!document.getElementById('wheelRank')"), "")

print("■ 文字の大きさ（読みやすさ）")
def band_heights(b64):
    import base64 as _b, io as _io
    from PIL import Image as _I
    im = _I.open(_io.BytesIO(_b.b64decode(b64))).convert("L")
    w, h = im.size; px = im.load()
    rows = [any(px[x, y] < 128 for x in range(0, w, 2)) for y in range(h)]
    out, st = [], None
    for y, on in enumerate(rows):
        if on and st is None: st = y
        if not on and st is not None: out.append(y - st); st = None
    if st is not None: out.append(h - st)
    return out

b.ev("setTepraRows(3); setTepraMinLenRatio(3.5)"); time.sleep(0.4)
h3 = band_heights(b.ev("TepraWin.makePng(fitLabelRows(['忘却の翼','通常 雄5 雌8','MD-260902-004']), 128)"))
r.expect("3行でも品種名は5mm以上", h3 and h3[0] >= 36, f"{h3[0]}ドット = {h3[0]/180*25.4:.1f}mm")
r.expect("3行の管理番号も3mm以上", len(h3) >= 3 and h3[2] >= 21, f"{h3[-1]}ドット = {h3[-1]/180*25.4:.1f}mm")

b.ev("setTepraRows(2)"); time.sleep(0.4)
lines2 = b.ev("fitLabelRows(['忘却の翼','通常 雄5 雌8','MD-260902-004'])")
r.check("2行にまとまる", len(lines2 or []), 2)
r.check("1行目は品種名のまま", (lines2 or [""])[0], "忘却の翼")
r.expect("2行目に数量と管理番号が入る",
         "雄5" in (lines2 or ["",""])[1] and "MD-260902-004" in (lines2 or ["",""])[1], str(lines2))
h2 = band_heights(b.ev("TepraWin.makePng(fitLabelRows(['忘却の翼','通常 雄5 雌8','MD-260902-004']), 128)"))
r.expect("2行にすると文字が大きくなる", h2[0] > h3[0] and h2[1] > h3[1],
         f"3行 {h3[0]}/{h3[1]}ドット → 2行 {h2[0]}/{h2[1]}ドット")
r.expect("2行目でも5mm以上", h2[1] >= 36, f"{h2[1]}ドット = {h2[1]/180*25.4:.1f}mm")

print("■ 長さの選択")
b.ev("setTepraRows(3); setTepraMinLenRatio(1.8)"); time.sleep(0.3)
w25 = b.ev("(async()=>{const b64=TepraWin.makePng(['あ','い','う'],128);const bin=atob(b64);const u=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)u[i]=bin.charCodeAt(i);const m=await createImageBitmap(new Blob([u],{type:'image/png'}));return m.width;})()")
b.ev("setTepraMinLenRatio(4.5)"); time.sleep(0.3)
w6 = b.ev("(async()=>{const b64=TepraWin.makePng(['あ','い','う'],128);const bin=atob(b64);const u=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)u[i]=bin.charCodeAt(i);const m=await createImageBitmap(new Blob([u],{type:'image/png'}));return m.width;})()")
r.expect("長さを変えられる", w6 > w25, f"短め {w25}px → もっと長く {w6}px")
r.expect("画面から選べる", b.ev("!!document.getElementById('tepraLen')") and b.ev("!!document.getElementById('tepraRows')"), "")

b.close(); r.finish()
