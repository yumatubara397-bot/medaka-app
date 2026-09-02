"""白紙のラベルが出ない／二重に印刷されないことを検証する。"""
import time
from common import Browser, Report

b = Browser(9369, 1200, 1200); r = Report()
b.ev("localStorage.clear();switchTab('register')"); time.sleep(0.6)
b.ev("""
window.__sent=[];
window.TepraBridge={
  status(){ return JSON.stringify({ok:true,connected:true,printer:'SR-R5600P',tapeMM:24}); },
  connect(){ return JSON.stringify({ok:true,connected:true}); },
  printWithMargin(j,m){ window.__sent.push(JSON.parse(j)); return JSON.stringify({ok:true,printed:1}); }
};
TepraLink._kind=null;""")
b.ev("renderRegisterPanel()"); time.sleep(1.0)

print("■ 中身が空の商品は送らない")
res = b.ev("TepraLink.print([{variety:'',rank:'',quantityText:'',controlNo:''}])")
r.check("送らない", b.ev("window.__sent.length"), 0)
r.check("断る", res.get("ok"), False)
r.expect("理由が出る", "書く内容がありません" in (res.get("error") or ""), res.get("error"))

print("■ 空のものが混ざっていても、中身のあるものだけ送る")
b.ev("window.__sent=[]")
res = b.ev("""TepraLink.print([
  {variety:'幹之',rank:'特上',quantityText:'2ペア',controlNo:'MD-1'},
  {variety:'',rank:'',quantityText:'',controlNo:''},
  {variety:'夜桜',rank:'上物',quantityText:'1ペア',controlNo:'MD-2'}])""")
time.sleep(0.5)
r.check("2枚だけ送る", b.ev("window.__sent[0].length"), 2)
r.check("成功として返る", res.get("ok"), True)
r.expect("飛ばしたものを知らせる", bool(res.get("skipped")), str(res.get("skipped")))

print("■ 管理番号だけでも印刷できる")
b.ev("window.__sent=[]")
res = b.ev("TepraLink.print([{variety:'',rank:'',quantityText:'',controlNo:'MD-9'}])")
time.sleep(0.4)
r.check("1枚送る", b.ev("window.__sent[0].length"), 1)
r.check("その1行だけ", b.ev("JSON.stringify(window.__sent[0][0].lines)"), '["MD-9"]')

print("■ 二重に走らせない")
b.ev("""window.__slow=[]; window.TepraBridge.printWithMargin=(j,m)=>{
  window.__slow.push(JSON.parse(j));
  const t=Date.now(); while(Date.now()-t<300){}   // わざと遅くする
  return JSON.stringify({ok:true,printed:1}); };""")
b.ev("""window.__r1=null; window.__r2=null;
  TepraLink.print([{variety:'幹之',rank:'特上',quantityText:'1ペア',controlNo:'MD-A'}]).then(x=>window.__r1=x);
  TepraLink.print([{variety:'幹之',rank:'特上',quantityText:'1ペア',controlNo:'MD-A'}]).then(x=>window.__r2=x);""")
time.sleep(2.0)
r.check("送ったのは1回だけ", b.ev("window.__slow.length"), 1)
r.expect("2つ目は断られる",
         (b.ev("window.__r1") or {}).get("ok") != (b.ev("window.__r2") or {}).get("ok"),
         f"1つ目={b.ev('window.__r1')} / 2つ目={b.ev('window.__r2')}")
r.expect("断る理由が分かる", "印刷しています" in ((b.ev("window.__r2") or {}).get("error") or ""),
         (b.ev("window.__r2") or {}).get("error"))
r.check("終われば次が通る", b.ev("TepraLink._busy"), False)

print("■ 白紙の画像は作らない（Windows側）")
r.expect("文字があれば作れる", bool(b.ev("TepraWin.makePng(['幹之','特上 2ペア','MD-1'],128)")), "")
blank = b.ev("""(()=>{ try { TepraWin.makePng([],128); return 'つくれてしまった'; }
   catch(e){ return 'ERR:'+e.message; } })()""")
r.expect("行が空なら作らない", str(blank).startswith("ERR:"), str(blank))
blank2 = b.ev("""(()=>{ try { TepraWin.makePng([' ','  '],128); return 'つくれてしまった'; }
   catch(e){ return 'ERR:'+e.message; } })()""")
r.expect("空白だけでも作らない", str(blank2).startswith("ERR:"), str(blank2))

print("■ 白紙かどうかの判定そのもの")
r.check("白紙は false", b.ev("""(()=>{const cv=document.createElement('canvas');cv.width=200;cv.height=128;
  const c=cv.getContext('2d');c.fillStyle='#fff';c.fillRect(0,0,200,128);
  return hasInk(c,200,128);})()"""), False)
r.check("文字があれば true", b.ev("""(()=>{const cv=document.createElement('canvas');cv.width=200;cv.height=128;
  const c=cv.getContext('2d');c.fillStyle='#fff';c.fillRect(0,0,200,128);
  c.fillStyle='#000';c.font='bold 60px sans-serif';c.fillText('幹之',10,80);
  return hasInk(c,200,128);})()"""), True)

b.close(); r.finish()
