"""登録ボタンを押したらすぐテプラから出るかを検証する。"""
import time
from common import Browser, Report

b = Browser(9365, 1200, 1200); r = Report()
b.ev("localStorage.clear();switchTab('register')"); time.sleep(0.6)
# Androidアプリの窓口を真似る
b.ev("""
window.__sent=[];
window.TepraBridge={
  status(){ return JSON.stringify({ok:true,connected:true,printer:'SR-R5600P',tapeMM:24}); },
  connect(){ return JSON.stringify({ok:true,connected:true,printer:'SR-R5600P',tapeMM:24}); },
  print(j){ window.__sent.push(JSON.parse(j)); return JSON.stringify({ok:true,printed:JSON.parse(j).length}); }
};
""")
b.ev("renderRegisterPanel()"); time.sleep(1.0)

print("■ 既定は「登録したらすぐ出す」")
r.check("既定は入", b.ev("tepraAutoOn()"), True)
r.expect("切り替えが出ている", b.ev("!!document.getElementById('tepraAuto')"), "登録したらすぐ出す")
r.check("最初からチェック済み", b.ev("!!(document.getElementById('tepraAuto')||{}).checked"), True)

print("■ 登録を押すとすぐ出る（魚）")
b.ev("""{ regSel.mode='fish'; regSel.breed=regMasters().breeds.find(x=>x.name==='幹之');
  regSel.rank='特上'; regSel.qtyMode='pair'; regSel.qtyN=2; regSel.step=3; renderRegisterPanel(); }""")
time.sleep(0.6)
b.ev("document.getElementById('regDoRegister').click()"); time.sleep(1.5)
r.check("1枚出た", b.ev("window.__sent.length"), 1)
r.check("中身", b.ev("window.__sent[0][0].lines.join('/')"), "幹之/特上 2ペア/" + b.ev("regItems()[0].controlNo"))
r.check("印刷済みになる", b.ev("regUnprinted().length"), 0)

print("■ 経路の判定がまだでも出る")
b.ev("TepraLink._kind = null; window.__sent = [];")
b.ev("""{ regSel.breed=regMasters().breeds.find(x=>x.name==='夜桜');
  regSel.rank='上物'; regSel.qtyN=1; regSel.step=3; renderRegisterPanel(); }""")
time.sleep(0.5)
b.ev("document.getElementById('regDoRegister').click()"); time.sleep(2.0)
r.check("判定してから出す", b.ev("window.__sent.length"), 1)
r.check("経路が決まっている", b.ev("TepraLink._kind"), "android")

print("■ 用品も登録と同時に出る")
b.ev("window.__sent = []; regSel.mode='goods'; regSel.step=1; renderRegisterPanel()"); time.sleep(0.8)
b.ev("""{ regSel.breed=regMasters().goods.find(x=>x.name==='ホテイソウ');
  regSel.qtyN=5; regSel.step=3; renderRegisterPanel(); }""")
time.sleep(0.5)
b.ev("document.getElementById('regDoRegister').click()"); time.sleep(1.5)
r.check("用品も1枚出る", b.ev("window.__sent.length"), 1)
r.check("用品のラベル", b.ev("window.__sent[0][0].lines.join('/')"), "ホテイソウ/5個/" + b.ev("goodsOf('ホテイソウ').fixedNo"))

print("■ 同じ用品を数量だけ変えたときも出し直す")
b.ev("window.__sent = []; regSel.mode='goods'; regSel.step=1; renderRegisterPanel()"); time.sleep(0.6)
b.ev("""{ regSel.breed=regMasters().goods.find(x=>x.name==='ホテイソウ');
  regSel.qtyN=12; regSel.step=3; renderRegisterPanel(); }""")
time.sleep(0.5)
b.ev("document.getElementById('regDoRegister').click()"); time.sleep(1.5)
r.check("出し直す", b.ev("window.__sent.length"), 1)
r.check("新しい数量で出る", b.ev("window.__sent[0][0].lines[1]"), "12個")

print("■ 切り替えを外すと出ない")
b.ev("window.__sent = []; setTepraAuto(false)"); time.sleep(0.5)
r.check("設定が切れる", b.ev("tepraAutoOn()"), False)
b.ev("""{ regSel.mode='fish'; regSel.breed=regMasters().breeds.find(x=>x.name==='オロチ');
  regSel.rank='通常'; regSel.qtyN=1; regSel.step=3; renderRegisterPanel(); }""")
time.sleep(0.5)
b.ev("document.getElementById('regDoRegister').click()"); time.sleep(1.5)
r.check("出ない", b.ev("window.__sent.length"), 0)
r.expect("登録はされる", (b.ev("regItems()") or [])[-1]["variety"] == "オロチ", "オロチ")
r.expect("未印刷として残る", (b.ev("regUnprinted().length") or 0) >= 1, f"{b.ev('regUnprinted().length')}件")
b.ev("setTepraAuto(true)"); time.sleep(0.4)
r.check("戻せる", b.ev("tepraAutoOn()"), True)
r.expect("設定は覚えている", b.ev("localStorage.getItem('medaka_tepra_auto')") == "1", b.ev("localStorage.getItem('medaka_tepra_auto')"))

print("■ テプラが無い端末では静かに何もしない")
b.ev("window.TepraBridge = undefined; TepraLink._kind = null; window.__sent = [];")
b.ev("""{ regSel.breed=regMasters().breeds.find(x=>x.name==='紅白');
  regSel.rank='通常'; regSel.qtyN=1; regSel.step=3; renderRegisterPanel(); }""")
time.sleep(0.5)
b.ev("document.getElementById('regDoRegister').click()"); time.sleep(1.5)
r.check("登録はできる", (b.ev("regItems()") or [])[-1]["variety"], "紅白")
r.check("経路なし", b.ev("TepraLink.kind()"), "none")

b.close(); r.finish()
