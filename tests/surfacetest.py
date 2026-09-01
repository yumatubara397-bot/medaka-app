"""Surface（Windows）向け：用品はテプラを出さない／繋がらないときの案内／ローカル保存。"""
import time
from common import Browser, Report

b = Browser(9366, 1200, 1200); r = Report()
b.ev("localStorage.clear();switchTab('register')"); time.sleep(0.6)
b.ev("""
window.__sent=[];
window.TepraBridge={
  status(){ return JSON.stringify({ok:true,connected:true,printer:'SR-R5600P',tapeMM:24}); },
  connect(){ return JSON.stringify({ok:true,connected:true,printer:'SR-R5600P',tapeMM:24}); },
  print(j){ window.__sent.push(JSON.parse(j)); return JSON.stringify({ok:true,printed:1}); }
};
TepraLink._kind=null;""")
b.ev("renderRegisterPanel()"); time.sleep(1.0)

print("■ 魚は今までどおり出る")
b.ev("""{ regSel.mode='fish'; regSel.breed=regMasters().breeds.find(x=>x.name==='幹之');
  regSel.rank='特上'; regSel.qtyMode='pair'; regSel.qtyN=2; regSel.step=3; renderRegisterPanel(); }""")
time.sleep(0.5)
b.ev("document.getElementById('regDoRegister').click()"); time.sleep(1.5)
r.check("魚は1枚出る", b.ev("window.__sent.length"), 1)

print("■ 用品はテプラを出さない")
b.ev("window.__sent=[]; regSel.mode='goods'; regSel.step=1; renderRegisterPanel()"); time.sleep(0.7)
b.ev("""{ regSel.breed=regMasters().goods.find(x=>x.name==='ホテイソウ');
  regSel.qtyN=5; regSel.step=3; renderRegisterPanel(); }""")
time.sleep(0.5)
b.ev("document.getElementById('regDoRegister').click()"); time.sleep(1.5)
r.check("用品は出ない", b.ev("window.__sent.length"), 0)
r.check("登録はされる", b.ev("regItems().filter(x=>x.kind==='goods').length"), 1)

print("■ 用品はまとめ印刷の対象にもならない")
b.ev("{const l=regItems(); l.forEach(x=>x.tepraExportedAt=null); saveRegItems(l);} renderRegisterPanel()")
time.sleep(0.8)
r.check("未印刷は魚の1件だけ", b.ev("regUnprinted().length"), 1)
r.expect("用品は含まれない", b.ev("regUnprinted().every(x=>x.kind!=='goods')"), 
         str(b.ev("regUnprinted().map(x=>x.variety)")))
b.ev("window.__sent=[]; tepraPrintPending()"); time.sleep(1.5)
r.check("まとめても魚1枚だけ", b.ev("window.__sent[0].length"), 1)
r.check("出たのは魚", b.ev("window.__sent[0][0].lines[0]"), "幹之")

print("■ パソコンで繋がらないときの案内")
b.ev("""{ window.TepraBridge=undefined; TepraLink._kind='none';
   TepraWin.lastError='つながりません。通信モジュールが起動していないか、ブラウザが止めています';
   renderTepraBar(); }""")
time.sleep(1.0)
txt = b.ev("document.getElementById('regTepraBar').textContent") or ""
r.expect("案内が出る", "つながりません" in txt, txt.strip()[:70])
r.expect("もう一度ためすがある", b.ev("!!document.getElementById('tepraRetry')"), "")
r.expect("対処を見るがある", b.ev("!!document.getElementById('tepraHelp')"), "")
help_text = b.ev("TEPRA_WIN_HELP")
r.expect("対処にテプラ クリエイターの入手先", "tepra_creator" in (help_text or ""), "")
r.expect("対処に通信モジュールの確認方法", "localhost:29108" in (help_text or ""), "")
r.expect("対処にローカル保存の案内", "このパソコンに保存" in (help_text or ""), "")

print("■ ローカル保存")
b.ev("switchTab('settings')"); time.sleep(0.5)
r.expect("保存ボタンがある", b.ev("!!document.getElementById('btnSaveLocal')"), "💾 このパソコンに保存")
b.ev("""{ window.__saved=null; window.downloadBlob=(bl,n)=>{ window.__saved={name:n,size:bl.size}; }; }""")
b.ev("document.getElementById('btnSaveLocal').click()"); time.sleep(2.5)
saved = b.ev("window.__saved")
r.expect("HTMLとして保存される", saved and saved["name"].endswith(".html"), str(saved))
r.expect("中身がある", saved and saved["size"] > 100000, f"{(saved or {}).get('size')}バイト")

b.close(); r.finish()
