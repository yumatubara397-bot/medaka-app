# -*- coding: utf-8 -*-
"""3〜5の改善を確かめる。
   登録したらそのまま撮影へ／撮り忘れの警告／品種ごとの説明文。"""
import time
from common import Browser, Report

b = Browser(9404, 1200, 1000); r = Report()
b.ev("localStorage.clear()"); time.sleep(0.4)

print("■ 登録したら、そのままカメラを開く")
r.check("はじめから入っている", b.ev("camAutoOn()"), True)
b.ev("localStorage.setItem('medaka_camera_auto','0')")
r.check("切ることもできる", b.ev("camAutoOn()"), False)
b.ev("localStorage.setItem('medaka_camera_auto','1')")
r.check("入れ直せる", b.ev("camAutoOn()"), True)
b.ev("switchTab('settings')"); time.sleep(0.4)
r.expect("設定タブに切り替えがある", b.ev("!!document.getElementById('camAutoOpen')"), "camAutoOpen")
r.check("画面の状態も合っている", b.ev("document.getElementById('camAutoOpen').checked"), True)

print("■ 撮り終えたら次の登録に戻る")
b.ev("""window.__wentNext = false;
const realNext = regGoNextFish;
regGoNextFish = () => { window.__wentNext = true; realNext(); };
fsEnsureFolder = async () => ({ kind:'directory', name:'x',
  entries(){ return { [Symbol.asyncIterator](){return this;}, async next(){ return {done:true}; } }; } });
navigator.mediaDevices.getUserMedia = async () => { const e=new Error('x'); e.name='NotFoundError'; throw e; };
'ok'""")
b.ev("(async()=>{ await Cam.open({variety:'幹之',rank:'特上',quantityText:'1ペア',controlNo:'MD-1'}, true); })()")
time.sleep(0.5)
b.ev("Cam.shots = 2")                       # 撮った状態にする
b.ev("(async()=>{ await Cam.close(); })()"); time.sleep(0.5)
r.check("撮っていれば次の登録へ戻る", b.ev("window.__wentNext"), True)

b.ev("window.__wentNext = false")
b.ev("(async()=>{ await Cam.open({variety:'夜桜',rank:'',quantityText:'',controlNo:'MD-2'}, true); })()")
time.sleep(0.4)
b.ev("(async()=>{ await Cam.close(); })()"); time.sleep(0.4)
r.check("1枚も撮らなければ戻さない", b.ev("window.__wentNext"), False)

print("■ 出品の前に、撮り忘れを知らせる")
b.ev("""products = [
  {variety:'幹之', rank:'特上', quantityText:'3ペア', controlNo:'MD-1', specimenIdxs:[0,1]},
  {variety:'夜桜', rank:'上物', quantityText:'2ペア', controlNo:'MD-2', specimenIdxs:[]},
  {variety:'紅帝', rank:'',    quantityText:'',     controlNo:'MD-3', specimenIdxs:[2]}
];
renderListingWarn(); 'ok'"""); time.sleep(0.4)
w = b.ev("document.getElementById('lstWarn').textContent") or ""
r.expect("警告が出る", not b.ev("document.getElementById('lstWarn').classList.contains('hidden')"), "表示")
r.expect("写真の無い商品を知らせる", "写真がまだ無い商品が 1件" in w, w[:60])
r.expect("どれかも分かる", "MD-2" in w, "管理番号を出す")
r.expect("ランクと数量の空も知らせる", "ランクと数量が空の商品が 1件" in w, "MD-3")

b.ev("""products = [{variety:'幹之', rank:'特上', quantityText:'3ペア', controlNo:'MD-1', specimenIdxs:[0,1,2,3,4,5,6]}];
renderListingWarn(); 'ok'"""); time.sleep(0.3)
r.expect("5枚を超えたら知らせる",
         "先頭5枚だけ" in (b.ev("document.getElementById('lstWarn').textContent") or ""), "オークタウンの上限")

b.ev("""products = [{variety:'幹之', rank:'特上', quantityText:'3ペア', controlNo:'MD-1', specimenIdxs:[0,1,2]}];
renderListingWarn(); 'ok'"""); time.sleep(0.3)
r.expect("問題が無ければ出さない", b.ev("document.getElementById('lstWarn').classList.contains('hidden')"), "hidden")

print("■ 品種ごとの説明文")
r.check("はじめは空", b.ev("breedNote('幹之')"), "")
r.check("書ける", b.ev("setBreedNote('幹之', '体外光が強く出る系統です。')"), True)
r.check("読める", b.ev("breedNote('幹之')"), "体外光が強く出る系統です。")
r.check("知らない品種には書けない", b.ev("setBreedNote('いない魚', 'x')"), False)
r.check("空の名前も断る", b.ev("setBreedNote('', 'x')"), False)
r.check("消せる", b.ev("(()=>{ setBreedNote('幹之',''); return breedNote('幹之'); })()"), "")

print("■ 説明文に差し込まれる")
b.ev("setBreedNote('幹之', '体外光が強く出る系統です。')")
b.ev("localStorage.setItem('medaka_desc_template', '【品種】{品種}\\n{品種説明}\\n【数量】{数量}')")
out = b.ev("""buildDescription({variety:'幹之', rank:'特上', quantityText:'3ペア', controlNo:'MD-1'},
                 {note:''}, false)""")
r.expect("品種説明が入る", "体外光が強く出る系統です。" in (out or ""), (out or "")[:60])
out2 = b.ev("""buildDescription({variety:'夜桜', rank:'上物', quantityText:'2ペア', controlNo:'MD-2'},
                 {note:''}, false)""")
r.expect("書いていない品種では、その行ごと消える", "{品種説明}" not in (out2 or ""), (out2 or "")[:60])

print("■ 設定タブの一覧")
b.ev("switchTab('settings'); renderBreedNotes()"); time.sleep(0.5)
n = b.ev("document.querySelectorAll('#breedNoteList input').length")
r.expect("品種が並ぶ", n and n > 30, f"{n}件")
r.check("書いてある件数が出る",
        "1件に書いてあります" in (b.ev("document.getElementById('breedNoteList').textContent") or ""), True)
b.ev("document.getElementById('breedNoteSearch').value='みゆき'; renderBreedNotes()"); time.sleep(0.3)
r.expect("ふりがなで絞り込める",
         b.ev("document.querySelectorAll('#breedNoteList input').length") < n, "絞り込み")

print("■ Android では勝手にカメラを開かない（本体カメラが撮ってしまうため）")
b.ev("""localStorage.setItem('medaka_camera_auto','1');
window.FolderBridge = { ensureFolder: () => '{}' };   // Android のふりをする
window.__camOpened = false; const realOpen = Cam.open;
Cam.open = async (...a) => { window.__camOpened = true; return realOpen.apply(Cam, a); };
'ok'""")
r.check("Android と見なされる", b.ev("FsLink.kind()"), "android")
b.ev("""regSel.mode='fish'; regSel.breed=regMasters().breeds[0]; regSel.rank='特上';
regSel.qtyMode='pair'; regSel.qtyN=1; regSel.step=4; regDoRegister(); 'ok'"""); time.sleep(1.2)
r.check("カメラを開かない", b.ev("window.__camOpened"), False)
b.ev("delete window.FolderBridge; 'ok'")

b.close(); r.finish()
