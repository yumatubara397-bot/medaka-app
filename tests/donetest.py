# -*- coding: utf-8 -*-
"""保管した「編集後」から選んで、あとからでも出品ファイルを作れるかを確かめる。"""
import time
from common import Browser, Report

b = Browser(9403, 1200, 1000); r = Report()
b.ev("localStorage.clear()"); time.sleep(0.3)

b.ev(r"""
const PNG='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==';
function bin(){ const s=atob(PNG); const u=new Uint8Array(s.length);
  for(let i=0;i<s.length;i++) u[i]=s.charCodeAt(i); return u; }
function fFile(name, text){
  const blob = text!=null ? new Blob([text],{type:'application/json'})
                          : new Blob([bin()],{type:'image/png'});
  return { kind:'file', name, getFile: async()=>new File([blob], name) };
}
function fDir(name, kids){
  kids = kids||{};
  return { kind:'directory', name, _kids:kids,
    async getDirectoryHandle(n,o){ const k=kids[n];
      if(k && k.kind==='directory') return k;
      if(o&&o.create){ kids[n]=fDir(n,{}); return kids[n]; }
      const e=new Error('nf'); e.name='NotFoundError'; throw e; },
    async getFileHandle(n,o){ const k=kids[n];
      if(k && k.kind==='file') return k;
      const e=new Error('nf'); e.name='NotFoundError'; throw e; },
    entries(){ const l=Object.entries(kids); let i=0;
      return { [Symbol.asyncIterator](){return this;},
        async next(){ return i<l.length?{value:l[i++],done:false}:{done:true}; } }; } };
}
window.__done = fDir('編集後', {
  '幹之_MD-1': fDir('幹之_MD-1', {
    '商品.json': fFile('商品.json', JSON.stringify({variety:'幹之',rank:'特上',quantityText:'3ペア',controlNo:'MD-1'})),
    '原本':   fDir('原本',   {'a.jpg':fFile('a.jpg'), 'b.jpg':fFile('b.jpg')}),
    '加工後': fDir('加工後', {'a.jpg':fFile('a.jpg'), 'b.jpg':fFile('b.jpg')})
  }),
  '夜桜_MD-2': fDir('夜桜_MD-2', {      // 古い保管（商品.json が無い）
    '原本': fDir('原本', {'p.jpg':fFile('p.jpg')})
  }),
  '空_MD-3': fDir('空_MD-3', { '原本': fDir('原本', {}) })
});
fsDoneDir = async () => window.__done;
'ok'""")

print("■ 編集後に何があるか調べる")
b.ev("(async()=>{ window.__list = await doneList(); })()"); time.sleep(0.6)
r.check("3件見つかる", b.ev("window.__list.length"), 3)
r.check("管理番号の新しい順に並ぶ", b.ev("window.__list.map(x=>x.folder).join(',')"), "空_MD-3,夜桜_MD-2,幹之_MD-1")
r.check("商品.json からランクと数量を読む",
        b.ev("(window.__list.find(x=>x.controlNo==='MD-1')||{}).rank + '/' + (window.__list.find(x=>x.controlNo==='MD-1')||{}).quantityText"),
        "特上/3ペア")
r.check("加工後があればそちらを使う", b.ev("(window.__list.find(x=>x.controlNo==='MD-1')||{}).from"), "加工後")
r.check("枚数も数える", b.ev("(window.__list.find(x=>x.controlNo==='MD-1')||{}).photos"), 2)
r.check("商品.json が無くてもフォルダ名から読み取る",
        b.ev("(window.__list.find(x=>x.folder==='夜桜_MD-2')||{}).variety"), "夜桜")
r.check("加工後が無ければ原本を使う", b.ev("(window.__list.find(x=>x.folder==='夜桜_MD-2')||{}).from"), "原本")
r.check("写真が無いものは0枚", b.ev("(window.__list.find(x=>x.folder==='空_MD-3')||{}).photos"), 0)

print("■ 選んで読み込む")
b.ev("(async()=>{ await doneLoad(window.__list.filter(x=>x.photos)); })()"); time.sleep(1.0)
r.check("2件読み込む", b.ev("products.length"), 2)
r.check("写真は3枚", b.ev("photos.length"), 3)
r.check("商品ごとに分かれる", b.ev("JSON.stringify(products.map(p=>p.specimenIdxs.length))"), "[1,2]")
r.check("ランクと数量も入る",
        b.ev("(products.find(p=>p.controlNo==='MD-1')||{}).rank"), "特上")
r.check("フォルダ名も覚えている",
        b.ev("(products.find(p=>p.controlNo==='MD-1')||{}).folderName"), "幹之_MD-1")
r.expect("出品の画面になる",
         not b.ev("document.getElementById('listingLoaded').classList.contains('hidden')"), "listingLoaded 表示")

print("■ 選ぶ画面")
b.ev("showDonePicker()"); time.sleep(0.8)
r.check("3件並ぶ", b.ev("document.querySelectorAll('#doneDialog .dpick').length"), 3)
r.check("写真の無いものは選べない",
        b.ev("document.querySelectorAll('#doneDialog .dpick[disabled]').length"), 1)
r.expect("最初は読み込めない", b.ev("document.getElementById('doneGo').disabled"), "選ぶまで押せない")
b.ev("document.getElementById('donePickAll').click()"); time.sleep(0.3)
r.check("全選択は写真のあるものだけ",
        b.ev("document.querySelectorAll('#doneDialog .dpick:checked').length"), 2)
r.check("件数がボタンに出る", b.ev("document.getElementById('doneGo').textContent"), "2件を読み込む")
b.ev("document.getElementById('donePickNone').click()"); time.sleep(0.3)
r.expect("全解除でまた押せなくなる", b.ev("document.getElementById('doneGo').disabled"), "0件")
b.ev("document.getElementById('doneClose').click()"); time.sleep(0.2)
r.expect("閉じられる", b.ev("document.getElementById('doneDialog').classList.contains('hidden')"), "hidden")

print("■ 何も無いとき")
b.ev("window.__done = fDir('編集後', {}); fsDoneDir = async () => window.__done; showDonePicker()")
time.sleep(0.6)
r.expect("空だと分かる案内が出る",
         "まだ何もありません" in (b.ev("document.getElementById('doneDialog').textContent") or ""),
         b.ev("document.getElementById('doneDialog').textContent")[:60])

b.close(); r.finish()
