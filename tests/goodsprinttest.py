"""用品は「選んで発行」を押したものだけ出ることを検証する。"""
import time
from common import Browser, Report

b = Browser(9367, 1200, 1200); r = Report()
b.ev("localStorage.clear();switchTab('register')"); time.sleep(0.6)
b.ev("""
window.__sent=[];
window.TepraBridge={
  status(){ return JSON.stringify({ok:true,connected:true,printer:'SR-R5600P',tapeMM:24}); },
  connect(){ return JSON.stringify({ok:true,connected:true,printer:'SR-R5600P',tapeMM:24}); },
  print(j){ window.__sent.push(JSON.parse(j)); return JSON.stringify({ok:true,printed:JSON.parse(j).length}); }
};
TepraLink._kind=null;""")
b.ev("renderRegisterPanel()"); time.sleep(1.0)

print("■ 用品を3件、魚を1件 登録する")
b.ev("""{ regSel.mode='goods';
  [['ホテイソウ',5],['ラムズホーン',10],['岩塩',2]].forEach(([nm,q])=>{
    regSel.breed=regMasters().goods.find(x=>x.name===nm);
    regSel.qtyN=q; regSel.step=3; regDoRegister(); }); }""")
time.sleep(1.5)
b.ev("""{ regSel.mode='fish'; regSel.breed=regMasters().breeds.find(x=>x.name==='幹之');
  regSel.rank='特上'; regSel.qtyMode='pair'; regSel.qtyN=1; regSel.step=4; regDoRegister(); }""")
time.sleep(1.5)
r.check("4件登録", b.ev("regItems().length"), 4)
r.check("登録時に出たのは魚の1枚だけ", b.ev("window.__sent.length"), 1)
r.check("出たのは幹之", b.ev("window.__sent[0][0].lines[0]"), "幹之")

print("■ 用品にはチェックが出る")
r.check("チェックは用品の3つ", b.ev("document.querySelectorAll('#regItemList .gpick').length"), 3)
r.check("魚の行にはチェックが無い",
        b.ev("[...document.querySelectorAll('#regItemList .reg-item')].filter(x=>!x.querySelector('.gpick')).length"), 1)
r.expect("選ぶまで発行ボタンは押せない", b.ev("document.getElementById('regGoodsPrint').disabled"),
         b.ev("document.getElementById('regGoodsPrint').textContent"))

print("■ 選んだものだけ出る")
b.ev("""{ const cs=[...document.querySelectorAll('#regItemList .gpick')];
   const pick = cs.filter(c=>['ホテイソウ','岩塩'].some(n=>c.closest('.reg-item').textContent.includes(n)));
   pick.forEach(c=>{ c.checked=true; c.dispatchEvent(new Event('change',{bubbles:true})); }); }""")
time.sleep(0.8)
r.check("2件選んだ", b.ev("goodsPicked.size"), 2)
r.expect("ボタンに件数が出る", "2件を発行" in (b.ev("document.getElementById('regGoodsPrint').textContent") or ""),
         b.ev("document.getElementById('regGoodsPrint').textContent"))
b.ev("window.__sent=[]; document.getElementById('regGoodsPrint').click()"); time.sleep(2.0)
r.check("1回でまとめて送る", b.ev("window.__sent.length"), 1)
r.check("2枚だけ出た", b.ev("window.__sent[0].length"), 2)
sent = b.ev("window.__sent[0].map(x=>x.lines[0])")
r.expect("出たのは選んだ用品", set(sent or []) == {"ホテイソウ","岩塩"}, str(sent))
r.expect("選んでいないラムズホーンは出ない", "ラムズホーン" not in (sent or []), str(sent))

print("■ 出したら印になり、選択は外れる")
r.check("選択は空に戻る", b.ev("goodsPicked.size"), 0)
r.check("出した2件に印がつく",
        b.ev("regItems().filter(x=>x.kind==='goods'&&x.tepraExportedAt).length"), 2)
r.check("ラムズホーンは未発行",
        b.ev("!!regItems().find(x=>x.variety==='ラムズホーン').tepraExportedAt"), False)

print("■ 何度でも出せる（同じものを選び直せる）")
b.ev("""{ const c=[...document.querySelectorAll('#regItemList .gpick')]
     .find(x=>x.closest('.reg-item').textContent.includes('ホテイソウ'));
   c.checked=true; c.dispatchEvent(new Event('change',{bubbles:true})); }""")
time.sleep(0.6)
b.ev("window.__sent=[]; document.getElementById('regGoodsPrint').click()"); time.sleep(2.0)
r.check("もう一度出せる", b.ev("window.__sent[0].length"), 1)
r.check("出たのはホテイソウ", b.ev("window.__sent[0][0].lines[0]"), "ホテイソウ")

print("■ 魚のまとめ印刷に用品は混ざらない")
b.ev("{const l=regItems(); l.forEach(x=>x.tepraExportedAt=null); saveRegItems(l);} renderRegisterPanel()")
time.sleep(0.8)
r.check("未印刷は魚だけ", b.ev("regUnprinted().length"), 1)
b.ev("window.__sent=[]; tepraPrintPending()"); time.sleep(1.5)
r.check("魚1枚だけ出る", b.ev("window.__sent[0].length"), 1)
r.check("それは幹之", b.ev("window.__sent[0][0].lines[0]"), "幹之")

print("■ 用品を消すと選択も消える")
b.ev("""{ goodsPicked.add(regItems().find(x=>x.variety==='ラムズホーン').controlNo);
   saveRegItems(regItems().filter(x=>x.variety!=='ラムズホーン')); renderRegItems(); }""")
time.sleep(0.6)
r.check("消えた用品は選択から外れる", b.ev("goodsPicked.size"), 0)

b.close(); r.finish()
