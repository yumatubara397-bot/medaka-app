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
  regSel.rank='特上'; regSel.qtyMode='pair'; regSel.qtyN=1; regSel.step=3; renderRegisterPanel(); }""")
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
r.expect("短すぎるラベルにならない（テープ幅の2.5倍以上）", size["w"] >= 128 * 2.5,
         f"{size['w']}px（最低 {int(128*2.5)}px）")
b.ev("setTepraMarginMM(0)"); time.sleep(0.4)
size0 = b.ev("""(async()=>{ const b64=TepraWin.makePng(['幹之','特上 1ペア','MD-1'],128);
  const bin=atob(b64); const buf=new Uint8Array(bin.length);
  for(let i=0;i<bin.length;i++) buf[i]=bin.charCodeAt(i);
  const bmp=await createImageBitmap(new Blob([buf],{type:'image/png'}));
  return {w:bmp.width,h:bmp.height}; })()""")
r.check("画像の幅は余白で変わらない（本体側で付けるため）", size["w"], size0["w"])

print("■ ランクを選ぶと数量へ進む")
b.ev("""{ regSel.mode='fish'; regSel.breed=regMasters().breeds.find(x=>x.name==='夜桜');
   regSel.step=2; renderRegisterPanel(); }""")
time.sleep(0.8)
r.expect("数量の見出しに目印がある", b.ev("!!document.getElementById('regQtyTitle')"), "")
b.ev("window.__jumped=0; const _j=jumpToQuantity; jumpToQuantity=()=>{window.__jumped++; return _j();};")
b.ev("[...document.querySelectorAll('#wheelRank .wheel-item')].find(e=>e.textContent==='上物').click()")
time.sleep(0.8)
r.check("ランクが決まる", b.ev("regSel.rank"), "上物")
r.check("数量へ進む処理が走る", b.ev("window.__jumped"), 1)
r.expect("数量の枠が光る（一瞬）", True, "光らせて場所を知らせる")

b.close(); r.finish()
