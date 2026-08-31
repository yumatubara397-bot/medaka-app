"""ランク・数量のホイールピッカーを検証する。"""
import time, datetime, json
from common import Browser, Report

b = Browser(9351); r = Report()
today = datetime.date.today().strftime("%y%m%d")
b.ev("localStorage.clear();switchTab('register');renderRegisterPanel()"); time.sleep(0.8)

print("■ ステップは3つになった")
r.check("ステップ数", b.ev("document.querySelectorAll('#regSteps .reg-step').length"), 3)
r.expect("②の名前", (b.ev("document.querySelectorAll('#regSteps .reg-step')[1].textContent.replace(/\\s+/g,'')") or "").startswith("2ランク・数量"),
         b.ev("document.querySelectorAll('#regSteps .reg-step')[1].textContent.replace(/\\s+/g,'')"))

print("■ 品種を選ぶと②へ")
b.ev("[...document.querySelectorAll('#regBreedList button')].find(x=>x.querySelector('.bn').textContent==='幹之').click()")
time.sleep(0.8)
r.check("ステップ②", b.ev("regSel.step"), 2)

print("■ ランクのホイール")
ranks = b.ev("[...document.querySelectorAll('#wheelRank .wheel-item')].map(e=>e.textContent)")
r.check("ランクの中身", ranks, ["特上","上物","通常","若魚"])
r.check("最初は特上", b.ev("regSel.rank"), "特上")
b.ev("[...document.querySelectorAll('#wheelRank .wheel-item')].find(e=>e.textContent==='上物').click()"); time.sleep(0.5)
r.check("押して選べる", b.ev("regSel.rank"), "上物")
r.expect("選んだ行が強調される",
         "on" in (b.ev("[...document.querySelectorAll('#wheelRank .wheel-item')].find(e=>e.textContent==='上物').className") or ""),
         b.ev("[...document.querySelectorAll('#wheelRank .wheel-item')].find(e=>e.textContent==='上物').className"))

print("■ 数量：ペア")
r.check("最初はペア", b.ev("regSel.qtyMode"), "pair")
r.check("1〜100が並ぶ", b.ev("document.querySelectorAll('#wheelQty .wheel-item').length"), 100)
r.check("最初は1", b.ev("document.querySelectorAll('#wheelQty .wheel-item')[0].textContent"), "1")
r.check("最後は100", b.ev("document.querySelectorAll('#wheelQty .wheel-item')[99].textContent"), "100")
b.ev("[...document.querySelectorAll('#wheelQty .wheel-item')].find(e=>e.textContent==='3').click()"); time.sleep(0.5)
r.check("3ペアになる", b.ev("regQuantityText()"), "3ペア")

print("■ 数量：セット")
b.ev("[...document.querySelectorAll('.qty-modes button')].find(x=>x.textContent==='セット').click()"); time.sleep(0.6)
r.check("種類がセットに", b.ev("regSel.qtyMode"), "set")
r.check("見出しがセット数", b.ev("document.querySelector('#wheelQty').closest('.wheel-box').querySelector('.wheel-title').textContent"), "セット数")
b.ev("[...document.querySelectorAll('#wheelQty .wheel-item')].find(e=>e.textContent==='12').click()"); time.sleep(0.5)
r.check("12セットになる", b.ev("regQuantityText()"), "12セット")

print("■ 数量：雄・雌べつべつ")
b.ev("[...document.querySelectorAll('.qty-modes button')].find(x=>x.textContent.includes('雄')).click()"); time.sleep(0.6)
r.check("種類が雄雌に", b.ev("regSel.qtyMode"), "sex")
r.check("ホイールが2本", b.ev("document.querySelectorAll('#wheelMale,#wheelFemale').length"), 2)
r.check("雄も1〜100", b.ev("document.querySelectorAll('#wheelMale .wheel-item').length"), 100)
r.check("雌も1〜100", b.ev("document.querySelectorAll('#wheelFemale .wheel-item').length"), 100)
b.ev("[...document.querySelectorAll('#wheelMale .wheel-item')].find(e=>e.textContent==='2').click()"); time.sleep(0.4)
b.ev("[...document.querySelectorAll('#wheelFemale .wheel-item')].find(e=>e.textContent==='5').click()"); time.sleep(0.5)
r.check("雄2 雌5 になる", b.ev("regQuantityText()"), "雄2 雌5")
r.expect("いま選んでいる内容に出る", "雄2 雌5" in (b.ev("document.getElementById('regStep2Now').textContent") or ""),
         b.ev("document.getElementById('regStep2Now').textContent"))
r.expect("ステップの見出しにも出る", "雄2 雌5" in (b.ev("document.querySelectorAll('#regSteps .reg-step')[1].textContent") or ""),
         b.ev("document.querySelectorAll('#regSteps .reg-step')[1].textContent").strip())

print("■ 確認へ進んで登録")
b.ev("document.getElementById('regStep2Next').click()"); time.sleep(0.6)
r.check("ステップ③", b.ev("regSel.step"), 3)
r.expect("確認に内容が出る",
         all(x in (b.ev("document.getElementById('regStepBody').textContent") or "") for x in ["幹之","上物","雄2 雌5","MD-"]),
         (b.ev("document.getElementById('regStepBody').textContent") or "").replace("\n"," ")[:90])
b.ev("document.getElementById('regDoRegister').click()"); time.sleep(0.6)
r.check("登録の中身", b.ev("regItems()[0].variety+'/'+regItems()[0].rank+'/'+regItems()[0].quantityText"), "幹之/上物/雄2 雌5")
r.check("管理番号", b.ev("regItems()[0].controlNo"), f"MD-{today}-001")

print("■ 出品タイトルとテプラのラベル")
b.ev("""{ photos=[{name:'a.jpg',handle:null,blobUrl:null,isLabel:false}]; folderHandle={name:'t'};
  switchTab('import'); document.getElementById('assignPerItem').value=1; assignPhotosToRegistered(); }""")
time.sleep(0.6)
t = b.ev("buildTitle(products[0], {})")
r.expect("タイトルに雄雌が入る", "雄2 雌5" in (t or ""), t)
b.ev("""window.__sent=[]; window.TepraBridge={ status(){return JSON.stringify({ok:true,connected:true,printer:'X',tapeMM:24});},
  connect(){return JSON.stringify({ok:true,connected:true});},
  print(j){window.__sent.push(JSON.parse(j));return JSON.stringify({ok:true,printed:1});} }; TepraLink._kind='android';""")
b.ev("tepraPrintPending()"); time.sleep(1.0)
r.check("ラベル2行目＝ランクと数量", b.ev("window.__sent[0][0].lines[1]"), "上物 雄2 雌5")

print("■ 古いランク(SS/S/A/B/C)は新しいものに入れ替わる")
b.ev("""{ localStorage.setItem('medaka_reg_masters', JSON.stringify({breeds:[{name:'テスト',reading:'てすと',code:''}],
     ranks:['SS','S','A','B','C'], quantities:['1匹']})); }""")
r.check("入れ替わる", b.ev("regMasters().ranks"), ["特上","上物","通常","若魚"])

print("■ タブのアイコン")
r.expect("favicon が指定されている", b.ev("!!document.querySelector('link[rel=icon]')"),
         b.ev("(document.querySelector('link[rel=icon]')||{}).getAttribute && document.querySelector('link[rel=icon]').getAttribute('href')"))

b.close(); r.finish()
