"""品種を減らす機能を検証する。"""
import time
from common import Browser, Report

b = Browser(9361, 1200, 1200); r = Report()
b.ev("localStorage.clear();switchTab('register');renderRegisterPanel()"); time.sleep(0.8)
b.ev("window.confirm = () => true")

print("■ 入口")
r.check("最初は40件", b.ev("regMasters().breeds.length"), 40)
r.expect("『品種を減らす』がある", b.ev("!!document.getElementById('regTidyStart')"), "🗑 品種を減らす")
b.ev("document.getElementById('regTidyStart').click()"); time.sleep(0.6)
r.expect("整理の画面になる", "品種を減らす" in (b.ev("document.querySelector('#regStepBody .card-title').textContent") or ""),
         b.ev("document.querySelector('#regStepBody .card-title').textContent"))
r.check("全品種が並ぶ", b.ev("document.querySelectorAll('#regBreedList button.tidy').length"), 40)
r.expect("選ぶ前は消せない", b.ev("document.getElementById('regTidyDo').disabled"), "")

print("■ 選ぶ")
b.ev("[...document.querySelectorAll('#regBreedList button.tidy')].find(x=>x.querySelector('.bn').textContent==='錦鯉').click()")
time.sleep(0.5)
b.ev("[...document.querySelectorAll('#regBreedList button.tidy')].find(x=>x.querySelector('.bn').textContent==='蜃気楼').click()")
time.sleep(0.5)
r.check("2件選ばれる", b.ev("regSel.tidyPicked.size"), 2)
r.expect("ボタンに件数が出る", "2件を消す" in (b.ev("document.getElementById('regTidyDo').textContent") or ""),
         (b.ev("document.getElementById('regTidyDo').textContent") or "").strip())
r.expect("選んだものに印がつく",
         "on" in (b.ev("[...document.querySelectorAll('#regBreedList button.tidy')].find(x=>x.querySelector('.bn').textContent==='錦鯉').className") or ""),
         "🗑")
b.ev("[...document.querySelectorAll('#regBreedList button.tidy')].find(x=>x.querySelector('.bn').textContent==='錦鯉').click()")
time.sleep(0.5)
r.check("押し直すと外れる", b.ev("regSel.tidyPicked.size"), 1)

print("■ 消す")
b.ev("[...document.querySelectorAll('#regBreedList button.tidy')].find(x=>x.querySelector('.bn').textContent==='錦鯉').click()")
time.sleep(0.4)
b.ev("document.getElementById('regTidyDo').click()"); time.sleep(1.0)
r.check("38件になる", b.ev("regMasters().breeds.length"), 38)
r.check("錦鯉が消えた", b.ev("regMasters().breeds.some(x=>x.name==='錦鯉')"), False)
r.check("蜃気楼も消えた", b.ev("regMasters().breeds.some(x=>x.name==='蜃気楼')"), False)
r.check("他は残る", b.ev("regMasters().breeds.some(x=>x.name==='幹之')"), True)
r.check("続けて減らせるよう整理画面のまま", b.ev("regSel.tidy"), True)
r.check("選んでいた印は外れる", b.ev("regSel.tidyPicked.size"), 0)
r.check("一覧も38件", b.ev("document.querySelectorAll('#regBreedList button').length"), 38)

print("■ 消しても登録ずみの商品は残る")
b.ev("""{ TepraLink._kind='none';
  regSel.breed=regMasters().breeds.find(x=>x.name==='幹之');
  regSel.rank='特上'; regSel.qtyMode='pair'; regSel.qtyN=1; regSel.step=4; regDoRegister(); }""")
time.sleep(1.0)
b.ev("[...document.querySelectorAll('#regBreedList button.tidy')].find(x=>x.querySelector('.bn').textContent==='幹之').click()")
time.sleep(0.4)
b.ev("document.getElementById('regTidyDo').click()"); time.sleep(1.0)
r.check("幹之を消した", b.ev("regMasters().breeds.some(x=>x.name==='幹之')"), False)
r.check("登録した商品は残る", b.ev("regItems().length"), 1)
r.check("品種名も残る", b.ev("regItems()[0].variety"), "幹之")

print("■ 検索しながら減らせる")
b.ev("document.getElementById('regBreedSearch').value='らめ';document.getElementById('regBreedSearch').dispatchEvent(new Event('input',{bubbles:true}))")
time.sleep(0.6)
n = b.ev("document.querySelectorAll('#regBreedList button.tidy').length")
r.expect("絞り込める", 0 < (n or 0) < 37, f"{n}件")
b.ev("document.getElementById('regTidyEnd').click()"); time.sleep(0.5)
r.check("やめると戻る", b.ev("regSel.tidy"), False)

print("■ 最初の一覧に戻す")
b.ev("regAddBreed('自作品種A','じさくひんしゅえー','')"); time.sleep(0.3)
b.ev("document.getElementById('regTidyStart').click()"); time.sleep(0.5)
b.ev("document.getElementById('regTidyReset').click()"); time.sleep(1.0)
r.check("40件に戻る", b.ev("regMasters().breeds.length"), 40)
r.check("消した品種も戻る", b.ev("regMasters().breeds.some(x=>x.name==='錦鯉')"), True)
r.check("自分で足したものは消える", b.ev("regMasters().breeds.some(x=>x.name==='自作品種A')"), False)
r.check("登録した商品はやはり残る", b.ev("regItems().length"), 1)

b.close(); r.finish()
