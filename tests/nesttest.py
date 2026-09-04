# -*- coding: utf-8 -*-
"""作業フォルダ「編集前」そのものを保存先に選んでしまったとき、
   その中にもう1つ作らず、ちゃんと直せるかを確かめる。"""
import time
from common import Browser, Report

b = Browser(9391, 1100, 900); r = Report()
b.ev("localStorage.clear()"); time.sleep(0.4)

# --- にせのフォルダを用意する -------------------------------------------------
b.ev(r"""
function fakeDir(name, kids){
  kids = kids || {};
  return {
    kind:'directory', name:name, _kids:kids,
    async getDirectoryHandle(n, o){
      if(kids[n]) return kids[n];
      if(o && o.create){ kids[n] = fakeDir(n, {}); return kids[n]; }
      const e = new Error('NotFound'); e.name = 'NotFoundError'; throw e;
    },
    async removeEntry(n){ delete kids[n]; },
    entries(){
      const list = Object.entries(kids);
      let i = 0;
      return { [Symbol.asyncIterator](){ return this; },
               async next(){ return i < list.length ? {value:list[i++], done:false} : {done:true}; } };
    }
  };
}
function fakeFile(name){ return { kind:'file', name:name }; }
window.fakeDir = fakeDir; window.fakeFile = fakeFile;
window.__realRestore = fsRestoreRoot;
// FsLink は const なので評価用スクリプトからは見えない。
// fsRestoreRoot だけ差し替えれば、本物の FsLink.status がそれを使ってくれる。
window.__setRoot = (h) => { fsRoot = null; fsRestoreRoot = async () => h; };
'ok'""")

# --- ① 「編集前」そのものを選んでしまった場合 --------------------------------------
print("■ 「編集前」そのものを選んでしまったとき")
b.ev("""
window.__uo = fakeDir('編集前', { '忘却の翼_MD-1': fakeDir('忘却の翼_MD-1', {'a.jpg': fakeFile('a.jpg')}) });
__setRoot(__uo); 'ok'""")

r.check("その中にもう1つ「編集前」を作らない", b.ev("(async()=>{ await fsWorkDir(); return Object.keys(__uo._kids).join(','); })()"),
        "忘却の翼_MD-1")
r.check("作業フォルダとしては使わない（null を返す）", b.ev("(async()=>(await fsWorkDir())===null)()"), True)
r.check("間違いだと気づく", b.ev("(async()=>(await fsDiagnose()).nested)()"), True)
r.check("直し方を知らせる", b.ev("(async()=>(await fsDiagnose()).notes.some(t=>t.includes('1つ上')))()"), True)

b.ev("(async()=>{ await refreshFsConnected(); })()")
r.check("画面の出し分け用の目印が立つ", b.ev("fsRootIsWork"), True)

# 登録の確認画面に「選び直す」ボタンが出るか
b.ev("""
regSel.mode='fish'; regSel.breed={name:'忘却の翼'}; regSel.rank='通常';
regSel.step = 4; renderRegStepBody(); 'ok'""")
time.sleep(0.3)
r.check("登録の前に選び直すボタンが出る", b.ev("!!document.getElementById('regFsFixRoot')"), True)

# 編集タブの案内
b.ev("(async()=>{ products=[]; photos=[]; await autoLoadForEdit(); })()"); time.sleep(0.4)
r.expect("編集タブでも理由を知らせる",
         "1つ上のフォルダ" in (b.ev("document.getElementById('editEmptyMsg').textContent") or ""),
         b.ev("document.getElementById('editEmptyTitle').textContent"))

# --- ② 正しく親フォルダを選んだ場合 -------------------------------------------
print("■ 1つ上（デスクトップ）を選び直したとき")
b.ev("""
window.__ok = fakeDir('デスクトップ', {
  '編集前': fakeDir('編集前', { '編集前': fakeDir('編集前', {}),
                        '忘却の翼_MD-1': fakeDir('忘却の翼_MD-1', {'a.jpg':fakeFile('a.jpg'),'b.jpg':fakeFile('b.jpg')}) }),
  '編集後': fakeDir('編集後', {})
});
__setRoot(__ok); 'ok'""")

r.check("作業フォルダを見つけられる", b.ev("(async()=>(await fsWorkDir()).name)()"), "編集前")
r.check("保管フォルダも見つけられる", b.ev("(async()=>(await fsDoneDir()).name)()"), "編集後")
r.check("もう間違い扱いしない", b.ev("(async()=>(await fsDiagnose()).nested)()"), False)
r.check("中の商品フォルダを数えられる", b.ev("(async()=>(await fsDiagnose()).workItems.length)()"), 2)
r.check("写真の枚数も数えられる",
        b.ev("(async()=>((await fsDiagnose()).workItems.find(x=>x.name==='忘却の翼_MD-1')||{}).photos)()"), 2)

# 間違ってできた空の「編集前/編集前」を片付ける
r.check("空っぽの入れ子を片付ける", b.ev("(async()=>await fsCleanNested())()"), True)
r.check("片付いたか", b.ev("(async()=>{const w=await fsWorkDir(); return Object.keys(w._kids).join(',');})()"),
        "忘却の翼_MD-1")

b.ev("(async()=>{ await refreshFsConnected(); })()")
r.check("目印も下りる", b.ev("fsRootIsWork"), False)

# 中身のある入れ子は消さない
b.ev("""
window.__ok2 = fakeDir('デスクトップ', { '編集前': fakeDir('編集前', {
  '編集前': fakeDir('編集前', { 'x_MD-9': fakeDir('x_MD-9', {'p.jpg':fakeFile('p.jpg')}) }) }) });
__setRoot(__ok2); 'ok'""")
r.check("中身がある入れ子は消さない", b.ev("(async()=>await fsCleanNested())()"), False)

# --- ③ 状態を見る画面 ---------------------------------------------------------
print("■ 状態を見る画面")
b.ev("__setRoot(__ok); showFsStatus()"); time.sleep(0.5)
txt = b.ev("document.getElementById('fsStatusDialog').textContent") or ""
r.expect("選んでいるフォルダ名が出る", "デスクトップ" in txt, txt[:60])
r.expect("編集前の中身が出る", "忘却の翼_MD-1" in txt, "一覧に表示")
r.check("閉じられる", b.ev("document.getElementById('fsStatusClose').click(); "
                          "document.getElementById('fsStatusDialog').classList.contains('hidden')"), True)

# --- ④ 読み取れないときに、理由が画面に出るか -------------------------------
print("■ 読み取れないときの案内")
b.ev("localStorage.setItem('medaka_fs_root_name','デスクトップ')")
b.ev("""
fsRoot = null;
fsRestoreRoot = window.__realRestore;      // 本物に戻して、本当の道筋を試す
fsHandleGet = async () => ({ name:'デスクトップ',
  async queryPermission(){ return 'prompt'; },
  async requestPermission(){ return 'denied'; } });
'ok'""")
b.ev("(async()=>{ products=[]; photos=[]; await autoLoadForEdit(); })()"); time.sleep(0.5)
ttl = b.ev("document.getElementById('editEmptyTitle').textContent") or ""
msg = b.ev("document.getElementById('editEmptyMsg').textContent") or ""
r.expect("どのフォルダが読めないか名前が出る", "デスクトップ" in ttl, ttl)
r.expect("理由が出る（当てずっぽうにしない）", "許可" in msg, msg[:70])

print("■ ブラウザの言い分を、分かる言葉にする")
r.check("許可が下りていない", b.ev("fsWhy({name:'NotAllowedError'})"), "このフォルダを使う許可が下りていません")
r.check("見つからない", b.ev("fsWhy({name:'NotFoundError'})"),
        "フォルダが見つかりません（名前を変えたか、移動したようです）")
r.check("ブラウザが守っている場所", b.ev("fsWhy({name:'SecurityError'})"),
        "ブラウザがこの場所を保護していて使えません")
r.expect("知らない理由もそのまま見せる",
         "Boom" in (b.ev("fsWhy({name:'OddError',message:'Boom'})") or ""), "握りつぶさない")

# --- ⑤ 前の名前のフォルダが残っていたら知らせる -------------------------------
print("■ 前の名前「魚」が残っているとき")
b.ev("""
window.__old = fakeDir('デスクトップ', {
  '編集前': fakeDir('編集前', {}),
  '魚': fakeDir('魚', { '幹之_MD-1': fakeDir('幹之_MD-1', {'a.jpg':fakeFile('a.jpg')}) })
});
__setRoot(__old); 'ok'""")
notes = b.ev("(async()=>((await fsDiagnose()).notes||[]).join(' / '))()") or ""
r.expect("残っていることを知らせる", "魚" in notes and "1件" in notes, notes[:80])
r.expect("どこへ移すかも言う", "編集前" in notes, "移し先を明示")

b.close(); r.finish()
