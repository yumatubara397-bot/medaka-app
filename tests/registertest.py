"""登録タブの検証：ステップ式・頭文字の絞り込み・検索・発番・その場追加・
   テプラCSV・Androidの窓口・写真の割り当て。"""
import time, datetime, json, base64
from common import Browser, Report

b = Browser(9350); r = Report()
today = datetime.date.today().strftime("%y%m%d")

b.ev("localStorage.clear();switchTab('register');renderRegisterPanel()"); time.sleep(0.6)

print("■ 読み込み直後（タブを押さなくても出る）")
r.check("ステップ表示は4つ", b.ev("document.querySelectorAll('#regSteps .reg-step').length"), 4)
r.check("品種が全部出る", b.ev("document.querySelectorAll('#regBreedList button').length"), 40)
r.check("読みが空の品種はない", b.ev("regMasters().breeds.filter(x=>!x.reading).length"), 0)
r.check("いまのステップ", b.ev("regSel.step"), 1)

print("■ 頭文字の絞り込み")
b.ev("[...document.querySelectorAll('#regKanaBar button')].find(x=>x.textContent==='か').click()"); time.sleep(0.3)
r.check("か行の件数", b.ev("document.querySelectorAll('#regBreedList button').length"), 10)
r.check("幹之はま行なので出ない",
        b.ev("[...document.querySelectorAll('#regBreedList button .bn')].some(e=>e.textContent==='幹之')"), False)
b.ev("[...document.querySelectorAll('#regKanaBar button')].find(x=>x.textContent==='ま').click()"); time.sleep(0.3)
r.expect("ま行に幹之がある",
         b.ev("[...document.querySelectorAll('#regBreedList button .bn')].some(e=>e.textContent==='幹之')"),
         b.ev("[...document.querySelectorAll('#regBreedList button .bn')].map(e=>e.textContent).join('/')"))
b.ev("[...document.querySelectorAll('#regKanaBar button')].find(x=>x.textContent==='全部').click()")

print("■ 検索（名前・ふりがな・コード／ひらがなカタカナを区別しない）")
for q, want in [("みゆき","幹之"),("MIY","幹之"),("さふぁ","サファイア"),("サファ","サファイア"),("おろち","オロチ")]:
    b.ev(f"regSel.search={json.dumps(q)};renderRegBreeds()")
    names = b.ev("[...document.querySelectorAll('#regBreedList button .bn')].map(e=>e.textContent)")
    r.expect(f"検索『{q}』", want in (names or []), str(names)[:60])
b.ev("regSel.search='';renderRegBreeds()")

print("■ 1つ選ぶと次の項目が出る")
b.ev("[...document.querySelectorAll('#regBreedList button')].find(x=>x.querySelector('.bn').textContent==='幹之').click()")
time.sleep(0.4)
r.check("ステップが②へ", b.ev("regSel.step"), 2)
r.check("ランクが全部出る", b.ev("[...document.querySelectorAll('#regStepBody .reg-big')].map(e=>e.textContent).join(',')"), "SS,S,A,B,C")
b.ev("[...document.querySelectorAll('#regStepBody .reg-big')].find(x=>x.textContent==='SS').click()"); time.sleep(0.4)
r.check("ステップが③へ", b.ev("regSel.step"), 3)
r.check("数量が全部出る", b.ev("document.querySelectorAll('#regStepBody .reg-big').length"), 7)
b.ev("[...document.querySelectorAll('#regStepBody .reg-big')].find(x=>x.textContent==='3匹').click()"); time.sleep(0.4)
r.check("ステップが④へ", b.ev("regSel.step"), 4)
r.expect("確認に内容と管理番号が出る",
         all(x in (b.ev("document.getElementById('regStepBody').textContent") or "") for x in ["幹之","SS","3匹","MD-"]),
         (b.ev("document.getElementById('regStepBody').textContent") or "").replace("\n"," ")[:80])

print("■ ステップを押して戻れる")
b.ev("document.querySelectorAll('#regSteps .reg-step')[1].click()"); time.sleep(0.3)
r.check("②に戻る", b.ev("regSel.step"), 2)
r.expect("選んだランクが選択状態",
         "on" in (b.ev("[...document.querySelectorAll('#regStepBody .reg-big')].find(x=>x.textContent==='SS').className") or ""), "SS")
b.ev("document.querySelectorAll('#regSteps .reg-step')[3].click()"); time.sleep(0.3)

print("■ 管理番号の発番")
r.check("押すまで消費しない", b.ev("regPreviewNumber().no"), f"MD-{today}-001")
b.ev("document.getElementById('regDoRegister').click()"); time.sleep(0.5)
r.check("登録の中身", b.ev("regItems()[0].variety+'/'+regItems()[0].rank+'/'+regItems()[0].quantityText"), "幹之/SS/3匹")
r.check("管理番号", b.ev("regItems()[0].controlNo"), f"MD-{today}-001")
r.check("次は002", b.ev("regPreviewNumber().no"), f"MD-{today}-002")
r.check("ステップ①に戻る", b.ev("regSel.step"), 1)
r.check("品種は空になる", b.ev("regSel.breed"), None)
r.check("ランクは残る", b.ev("regSel.rank"), "SS")

print("■ その場で追加")
b.ev("window.prompt = () => '青龍'")
b.ev("document.getElementById('regAddBreed').click()"); time.sleep(0.4)
r.check("品種が41件に", b.ev("regMasters().breeds.length"), 41)
r.check("追加した品種が選ばれる", b.ev("(regSel.breed||{}).name"), "青龍")
b.ev("regSel.step=2;renderRegisterPanel();window.prompt=()=>'SSS'"); time.sleep(0.3)
b.ev("document.getElementById('regPickAdd').click()"); time.sleep(0.4)
r.check("ランクが6件に", b.ev("regMasters().ranks.length"), 6)
r.check("追加したランクが選ばれる", b.ev("regSel.rank"), "SSS")

print("■ 番号が重複しない")
for _ in range(3):
    b.ev("regSel.breed=regMasters().breeds[0];regSel.step=4;regDoRegister()"); time.sleep(0.25)
r.check("4件登録", b.ev("regItems().length"), 4)
r.check("番号に重複なし", b.ev("new Set(regItems().map(x=>x.controlNo)).size"), 4)

print("■ テプラ用CSV")
csv = b.ev("buildTepraCsv(regItems())")
lines = [l for l in (csv or "").split("\r\n") if l]
r.check("タイトル行", lines[0], "管理番号,品種,ランク,数量,ラベル")
r.check("行数（タイトル+4件）", len(lines), 5)
b.ev("regAddBreed('赤,白ラメ','あかしろらめ','TST');regSel.breed=regMasters().breeds.find(x=>x.name==='赤,白ラメ');regSel.step=4;regDoRegister()")
time.sleep(0.4)
r.expect("カンマを含む品種は引用符で囲む", '"赤,白ラメ"' in (b.ev("buildTepraCsv(regItems())") or ""), "")
sj = b.ev("(()=>{const b=encodeSjis(buildTepraCsv(regItems()));let s='';for(const x of b)s+=String.fromCharCode(x);return btoa(s);})()")
try:
    dec = base64.b64decode(sj).decode("cp932")
    r.expect("Shift_JISで書き出せる（漢字が化けない）", "幹之" in dec and "赤,白ラメ" in dec, f"{len(base64.b64decode(sj))}バイト")
except Exception as e:
    r.expect("Shift_JISで書き出せる", False, str(e))

print("■ 二重に出さない")
r.check("未書き出しは5件", b.ev("regUnprinted().length"), 5)
b.ev("exportTepraCsv('sjis', false)"); time.sleep(0.5)
r.check("書き出したら0件", b.ev("regUnprinted().length"), 0)
r.expect("ボタンが押せなくなる", b.ev("document.getElementById('regTepraCsv').disabled"),
         b.ev("document.getElementById('regTepraCsv').textContent"))

print("■ Androidの窓口（偽物に差し替えて確認）")
b.ev("""window.__sent=[];
window.TepraBridge={ status(){return JSON.stringify({ok:true,connected:true,printer:'SR-R5600P',tapeMM:24});},
  connect(){return JSON.stringify({ok:true,connected:true,printer:'SR-R5600P',tapeMM:24});},
  print(j){window.__sent.push(JSON.parse(j));return JSON.stringify({ok:true,printed:JSON.parse(j).length});} };
TepraLink._kind=null;""")
r.check("経路の判定", b.ev("TepraLink.probe()"), "android")
b.ev("renderRegisterPanel()"); time.sleep(0.8)
r.expect("状態バーが出る", "SR-R5600P" in (b.ev("document.getElementById('regTepraBar').textContent") or ""),
         (b.ev("document.getElementById('regTepraBar').textContent") or "").strip()[:50])
b.ev("regSel.breed=regMasters().breeds.find(x=>x.name==='夜桜');regSel.rank='A';regSel.qty='1ペア';regSel.step=4;regDoRegister()")
time.sleep(1.0)
r.check("登録と同時に1枚送る", b.ev("window.__sent.length"), 1)
r.check("1行目＝品種", b.ev("window.__sent[0][0].lines[0]"), "夜桜")
r.check("2行目＝ランクと数量", b.ev("window.__sent[0][0].lines[1]"), "A 1ペア")
r.check("3行目＝管理番号", b.ev("window.__sent[0][0].lines[2]"), f"MD-{today}-006")
b.ev("window.TepraBridge.print=()=>JSON.stringify({ok:false,error:'カバーが開いています'})")
b.ev("{const l=regItems();l.forEach(x=>x.tepraExportedAt=null);saveRegItems(l);renderRegisterPanel();}"); time.sleep(0.4)
n = b.ev("regUnprinted().length")
b.ev("tepraPrintPending()"); time.sleep(1.0)
r.check("失敗したら印刷済みにしない", b.ev("regUnprinted().length"), n)

print("■ 写真の割り当て（撮った順に配る）")
b.ev("""{ localStorage.setItem('medaka_reg_items','[]');
  ['幹之','夜桜','オロチ'].forEach(nm=>{ regSel.breed=regMasters().breeds.find(x=>x.name===nm);
    regSel.rank='SS'; regSel.qty='3匹'; regSel.step=4; regDoRegister(); });
  window.TepraBridge=undefined; TepraLink._kind='none';
  photos = Array.from({length:9},(_,i)=>({name:'IMG_'+String(i+1).padStart(3,'0')+'.jpg',handle:null,blobUrl:null,isLabel:false}));
  folderHandle={name:'テスト'}; }""")
time.sleep(0.6)
b.ev("switchTab('import');document.getElementById('assignPerItem').value=3;refreshAssignBar();assignPhotosToRegistered()")
time.sleep(0.6)
r.check("商品が3件できる", b.ev("products.length"), 3)
r.check("順番どおりに配る", b.ev("JSON.stringify(products.map(p=>p.specimenIdxs))"), "[[0,1,2],[3,4,5],[6,7,8]]")
r.check("管理番号が引き継がれる", b.ev("products[0].controlNo"), b.ev("regItems()[0].controlNo"))
t = b.ev("buildTitle(products[0], {})")
r.expect("出品タイトルが作れる", "幹之" in (t or "") and (b.ev("regItems()[0].controlNo") in (t or "")), t)

b.close(); r.finish()
