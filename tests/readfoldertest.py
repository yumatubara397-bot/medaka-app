# -*- coding: utf-8 -*-
"""「編集前」に入っているフォルダを、そのまま商品ごとに読み込めるかを確かめる。
   登録が残っていないフォルダも、名前から品種と管理番号を読み取って編集できること。"""
import time
from common import Browser, Report

b = Browser(9397, 1200, 900); r = Report()
b.ev("localStorage.clear()"); time.sleep(0.4)

# 中身のあるにせフォルダ（写真は本物のPNGにする）
b.ev(r"""
const PNG = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==';
function bin(){ const s = atob(PNG); const u = new Uint8Array(s.length);
  for(let i=0;i<s.length;i++) u[i]=s.charCodeAt(i); return u; }
function fakeFile(name){
  const blob = new Blob([bin()], {type:'image/png'});
  return { kind:'file', name:name, getFile: async () => new File([blob], name, {type:'image/png'}) };
}
function fakeDir(name, kids){
  kids = kids || {};
  return { kind:'directory', name:name, _kids:kids,
    async getDirectoryHandle(n,o){ if(kids[n]) return kids[n];
      if(o&&o.create){ kids[n]=fakeDir(n,{}); return kids[n]; }
      const e=new Error('nf'); e.name='NotFoundError'; throw e; },
    async removeEntry(n){ delete kids[n]; },
    entries(){ const l=Object.entries(kids); let i=0;
      return { [Symbol.asyncIterator](){return this;},
               async next(){ return i<l.length?{value:l[i++],done:false}:{done:true}; } }; } };
}
window.__root = fakeDir('めだか写真', {
  '編集前': fakeDir('編集前', {
    '忘却の翼_MD-260904-002': fakeDir('忘却の翼_MD-260904-002',
        {'b.jpg':fakeFile('b.jpg'), 'a.jpg':fakeFile('a.jpg')}),
    '幹之_MD-260904-001': fakeDir('幹之_MD-260904-001', {'p1.jpg':fakeFile('p1.jpg')}),
    '夜桜_MD-260904-003': fakeDir('夜桜_MD-260904-003', {}),
  }),
  '編集後': fakeDir('編集後', {})
});
fsRoot = null; fsRestoreRoot = async () => window.__root;
'ok'""")

print("■ 登録が1件も残っていなくても、フォルダから読める")
b.ev("localStorage.setItem('medaka_reg_items','[]')")
b.ev("(async()=>{ await fsLoadFromFolders(); })()"); time.sleep(1.0)
r.check("フォルダの数だけ商品が並ぶ", b.ev("products.length"), 3)
r.check("名前順に並ぶ", b.ev("products.map(p=>p.controlNo).join(',')"),
        "MD-260904-001,MD-260904-002,MD-260904-003")
r.check("品種名をフォルダ名から取れる", b.ev("products.map(p=>p.variety).join(',')"), "幹之,忘却の翼,夜桜")
r.check("写真も読める", b.ev("photos.length"), 3)
r.check("写真は商品ごとに分かれる", b.ev("JSON.stringify(products.map(p=>p.specimenIdxs.length))"), "[1,2,0]")
r.check("フォルダの中も名前順", b.ev("products[1].specimenIdxs.map(i=>photos[i].name).join(',')"), "a.jpg,b.jpg")
r.expect("写真が無いフォルダも並ぶ（撮り忘れが分かる）",
         b.ev("products[2].specimenIdxs.length") == 0, "夜桜は0枚で表示")
r.check("画面にも3件出る", b.ev("document.querySelectorAll('#folderList .folder').length"), 3)
r.expect("読み込み後の画面になる",
         not b.ev("document.getElementById('editLoaded').classList.contains('hidden')"), "editLoaded 表示")

print("■ 登録が残っていれば、ランクと数量も引き継ぐ")
b.ev("""localStorage.setItem('medaka_reg_items', JSON.stringify([
  {variety:'幹之', rank:'特上', quantityText:'3ペア', controlNo:'MD-260904-001'}
])); 'ok'""")
b.ev("(async()=>{ await fsLoadFromFolders(); })()"); time.sleep(1.0)
r.check("登録があるものはランクが入る", b.ev("products.find(p=>p.controlNo==='MD-260904-001').rank"), "特上")
r.check("数量も入る", b.ev("products.find(p=>p.controlNo==='MD-260904-001').quantityText"), "3ペア")
r.check("登録が無いものは空のまま", b.ev("products.find(p=>p.controlNo==='MD-260904-003').rank"), "")
r.check("それでも3件そろう", b.ev("products.length"), 3)

print("■ 保管するときは、読み込んだときのフォルダ名を使う")
r.check("フォルダ名を覚えている", b.ev("products.map(p=>p.folderName).join(',')"),
        "幹之_MD-260904-001,忘却の翼_MD-260904-002,夜桜_MD-260904-003")

print("■ フォルダ名を品種と管理番号に分ける")
r.check("ふつう", b.ev("JSON.stringify(fsParseFolderName('幹之_MD-260904-001'))"),
        '{"variety":"幹之","controlNo":"MD-260904-001"}')
r.check("品種に _ が入っていても最後で分ける",
        b.ev("JSON.stringify(fsParseFolderName('赤_白_ラメ_MD-1'))"),
        '{"variety":"赤_白_ラメ","controlNo":"MD-1"}')
r.check("_ が無ければ全部を品種として扱う", b.ev("JSON.stringify(fsParseFolderName('幹之'))"),
        '{"variety":"幹之","controlNo":""}')

print("■ 中が空のとき")
b.ev("window.__root._kids['編集前']._kids = {}; localStorage.setItem('medaka_reg_items','[]'); 'ok'")
b.ev("(async()=>{ await fsLoadFromFolders(); })()"); time.sleep(0.6)
r.expect("空でも落ちない", isinstance(b.ev("products.length"), int), "products=" + str(b.ev("products.length")))

b.close(); r.finish()
