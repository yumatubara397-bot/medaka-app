"""用品（魚以外の固定商品）の登録を検証する。"""
import time, datetime
from common import Browser, Report

b = Browser(9363, 1200, 1300); r = Report()
today = datetime.date.today().strftime("%y%m%d")
b.ev("localStorage.clear();switchTab('register');renderRegisterPanel()"); time.sleep(0.9)
b.ev("window.confirm = () => true; TepraLink._kind='none'")

print("■ 用品が入っている")
r.check("用品は23件", b.ev("regMasters().goods.length"), 23)
for nm in ["舞めだかゴールドフード","舞めだかオリジナルフード","ホテイソウ","ラムズホーン",
           "岩塩","ミジンコ","タモ(小)","タモ(中)","タモ(大)"]:
    r.expect(f"{nm}", b.ev(f"regMasters().goods.some(x=>x.name==={nm!r})"), "")
for nm in ["ウォーターフード","めだか稚魚のえさ","めだか成魚のえさ","めだかのえさ","めだか飼料pro",
           "めだかの黒発泡スチロール","サイコロルーム150","萩物語めだか MD-205"]:
    r.expect(f"クハラ {nm}", b.ev(f"regMasters().goods.some(x=>x.name==={nm!r})"), "")

print("■ メダカ／用品を切り替えられる")
r.expect("切り替えがある", b.ev("document.querySelectorAll('#regStepBody .reg-mode button').length") == 2,
         b.ev("document.querySelector('#regStepBody .reg-mode').textContent"))
r.check("最初はメダカ", b.ev("regSel.mode"), "fish")
r.check("メダカは40件", b.ev("document.querySelectorAll('#regBreedList button').length"), 40)
b.ev("[...document.querySelectorAll('#regStepBody .reg-mode button')].find(x=>x.textContent.includes('用品')).click()")
time.sleep(0.8)
r.check("用品に切り替わる", b.ev("regSel.mode"), "goods")
r.check("用品23件が並ぶ", b.ev("document.querySelectorAll('#regBreedList button').length"), 23)
r.expect("見出しが商品になる", "商品を選ぶ" in (b.ev("document.querySelector('#regStepBody .card-title').textContent") or ""),
         b.ev("document.querySelector('#regStepBody .card-title').textContent"))
r.expect("ステップ名も変わる",
         "商品" in (b.ev("document.querySelectorAll('#regSteps .reg-step')[0].textContent") or "")
         and "数量" in (b.ev("document.querySelectorAll('#regSteps .reg-step')[1].textContent") or ""),
         b.ev("[...document.querySelectorAll('#regSteps .reg-step')].map(x=>x.textContent.replace(/\\s+/g,'')).join(' / ')"))

print("■ 頭文字と検索は用品でも効く")
b.ev("[...document.querySelectorAll('#regKanaBar button')].find(x=>x.textContent==='た').click()"); time.sleep(0.5)
names = b.ev("[...document.querySelectorAll('#regBreedList button .bn')].map(e=>e.textContent)")
r.expect("た行にタモ3つ", set(["タモ(小)","タモ(中)","タモ(大)"]).issubset(set(names or [])), str(names))
b.ev("[...document.querySelectorAll('#regKanaBar button')].find(x=>x.textContent==='全部').click()"); time.sleep(0.4)
b.ev("regSel.search='がんえん';renderRegStepBody()"); time.sleep(0.5)
r.check("ふりがなで岩塩が出る",
        b.ev("[...document.querySelectorAll('#regBreedList button .bn')].map(e=>e.textContent)"), ["岩塩"])
b.ev("regSel.search='';renderRegStepBody()"); time.sleep(0.4)

print("■ 用品はランクを聞かず、個数だけ")
b.ev("[...document.querySelectorAll('#regBreedList button')].find(x=>x.querySelector('.bn').textContent==='ホテイソウ').click()")
time.sleep(0.8)
r.check("ステップ②へ", b.ev("regSel.step"), 2)
r.expect("ランクのホイールは出ない", not b.ev("!!document.getElementById('wheelRank')"), "")
r.expect("ペア・雄雌の切り替えも出ない", not b.ev("!!document.querySelector('.qty-modes')"), "")
r.check("個数のホイールが出る", b.ev("document.querySelectorAll('#wheelQty .wheel-item').length"), 100)
b.ev("[...document.querySelectorAll('#wheelQty .wheel-item')].find(e=>e.textContent==='5').click()"); time.sleep(0.6)
r.check("5個になる", b.ev("regQuantityText()"), "5個")

print("■ 登録")
b.ev("document.getElementById('regStep2Next').click()"); time.sleep(0.6)
r.expect("確認にランクが出ない", "ランク" not in (b.ev("document.getElementById('regStepBody').textContent") or ""),
         (b.ev("document.getElementById('regStepBody').textContent") or "").replace("\n"," ")[:80])
b.ev("document.getElementById('regDoRegister').click()"); time.sleep(0.8)
r.check("登録された", b.ev("regItems().length"), 1)
r.check("商品名", b.ev("regItems()[0].variety"), "ホテイソウ")
r.check("ランクは空", b.ev("regItems()[0].rank"), "")
r.check("数量は5個", b.ev("regItems()[0].quantityText"), "5個")
r.check("用品として記録", b.ev("regItems()[0].kind"), "goods")
r.check("管理番号は用品の固定番号", b.ev("regItems()[0].controlNo"), b.ev("goodsOf('ホテイソウ').fixedNo"))

print("■ ラベルと出品タイトル")
b.ev("""window.__sent=[]; window.TepraBridge={ status(){return JSON.stringify({ok:true,connected:true,printer:'X',tapeMM:24});},
  connect(){return JSON.stringify({ok:true,connected:true});},
  print(j){window.__sent.push(JSON.parse(j));return JSON.stringify({ok:true,printed:1});} }; TepraLink._kind='android';""")
b.ev("{const l=regItems(); l.forEach(x=>x.tepraExportedAt=null); saveRegItems(l);} tepraPrintPending()"); time.sleep(1.2)
r.check("ラベル1行目＝商品名", b.ev("window.__sent[0][0].lines[0]"), "ホテイソウ")
r.check("ラベル2行目＝個数", b.ev("window.__sent[0][0].lines[1]"), "5個")
b.ev("""{ photos=[{name:'a.jpg',handle:null,blobUrl:null}]; folderHandle={name:'t'}; TepraLink._kind='none';
  switchTab('import'); document.getElementById('assignPerItem').value=1; assignPhotosToRegistered(); }""")
time.sleep(1.0)
t = b.ev("buildTitle(products[0], {})")
r.expect("出品タイトルは用品向けになる",
         (t or "").startswith("【メダカ用品】") and "ホテイソウ" in t and "5個" in t, t)
# 魚のほうは従来どおり
b.ev("""{ switchTab('register'); regSel.mode='fish';
  regSel.breed=regMasters().breeds.find(x=>x.name==='幹之');
  regSel.rank='特上'; regSel.qtyMode='pair'; regSel.qtyN=2; regSel.step=3; regDoRegister();
  photos.push({name:'b.jpg',handle:null,blobUrl:null});
  switchTab('import'); document.getElementById('assignPerItem').value=1; assignPhotosToRegistered(); }""")
time.sleep(1.2)
t2 = b.ev("buildTitle(products[1], {})")
r.expect("魚は【メダカ】のまま", (t2 or "").startswith("【メダカ】") and "幹之" in t2, t2)

print("■ 用品も減らせる／メダカ側に影響しない")
b.ev("switchTab('register'); regSel.mode='goods'; regSel.step=1; renderRegisterPanel()"); time.sleep(0.8)
b.ev("document.getElementById('regTidyStart').click()"); time.sleep(0.6)
b.ev("[...document.querySelectorAll('#regBreedList button.tidy')].find(x=>x.querySelector('.bn').textContent==='岩塩').click()")
time.sleep(0.4)
b.ev("document.getElementById('regTidyDo').click()"); time.sleep(1.0)
r.check("用品が22件に", b.ev("regMasters().goods.length"), 22)
r.check("メダカは40件のまま", b.ev("regMasters().breeds.length"), 40)
b.ev("document.getElementById('regTidyReset').click()"); time.sleep(0.9)
r.check("用品だけ戻る", b.ev("regMasters().goods.length"), 23)
r.check("メダカはやはり40件", b.ev("regMasters().breeds.length"), 40)

print("■ メダカに戻すと元どおり")
b.ev("document.getElementById('regTidyEnd').click()"); time.sleep(0.5)
b.ev("[...document.querySelectorAll('#regStepBody .reg-mode button')].find(x=>x.textContent.includes('メダカ')).click()")
time.sleep(0.8)
r.check("メダカ40件", b.ev("document.querySelectorAll('#regBreedList button').length"), 40)
r.expect("ステップ名が品種に戻る", "品種" in (b.ev("document.querySelectorAll('#regSteps .reg-step')[0].textContent") or ""),
         b.ev("document.querySelectorAll('#regSteps .reg-step')[0].textContent").strip())

b.close(); r.finish()
