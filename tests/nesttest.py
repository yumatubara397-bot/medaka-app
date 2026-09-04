# -*- coding: utf-8 -*-
"""「魚」そのものを保存先に選んでしまったとき、
   その中にもう1つ「魚」を作らず、ちゃんと直せるかを確かめる。"""
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
window.__setRoot = (h) => { fsRestoreRoot = async () => h; FsLink.status = async () =>
  ({ ok:true, hasRoot:!!h, rootName: h ? h.name : '' }); };
'ok'""")

# --- ① 「魚」そのものを選んでしまった場合 --------------------------------------
print("■ 「魚」そのものを選んでしまったとき")
b.ev("""
window.__uo = fakeDir('魚', { '忘却の翼_MD-1': fakeDir('忘却の翼_MD-1', {'a.jpg': fakeFile('a.jpg')}) });
__setRoot(__uo); 'ok'""")

r.check("その中にもう1つ「魚」を作らない", b.ev("(async()=>{ await fsWorkDir(); return Object.keys(__uo._kids).join(','); })()"),
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
  '魚': fakeDir('魚', { '魚': fakeDir('魚', {}),
                        '忘却の翼_MD-1': fakeDir('忘却の翼_MD-1', {'a.jpg':fakeFile('a.jpg'),'b.jpg':fakeFile('b.jpg')}) }),
  '魚編集後': fakeDir('魚編集後', {})
});
__setRoot(__ok); 'ok'""")

r.check("作業フォルダを見つけられる", b.ev("(async()=>(await fsWorkDir()).name)()"), "魚")
r.check("保管フォルダも見つけられる", b.ev("(async()=>(await fsDoneDir()).name)()"), "魚編集後")
r.check("もう間違い扱いしない", b.ev("(async()=>(await fsDiagnose()).nested)()"), False)
r.check("中の商品フォルダを数えられる", b.ev("(async()=>(await fsDiagnose()).workItems.length)()"), 2)
r.check("写真の枚数も数えられる",
        b.ev("(async()=>((await fsDiagnose()).workItems.find(x=>x.name==='忘却の翼_MD-1')||{}).photos)()"), 2)

# 間違ってできた空の「魚/魚」を片付ける
r.check("空っぽの「魚/魚」を片付ける", b.ev("(async()=>await fsCleanNested())()"), True)
r.check("片付いたか", b.ev("(async()=>{const w=await fsWorkDir(); return Object.keys(w._kids).join(',');})()"),
        "忘却の翼_MD-1")

b.ev("(async()=>{ await refreshFsConnected(); })()")
r.check("目印も下りる", b.ev("fsRootIsWork"), False)

# 中身のある「魚/魚」は消さない
b.ev("""
window.__ok2 = fakeDir('デスクトップ', { '魚': fakeDir('魚', {
  '魚': fakeDir('魚', { 'x_MD-9': fakeDir('x_MD-9', {'p.jpg':fakeFile('p.jpg')}) }) }) });
__setRoot(__ok2); 'ok'""")
r.check("中身がある「魚/魚」は消さない", b.ev("(async()=>await fsCleanNested())()"), False)

# --- ③ 状態を見る画面 ---------------------------------------------------------
print("■ 状態を見る画面")
b.ev("__setRoot(__ok); showFsStatus()"); time.sleep(0.6)
txt = b.ev("document.getElementById('fsStatusDialog').textContent") or ""
r.expect("選んでいるフォルダ名が出る", "デスクトップ" in txt, txt[:60])
r.expect("魚の中身が出る", "忘却の翼_MD-1" in txt, "一覧に表示")
r.check("閉じられる", b.ev("document.getElementById('fsStatusClose').click(); "
                          "document.getElementById('fsStatusDialog').classList.contains('hidden')"), True)

b.close(); r.finish()
