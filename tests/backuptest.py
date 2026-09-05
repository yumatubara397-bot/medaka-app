# -*- coding: utf-8 -*-
"""登録や品種の一覧が、フォルダの「設定.json」に控えられるかを確かめる。
   ブラウザのデータを消しても戻せることが要点。"""
import time, json
from common import Browser, Report

b = Browser(9401, 1100, 900); r = Report()
b.ev("localStorage.clear()"); time.sleep(0.3)

b.ev(r"""
function fakeRoot(files){
  files = files || {};
  return { kind:'directory', name:'めだか写真', _files:files,
    async getFileHandle(n, o){
      if(!(n in files)){ if(!o||!o.create){ const e=new Error('nf'); e.name='NotFoundError'; throw e; } files[n]=null; }
      return { async createWritable(){ return { async write(b){ files[n]=b; }, async close(){} }; },
               async getFile(){ return files[n]; } };
    },
    async getDirectoryHandle(n,o){ const e=new Error('nf'); e.name='NotFoundError'; throw e; } };
}
window.__root = fakeRoot({});
fsRoot = null; fsRestoreRoot = async () => window.__root;
'ok'""")

print("■ 控えを取る")
b.ev("""localStorage.setItem('medaka_reg_items', JSON.stringify([
  {variety:'幹之', rank:'特上', quantityText:'3ペア', controlNo:'MD-1'},
  {variety:'夜桜', rank:'上物', quantityText:'2ペア', controlNo:'MD-2'}]));
localStorage.setItem('medaka_reg_masters', JSON.stringify({breeds:[{name:'幹之'}], ranks:['特上']}));
localStorage.setItem('medaka_tepra_font', '0.86');
localStorage.setItem('medaka_camera_id', 'このパソコンだけのもの');
'ok'""")
b.ev("(async()=>{ await backupSave(true); })()"); time.sleep(0.6)
r.expect("設定.json ができる", "設定.json" in (b.ev("Object.keys(window.__root._files).join(',')") or ""),
         b.ev("Object.keys(window.__root._files).join(',')"))

saved = b.ev("(async()=>{ const f = window.__root._files['設定.json']; return await f.text(); })()")
obj = json.loads(saved)
r.check("控えだと分かる印", obj.get("kind"), "medaka-backup")
r.check("商品の件数を控える", obj.get("items"), 2)
r.expect("登録が入っている", "medaka_reg_items" in obj["data"], "登録")
r.expect("品種の一覧も入っている", "medaka_reg_masters" in obj["data"], "品種")
r.expect("テプラ設定も入っている", "medaka_tepra_font" in obj["data"], "テプラ")
r.expect("その端末だけのものは入れない", "medaka_camera_id" not in obj["data"], "カメラの選択は持ち込まない")
r.expect("取った日時が入っている", bool(obj.get("savedAt")), obj.get("savedAt", "")[:19])

print("■ ブラウザのデータが消えても戻せる")
b.ev("localStorage.clear()"); time.sleep(0.2)
r.check("消えたことを確かめる", b.ev("regItems().length"), 0)
b.ev("(async()=>{ const o = await backupRead(); backupApply(o); })()"); time.sleep(0.5)
r.check("登録が戻る", b.ev("regItems().length"), 2)
r.check("中身も同じ", b.ev("regItems().map(x=>x.controlNo).join(',')"), "MD-1,MD-2")
r.check("品種の一覧も戻る", b.ev("JSON.parse(localStorage.getItem('medaka_reg_masters')).ranks.join(',')"), "特上")
r.check("テプラ設定も戻る", b.ev("localStorage.getItem('medaka_tepra_font')"), "0.86")

print("■ 登録すると自動で控えが新しくなる")
b.ev("Object.keys(window.__root._files).forEach(k=>delete window.__root._files[k]); saveRegItems(regItems().concat([{variety:'紅帝',rank:'通常',quantityText:'1ペア',controlNo:'MD-3'}])); 'ok'")
r.expect("すぐには書かない（まとめて書く）", "設定.json" not in (b.ev("Object.keys(window.__root._files).join(',')") or ""),
         "3秒待ってから")
time.sleep(4)
r.expect("少し待つと書かれる", "設定.json" in (b.ev("Object.keys(window.__root._files).join(',')") or ""),
         b.ev("Object.keys(window.__root._files).join(',')"))
saved2 = json.loads(b.ev("(async()=>await window.__root._files['設定.json'].text())()"))
r.check("増えた分も入っている", saved2["items"], 3)

print("■ 控えの形が違うものは受け付けない")
r.expect("形が違えば断る",
         "ERR" in str(b.ev("(()=>{ try{ backupApply({kind:'よそのもの'}); return 'ok'; }catch(e){ return 'ERR '+e.message; } })()")),
         "取り違えを防ぐ")
r.expect("medaka_ 以外の名前は書き込まない",
         b.ev("(()=>{ backupApply({kind:'medaka-backup', data:{'よそのキー':'x'}}); return localStorage.getItem('よそのキー'); })()") is None,
         "関係ないものは触らない")

print("■ 中身が空のときだけ、戻す案内を出す")
b.ev("localStorage.clear(); 'ok'"); time.sleep(0.2)
r.check("空なら案内を出す", b.ev("(async()=>await backupOfferRestore())()"), True)
r.expect("画面に出る", not b.ev("document.getElementById('restoreBar').classList.contains('hidden')"), "restoreBar 表示")
txt = b.ev("document.getElementById('restoreBar').textContent") or ""
r.expect("いつの控えか出る", "控え" in txt and "件" in txt, txt[:60])
r.expect("戻すボタンがある", b.ev("!!document.getElementById('restoreDo')"), "↩ 控えから戻す")
b.ev("document.getElementById('restoreNo').click()"); time.sleep(0.2)
r.expect("閉じられる", b.ev("document.getElementById('restoreBar').classList.contains('hidden')"), "hidden")

b.ev("""localStorage.setItem('medaka_reg_items', JSON.stringify([{variety:'幹之',controlNo:'MD-9'}])); 'ok'""")
r.check("中身があれば案内を出さない（勝手に上書きしない）",
        b.ev("(async()=>await backupOfferRestore())()"), False)
r.expect("画面にも出ない", b.ev("document.getElementById('restoreBar').classList.contains('hidden')"), "hidden")

print("■ 控えの様子を画面に出す")
b.ev("(async()=>{ await renderBackupState(); })()"); time.sleep(0.5)
txt = b.ev("document.getElementById('backupState').textContent") or ""
r.expect("いまの件数と控えの日時が出る", "控え" in txt and "商品" in txt, txt[:70])

b.close(); r.finish()
