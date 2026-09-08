# -*- coding: utf-8 -*-
"""「写真を撮る」を押したら、その場でカメラが立ち上がり、
   撮った写真がその商品のフォルダに保存されるかを確かめる。"""
import time
from common import Browser, Report

b = Browser(9400, 1200, 1000); r = Report()
b.ev("localStorage.clear()"); time.sleep(0.4)

# にせのフォルダ（書き込みを記録する）
b.ev(r"""
function fakeDir(name, files){
  files = files || {};
  return { kind:'directory', name:name, _files:files,
    async getFileHandle(n, o){
      if(!(n in files)){ if(!o||!o.create){ const e=new Error('nf'); e.name='NotFoundError'; throw e; } files[n]=null; }
      return { async createWritable(){ return { async write(b){ files[n]=b; }, async close(){} }; },
               async getFile(){ return files[n]; } };
    },
    entries(){ const l=Object.entries(files); let i=0;
      return { [Symbol.asyncIterator](){return this;},
        async next(){ return i<l.length ? {value:[l[i][0], {kind:'file', name:l[i++][0]}], done:false} : {done:true}; } }; }
  };
}
window.__dir = fakeDir('幹之_MD-260905-001', {});
fsEnsureFolder = async () => window.__dir;
window.__item = { variety:'幹之', rank:'特上', quantityText:'3ペア', controlNo:'MD-260905-001' };
'ok'""")

print("■ カメラが使えないときも、理由が出て写真は入れられる")
b.ev("""
navigator.mediaDevices.getUserMedia = async () => {
  const e = new Error('no'); e.name = 'NotAllowedError'; throw e; };
'ok'""")
b.ev("(async()=>{ await Cam.open(window.__item); })()"); time.sleep(0.6)
r.expect("撮影画面が開く", not b.ev("document.getElementById('camDialog').classList.contains('hidden')"), "camDialog 表示")
r.check("どの商品か出る", b.ev("document.getElementById('camNo').textContent"), "MD-260905-001")
r.expect("保存先も出る", "編集前/幹之_MD-260905-001/" in (b.ev("document.getElementById('camSub').textContent") or ""),
         b.ev("document.getElementById('camSub').textContent"))
msg = b.ev("document.getElementById('camMsg').textContent") or ""
r.expect("許可が無い理由が出る", "許可" in msg, msg[:60])
r.expect("ファイルからも入れられると伝える", "ファイルから追加" in msg, "代わりの道を示す")

print("■ 撮ったものは、押すまで保存されない")
b.ev("""
  const f = new File([new Blob(['x'])], 'IMG_001.JPG', {type:'image/jpeg'});
  Cam.addFiles([f]); 'ok'"""); time.sleep(0.4)
r.check("手元に1枚ある", b.ev("Cam.pending.length"), 1)
r.check("まだフォルダには入っていない", b.ev("Object.keys(window.__dir._files).length"), 0)
r.expect("保存先が出る", "編集前 / 幹之_MD-260905-001" in (b.ev("document.getElementById('camDest').textContent") or ""),
         b.ev("document.getElementById('camDest').textContent"))
r.check("保存ボタンに枚数が出る", b.ev("document.getElementById('camSave').textContent"), "💾 1枚を保存する")

print("■ ×ですぐ消せる")
b.ev("""Cam.addFiles([new File([new Blob(['y'])], 'a.png', {type:'image/png'}),
                     new File([new Blob(['z'])], 'b.jpeg', {type:'image/jpeg'})]); 'ok'""")
time.sleep(0.3)
r.check("3枚ためた", b.ev("Cam.pending.length"), 3)
r.check("×ボタンも3つ", b.ev("document.querySelectorAll('#camShots .x').length"), 3)
b.ev("document.querySelectorAll('#camShots .x')[1].click()"); time.sleep(0.3)
r.check("押した1枚だけ消える", b.ev("Cam.pending.length"), 2)
r.check("残ったのは1枚目と3枚目", b.ev("Cam.pending.map(p=>p.ext).join(',')"), "jpg,jpg")
r.check("番号が振り直される", b.ev("[...document.querySelectorAll('#camShots .n')].map(e=>e.textContent).join(',')"), "1,2")
r.check("消してもフォルダは空のまま", b.ev("Object.keys(window.__dir._files).length"), 0)

print("■ 保存するボタンで、そのフォルダに入る")
b.ev("(async()=>{ await Cam.saveAll(); })()"); time.sleep(0.6)
r.check("2枚入る", b.ev("Object.keys(window.__dir._files).length"), 2)
r.check("管理番号＋連番の名前になる",
        b.ev("Object.keys(window.__dir._files).sort().join(',')"),
        "MD-260905-001_01.jpg,MD-260905-001_02.jpg")
r.check("手元は空になる", b.ev("Cam.pending.length"), 0)
r.expect("保存の帯が消える", b.ev("document.getElementById('camSaveBar').classList.contains('hidden')"), "hidden")

print("■ 続けて撮ると番号が続く")
b.ev("""Cam.addFiles([new File([new Blob(['w'])], 'c.jpg', {type:'image/jpeg'})]); 'ok'""")
b.ev("(async()=>{ await Cam.saveAll(); })()"); time.sleep(0.5)
r.check("3枚目は _03", b.ev("Object.keys(window.__dir._files).sort().join(',')"),
        "MD-260905-001_01.jpg,MD-260905-001_02.jpg,MD-260905-001_03.jpg")

print("■ シャッター音")
r.expect("音を鳴らす仕掛けがある", b.ev("typeof camShutterSound"), "function")
r.expect("音のファイルを持たずに鳴らす",
         b.ev("(()=>{ try{ camShutterSound(); return 'ok'; }catch(e){ return 'ERR '+e.message; } })()") == 'ok',
         "その場で作る")

print("■ すでに写真が入っているフォルダでも、上書きしない")
b.ev("window.__dir2 = fakeDir('夜桜_MD-9', {'MD-9_01.jpg':1, 'MD-9_07.jpg':1}); 'ok'")
r.check("次は8番から", b.ev("(async()=>await Cam.nextIndex(window.__dir2))()"), 8)

print("■ 保存が済めば手元は空になる")
r.check("並びも空になる", b.ev("document.querySelectorAll('#camShots .cam-shot').length"), 0)

print("■ 終わると片付く")
b.ev("Cam.close()"); time.sleep(0.4)
r.expect("画面が閉じる", b.ev("document.getElementById('camDialog').classList.contains('hidden')"), "hidden")
r.check("カメラを止める", b.ev("Cam.stream"), None)

print("■ 「写真を撮る」は編集タブに飛ばさない")
b.ev("""localStorage.setItem('medaka_reg_items', JSON.stringify([
  {variety:'幹之', rank:'特上', quantityText:'3ペア', controlNo:'MD-260905-001'}]));
regSel.lastNo = 'MD-260905-001'; renderRegDone();
window.__realOpen = Cam.open;
window.__opened = null; Cam.open = async (it) => { window.__opened = it.controlNo; };
'ok'""")
time.sleep(0.3)
r.check("ボタンの文言", b.ev("document.getElementById('regGoPhotos').textContent"), "📷 写真を撮る")
b.ev("document.getElementById('regGoPhotos').click()"); time.sleep(0.4)
r.check("押すとカメラが開く", b.ev("window.__opened"), "MD-260905-001")
r.expect("編集タブに移らない",
         b.ev("document.getElementById('panel-register').classList.contains('hidden')") == False,
         "登録タブのまま")

print("■ 登録一覧からも撮れる")
b.ev("""localStorage.setItem('medaka_reg_items', JSON.stringify([
  {variety:'幹之', rank:'特上', quantityText:'3ペア', controlNo:'MD-260905-001'},
  {variety:'舞めだかゴールドフード', rank:'', quantityText:'1個', controlNo:'YO-01', kind:'goods'}
])); renderRegItems(); 'ok'""")
time.sleep(0.4)
r.check("メダカにはカメラボタンが付く", b.ev("document.querySelectorAll('#regItemList .cam').length"), 1)
r.expect("用品には付かない",
         b.ev("!!document.querySelector('#regItemList .reg-item.goods .cam')") == False,
         "用品は撮らない")
b.ev("window.__opened = null; document.querySelector('#regItemList .cam').click()"); time.sleep(0.4)
r.check("押すとその商品のカメラが開く", b.ev("window.__opened"), "MD-260905-001")


print("■ 撮る形（既定は正方形）")
b.ev("localStorage.removeItem('medaka_camera_ratio')")
r.check("はじめは正方形", b.ev("camRatioKey()"), "1:1")
r.check("横縦比は1", b.ev("camRatioValue()"), 1)
b.ev("localStorage.setItem('medaka_camera_ratio','3:4')")
r.check("縦長も選べる", b.ev("camRatioKey()"), "3:4")
r.check("その比率になる", b.ev("Math.round(camRatioValue()*100)/100"), 0.75)
b.ev("localStorage.setItem('medaka_camera_ratio','full')")
r.check("カメラのままも選べる", b.ev("camRatioKey()"), "full")
r.check("そのときは切り出さない", b.ev("camRatioValue()"), None)
b.ev("localStorage.setItem('medaka_camera_ratio','へんな値')")
r.check("知らない値なら正方形に戻す", b.ev("camRatioKey()"), "1:1")

print("■ 真ん中を切り出す")
r.check("横長から正方形（1600x1200 → 1200x1200）",
        b.ev("JSON.stringify(camCropRect(1600,1200,1))"), '{"sx":200,"sy":0,"sw":1200,"sh":1200}')
r.check("縦長から正方形（1200x1600 → 1200x1200）",
        b.ev("JSON.stringify(camCropRect(1200,1600,1))"), '{"sx":0,"sy":200,"sw":1200,"sh":1200}')
r.check("すでに正方形なら切らない",
        b.ev("JSON.stringify(camCropRect(1000,1000,1))"), '{"sx":0,"sy":0,"sw":1000,"sh":1000}')
r.check("縦長に切り出す（1600x1200 → 900x1200）",
        b.ev("JSON.stringify(camCropRect(1600,1200,0.75))"), '{"sx":350,"sy":0,"sw":900,"sh":1200}')
r.check("カメラのままなら丸ごと",
        b.ev("JSON.stringify(camCropRect(1600,1200,null))"), '{"sx":0,"sy":0,"sw":1600,"sh":1200}')

print("■ 画面の枠も、選んだ形に合わせる")
b.ev("localStorage.setItem('medaka_camera_ratio','1:1'); Cam.applyRatio()"); time.sleep(0.2)
r.check("正方形の枠", b.ev("document.getElementById('camView').style.aspectRatio"), "1 / 1")
r.check("選択も合っている", b.ev("document.getElementById('camRatio').value"), "1:1")
b.ev("localStorage.setItem('medaka_camera_ratio','16:9'); Cam.applyRatio()"); time.sleep(0.2)
r.check("横に広い枠", b.ev("document.getElementById('camView').style.aspectRatio"), "16 / 9")
r.expect("見えている範囲がそのまま写る（はみ出しは切る）",
         b.ev("!document.getElementById('camView').classList.contains('full')"), "object-fit: cover")
b.ev("localStorage.setItem('medaka_camera_ratio','full'); Cam.applyRatio()"); time.sleep(0.2)
r.expect("カメラのままなら全体を映す",
         b.ev("document.getElementById('camView').classList.contains('full')"), "object-fit: contain")
b.ev("localStorage.setItem('medaka_camera_ratio','1:1')")



print("■ ズーム")
b.ev("localStorage.removeItem('medaka_camera_zoom')")
r.check("はじめは等倍", b.ev("camZoomPct()"), 100)
b.ev("localStorage.setItem('medaka_camera_zoom','250')")
r.check("覚える", b.ev("camZoomPct()"), 250)
b.ev("localStorage.setItem('medaka_camera_zoom','9999')")
r.check("行き過ぎは400%まで", b.ev("camZoomPct()"), 400)
b.ev("localStorage.setItem('medaka_camera_zoom','10')")
r.check("100%より引けない", b.ev("camZoomPct()"), 100)

print("■ ズームぶん、真ん中を狭く切り出す")
r.check("等倍なら形だけ（1600x1200 → 1200x1200）",
        b.ev("JSON.stringify(camCropRect(1600,1200,1,1))"), '{"sx":200,"sy":0,"sw":1200,"sh":1200}')
r.check("2倍なら半分（1200x1200 → 600x600・真ん中）",
        b.ev("JSON.stringify(camCropRect(1600,1200,1,2))"), '{"sx":500,"sy":300,"sw":600,"sh":600}')
r.check("形なし＋2倍でも真ん中",
        b.ev("JSON.stringify(camCropRect(1600,1200,null,2))"), '{"sx":400,"sy":300,"sw":800,"sh":600}')
r.check("ズーム未指定は等倍と同じ",
        b.ev("JSON.stringify(camCropRect(1600,1200,1))"), '{"sx":200,"sy":0,"sw":1200,"sh":1200}')

print("■ カメラ本体がズームを持っていれば、そちらを使う")
b.ev("""window.__applied = [];
Cam.stream = { getVideoTracks: () => [{
  getCapabilities: () => ({ zoom:{min:1,max:2,step:0.1} }),
  getSettings: () => ({ zoom:1 }),
  applyConstraints: async (c) => { window.__applied.push(c); }
}] };
localStorage.setItem('medaka_camera_zoom','200'); 'ok'""")
b.ev("(async()=>{ await Cam.applyZoom(); })()"); time.sleep(0.4)
r.check("本体に2倍を頼む", b.ev("JSON.stringify(window.__applied.slice(-1)[0])"), '{"advanced":[{"zoom":2}]}')
r.check("画像側では寄せない（画質を落とさない）", b.ev("Cam.softZoom"), 1)

print("■ 本体で足りない分は、画像側で寄せる")
b.ev("localStorage.setItem('medaka_camera_zoom','400')")
b.ev("(async()=>{ await Cam.applyZoom(); })()"); time.sleep(0.4)
r.check("本体は上限の2倍まで", b.ev("JSON.stringify(window.__applied.slice(-1)[0])"), '{"advanced":[{"zoom":2}]}')
r.check("残りの2倍を画像側で受け持つ", b.ev("Cam.softZoom"), 2)

print("■ 本体にズームが無くても効く")
b.ev("""Cam.stream = { getVideoTracks: () => [{
  getCapabilities: () => ({}), getSettings: () => ({}), applyConstraints: async () => {} }] };
localStorage.setItem('medaka_camera_zoom','300'); 'ok'""")
b.ev("(async()=>{ await Cam.applyZoom(); })()"); time.sleep(0.4)
r.check("全部を画像側で受け持つ", b.ev("Cam.softZoom"), 3)
r.expect("画面も同じだけ寄る（見える範囲＝写る範囲）",
         "scale(3)" in (b.ev("document.getElementById('camVideo').style.transform") or ""),
         b.ev("document.getElementById('camVideo').style.transform"))

print("■ ボタンとゲージ")
b.ev("camSetZoom(100)"); time.sleep(0.2)
r.check("戻すで等倍", b.ev("camZoomPct()"), 100)
b.ev("document.getElementById('camZoomIn').click()"); time.sleep(0.3)
r.check("＋で25%ずつ寄る", b.ev("camZoomPct()"), 125)
b.ev("document.getElementById('camZoomOut').click()"); time.sleep(0.3)
r.check("−で戻る", b.ev("camZoomPct()"), 100)
b.ev("document.getElementById('camZoomOut').click()"); time.sleep(0.3)
r.check("等倍より引けない", b.ev("camZoomPct()"), 100)
r.check("ゲージにも出る", b.ev("document.getElementById('camZoomVal').textContent"), "100%")
b.ev("Cam.stream = null")


print("■ ピント")
b.ev("localStorage.removeItem('medaka_camera_focus')")
r.check("既定は追いかける（動くメダカ向き）", b.ev("camFocusMode()"), "continuous")
b.ev("localStorage.setItem('medaka_camera_focus','manual')")
r.check("手で合わせるも選べる", b.ev("camFocusMode()"), "manual")
b.ev("localStorage.setItem('medaka_camera_focus','へんな値')")
r.check("知らない値なら追いかけるに戻す", b.ev("camFocusMode()"), "continuous")

b.ev("""window.__c = [];
Cam.stream = { getVideoTracks: () => [{
  getCapabilities: () => ({ focusMode:['continuous','single-shot','manual'],
                            pointsOfInterest:true,
                            exposureMode:['continuous','manual'], exposureTime:{min:10,max:1000,step:10},
                            frameRate:{min:1,max:60} }),
  getSettings: () => ({}),
  applyConstraints: async (c) => { window.__c.push(JSON.stringify(c)); }
}] }; 'ok'""")
r.check("追いかけるを伝える", b.ev("(async()=>await Cam.applyFocus())()"), True)
r.expect("continuous を頼む", "continuous" in (b.ev("window.__c.slice(-1)[0]") or ""), b.ev("window.__c.slice(-1)[0]"))

b.ev("localStorage.setItem('medaka_camera_focus','single'); window.__c = []")
b.ev("(async()=>await Cam.applyFocus())()"); time.sleep(0.2)
r.expect("1回だけは single-shot を頼む", "single-shot" in (b.ev("window.__c.slice(-1)[0]") or ""),
         b.ev("window.__c.slice(-1)[0]"))

print("■ 動きを止める")
b.ev("localStorage.removeItem('medaka_camera_motion')")
r.check("既定は止める", b.ev("camStopMotion()"), True)
b.ev("window.__c = []")
r.check("設定できる", b.ev("(async()=>await Cam.applyMotion())()"), True)
allc = b.ev("window.__c.join(' ')") or ""
r.expect("露出を短くする", "exposureTime" in allc, "ブレを減らす")
r.expect("フレームレートも上げる", "frameRate" in allc, "少しでもブレを減らす")
b.ev("localStorage.setItem('medaka_camera_motion','off'); window.__c = []")
r.check("いいえなら自動に戻す", b.ev("(async()=>await Cam.applyMotion())()"), False)
r.expect("カメラ任せに戻す", "continuous" in (b.ev("window.__c.join(' ')") or ""), "exposureMode: continuous")
b.ev("localStorage.setItem('medaka_camera_motion','on')")

print("■ 押したところにピントを合わせる")
b.ev("window.__c = []")
r.check("場所を伝えられる", b.ev("(async()=>await Cam.focusAt(25, 75))()"), True)
c = b.ev("window.__c.join(' ')") or ""
r.expect("押した位置を割合で渡す", '"x":0.25' in c and '"y":0.75' in c, c[:80])
r.expect("印が出る", not b.ev("document.getElementById('camFocusMark').classList.contains('hidden')"), "光る円")

print("■ ピントを選べないカメラでは、そう言う")
b.ev("""Cam.stream = { getVideoTracks: () => [{
  getCapabilities: () => ({}), getSettings: () => ({}), applyConstraints: async () => {} }] }; 'ok'""")
r.check("できないと分かる", b.ev("(async()=>await Cam.applyFocus())()"), False)
r.check("動きの設定もできない", b.ev("(async()=>await Cam.applyMotion())()"), False)
b.ev("Cam.stream = null")

print("■ 詳しい設定")
b.ev("['medaka_camera_size','medaka_camera_quality','medaka_camera_grid'].forEach(k=>localStorage.removeItem(k))")
r.check("大きさの既定", b.ev("camSize()"), 1920)
r.check("画質の既定", b.ev("camQuality()"), 0.92)
r.check("目安の線の既定", b.ev("camGrid()"), "none")
b.ev("localStorage.setItem('medaka_camera_size','2560')")
r.check("大きさを変えられる", b.ev("camSize()"), 2560)
b.ev("localStorage.setItem('medaka_camera_quality','0.96')")
r.check("画質を変えられる", b.ev("camQuality()"), 0.96)
b.ev("localStorage.setItem('medaka_camera_quality','9')")
r.check("ありえない画質は既定に戻す", b.ev("camQuality()"), 0.92)
b.ev("localStorage.setItem('medaka_camera_grid','へんな値')")
r.check("知らない線の指定はなしに戻す", b.ev("camGrid()"), "none")

print("■ 目安の線")
b.ev("localStorage.setItem('medaka_camera_grid','thirds'); Cam.applyGrid()"); time.sleep(0.2)
r.check("三分割は4本", b.ev("document.querySelectorAll('#camGridOverlay line').length"), 4)
b.ev("localStorage.setItem('medaka_camera_grid','center'); Cam.applyGrid()"); time.sleep(0.2)
r.check("十字は2本", b.ev("document.querySelectorAll('#camGridOverlay line').length"), 2)
b.ev("localStorage.setItem('medaka_camera_grid','none'); Cam.applyGrid()"); time.sleep(0.2)
r.check("なしは0本", b.ev("document.querySelectorAll('#camGridOverlay line').length"), 0)

print("■ つまみは、カメラが本当に持っている機能だけ出す")
b.ev("""Cam.stream = { getVideoTracks: () => [{
  getCapabilities: () => ({ zoom:{min:1,max:4,step:0.1}, exposureCompensation:{min:-2,max:2,step:0.1},
                            focusMode:['continuous'], contrast:{min:0,max:0} }),
  getSettings: () => ({ zoom:1, exposureCompensation:0 }),
  applyConstraints: async () => {}
}] }; Cam.renderCaps(); 'ok'"""); time.sleep(0.3)
r.check("使えるものだけ並ぶ", b.ev("document.querySelectorAll('#camCaps input[data-cap]').length"), 2)
r.check("ズームがある", b.ev("!!document.querySelector('#camCaps input[data-cap=zoom]')"), True)
r.expect("幅のない項目は出さない（contrast は min=max=0）",
         not b.ev("!!document.querySelector('#camCaps input[data-cap=contrast]')"), "効かないつまみは出さない")
r.expect("一覧だけの項目も出さない（focusMode）",
         not b.ev("!!document.querySelector('#camCaps input[data-cap=focusMode]')"), "範囲でないものは対象外")

b.ev("""Cam.stream = { getVideoTracks: () => [{
  getCapabilities: () => ({}), getSettings: () => ({}), applyConstraints: async () => {} }] };
Cam.renderCaps(); 'ok'"""); time.sleep(0.3)
r.check("何も使えなければ空", b.ev("document.querySelectorAll('#camCaps input[data-cap]').length"), 0)
r.expect("そのときは、その旨を伝える",
         "できません" in (b.ev("document.getElementById('camCapsNote').textContent") or ""),
         b.ev("document.getElementById('camCapsNote').textContent"))
b.ev("Cam.stream = null")

print("■ どのカメラを使うかの選び分け")
def choose(devs, saved="null"):
    import json
    return b.ev(f"(camChoose({devs}, {saved})||{{}}).label")

r.check("外側(Rear)を選ぶ",
        choose("[{deviceId:'a',label:'Surface Camera Front'},{deviceId:'b',label:'Surface Camera Rear'}]"),
        "Surface Camera Rear")
r.check("Back という名前でも選ぶ",
        choose("[{deviceId:'a',label:'Integrated Webcam (Front)'},{deviceId:'b',label:'Back Camera'}]"),
        "Back Camera")
r.check("日本語の「背面」も選ぶ",
        choose("[{deviceId:'a',label:'前面カメラ'},{deviceId:'b',label:'背面カメラ'}]"), "背面カメラ")
r.check("外側と分かる名前が無ければ、内側でないものを選ぶ",
        choose("[{deviceId:'a',label:'HD User Facing'},{deviceId:'b',label:'USB Camera'}]"), "USB Camera")
r.check("名前で分からなければ最後のものを選ぶ",
        choose("[{deviceId:'a',label:''},{deviceId:'b',label:''}]"), "")
r.check("前に選んだものがあれば、それを優先する",
        choose("[{deviceId:'a',label:'Front'},{deviceId:'b',label:'Rear'}]", "'a'"), "Front")
r.check("覚えているものが無くなっていたら、選び直す",
        choose("[{deviceId:'a',label:'Front'},{deviceId:'b',label:'Rear'}]", "'zzz'"), "Rear")
r.check("1つしか無ければ、それを使う",
        choose("[{deviceId:'a',label:'Front only'}]"), "Front only")
r.expect("カメラが無ければ null", b.ev("camChoose([], null)") is None, "null")

print("■ 内側／外側の見分け")
for label, back, front in [("Surface Camera Rear", True, False), ("Front Camera", False, True),
                           ("背面カメラ", True, False), ("前面カメラ", False, True),
                           ("USB Video Device", False, False),
                           ("Surface Camera Front", False, True),
                           ("Microsoft Camera Rear", True, False),
                           ("Surface Hub Camera", False, False)]:
    r.check(f"{label} → 外側", b.ev(f"camIsBack({label!r})"), back)
    r.check(f"{label} → 内側", b.ev(f"camIsFront({label!r})"), front)

print("■ 保存せずに閉じようとしたとき")
b.ev("Cam.open = window.__realOpen")     # 本物に戻す
b.ev("""window.__dir3 = fakeDir('夜桜_MD-7', {});
fsEnsureFolder = async () => window.__dir3;
window.__item3 = {variety:'夜桜', rank:'上物', quantityText:'2ペア', controlNo:'MD-7'};
'ok'""")
b.ev("(async()=>{ await Cam.open(window.__item3); })()"); time.sleep(0.5)
b.ev("Cam.addFiles([new File([new Blob(['q'])], 'q.jpg', {type:'image/jpeg'})]); 'ok'"); time.sleep(0.3)
r.check("手元に1枚", b.ev("Cam.pending.length"), 1)

# キャンセル → 閉じない、消えない
b.ev("window.confirm = () => false")
b.ev("(async()=>{ await Cam.close(); })()"); time.sleep(0.4)
r.expect("キャンセルなら閉じない",
         not b.ev("document.getElementById('camDialog').classList.contains('hidden')"), "開いたまま")
r.check("写真も消えない", b.ev("Cam.pending.length"), 1)

# OK → 保存してから閉じる
b.ev("window.confirm = () => true")
b.ev("(async()=>{ await Cam.close(); })()"); time.sleep(0.6)
r.expect("OKなら閉じる", b.ev("document.getElementById('camDialog').classList.contains('hidden')"), "hidden")
r.check("捨てずに保存されている", b.ev("Object.keys(window.__dir3._files).join(',')"), "MD-7_01.jpg")
r.check("手元は空", b.ev("Cam.pending.length"), 0)

b.close(); r.finish()
