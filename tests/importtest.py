# -*- coding: utf-8 -*-
"""カメラ（USBテザー）からの自動取り込みと、SDカードからの一括取り込み。"""
import time, json
from common import Browser, Report

b = Browser(9408, 1200, 1000); r = Report()
b.ev("localStorage.clear()"); time.sleep(0.3)

b.ev(r"""
const PNG='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==';
function bin(){ const s=atob(PNG); const u=new Uint8Array(s.length);
  for(let i=0;i<s.length;i++) u[i]=s.charCodeAt(i); return u; }
function shot(name, at){
  const f = new File([new Blob([bin()],{type:'image/jpeg'})], name, {type:'image/jpeg', lastModified:at});
  return { kind:'file', name, getFile: async () => f };
}
window.__cardFiles = { 'DSC_0001.JPG': shot('DSC_0001.JPG', 1000),
                       'DSC_0002.JPG': shot('DSC_0002.JPG', 2000),
                       'DSC_0003.NEF': shot('DSC_0003.NEF', 3000),
                       'メモ.txt':      shot('メモ.txt', 4000) };
window.__card = { kind:'directory', name:'DCIM',
  entries(){ const l=Object.entries(window.__cardFiles); let i=0;
    return { [Symbol.asyncIterator](){return this;},
      async next(){ return i<l.length?{value:l[i++],done:false}:{done:true}; } }; } };
'ok'""")

print("■ 写真だけを拾い、新しい順に並べる")
lst = b.ev("(async()=>{ const a = await Watch.list(window.__card); return a.map(x=>x.name).join(','); })()")
r.check("JPEGだけ拾う（NEFとtxtは除く）", lst, "DSC_0002.JPG,DSC_0001.JPG")
r.check("RAWがあったことは覚えておく", b.ev("Watch.sawRaw"), True)

print("■ 新しく入ってきた写真だけを拾う")
b.ev("Watch.dir = window.__card; Watch.seen = new Set(); 'ok'")
b.ev("""window.__got = [];
(async()=>{ await Watch.start({controlNo:'MD-1'}, async (x) => { window.__got.push(x.name); }); })()""")
time.sleep(0.6)
r.check("いまあるものは拾わない（撮る前の分）", b.ev("window.__got.length"), 0)
b.ev("window.__cardFiles['DSC_0004.JPG'] = shot('DSC_0004.JPG', 5000); 'ok'")
time.sleep(2.6)
r.check("あとから入った1枚だけ拾う", b.ev("window.__got.join(',')"), "DSC_0004.JPG")
r.check("枚数を数えている", b.ev("Watch.found"), 1)
b.ev("window.__cardFiles['DSC_0005.JPG'] = shot('DSC_0005.JPG', 6000); 'ok'")
time.sleep(2.6)
r.check("続けて入っても拾う", b.ev("window.__got.join(',')"), "DSC_0004.JPG,DSC_0005.JPG")
r.check("同じ写真を二度拾わない", b.ev("window.__got.length"), 2)
b.ev("Watch.stop()")
r.check("やめられる", b.ev("Watch.running"), False)
time.sleep(2.2)
b.ev("window.__cardFiles['DSC_0006.JPG'] = shot('DSC_0006.JPG', 7000); 'ok'")
time.sleep(2.4)
r.check("やめたあとは拾わない", b.ev("window.__got.length"), 2)

print("■ その商品のフォルダへ入れる")
b.ev(r"""
window.__into = {};
fsEnsureFolder = async () => ({ kind:'directory', name:'幹之_MD-1', _files: window.__into,
  async getFileHandle(n,o){ if(!(n in window.__into)){ if(!o||!o.create){const e=new Error('nf');e.name='NotFoundError';throw e;} window.__into[n]=null; }
    return { async createWritable(){ return { async write(b){ window.__into[n]=b; }, async close(){} }; } }; },
  entries(){ const l=Object.entries(window.__into); let i=0;
    return { [Symbol.asyncIterator](){return this;},
      async next(){ return i<l.length?{value:[l[i][0],{kind:'file',name:l[i++][0]}],done:false}:{done:true}; } }; } });
'ok'""")
n = b.ev("""(async()=>{
  const shots = await Watch.list(window.__card);
  return await importShots({variety:'幹之', controlNo:'MD-1'}, shots.slice(0,2));
})()""")
time.sleep(0.6)
r.check("選んだ2枚が入る", n, 2)
r.check("管理番号＋連番の名前になる",
        b.ev("Object.keys(window.__into).sort().join(',')"), "MD-1_01.jpg,MD-1_02.jpg")

print("■ 続けて取り込むと番号が続く")
n2 = b.ev("""(async()=>{
  const shots = await Watch.list(window.__card);
  return await importShots({variety:'幹之', controlNo:'MD-1'}, shots.slice(0,1));
})()""")
time.sleep(0.5)
r.check("1枚追加", n2, 1)
r.check("_03 になる", b.ev("Object.keys(window.__into).sort().join(',')"),
        "MD-1_01.jpg,MD-1_02.jpg,MD-1_03.jpg")

print("■ 拡張子の扱い")
r.check("JPGは jpg に揃える", b.ev("'DSC.JPG'.match(CAM_IMG_RE)[1].toLowerCase()"), "jpg")
r.check("NEFは写真として扱わない", b.ev("CAM_IMG_RE.test('DSC.NEF')"), False)
r.check("NEFはRAWと分かる", b.ev("CAM_RAW_RE.test('DSC.NEF')"), True)
r.check("CR3もRAW", b.ev("CAM_RAW_RE.test('IMG.CR3')"), True)

print("■ 画面の入口")
r.expect("登録タブから開ける", b.ev("!!document.getElementById('regImport')"), "📥 カメラ・SDから取り込む")
r.expect("編集タブからも開ける", b.ev("!!document.getElementById('btnEditImport')"), "同じ入口")
r.expect("撮影画面からも見張れる", b.ev("!!document.getElementById('camWatch')"), "📷 カメラから自動で取り込む")

b.close(); r.finish()
