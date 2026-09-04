"""アプリの部品がそろっているかを機械的に調べる。
   書き換えの拍子に関数が消える事故を、次からはここで止める。"""
import time
from common import Browser, Report

b = Browser(9375, 1100, 900); r = Report()
b.ev("localStorage.clear()"); time.sleep(0.5)

def has(expr):
    return b.ev(f"typeof ({expr})")

print("■ 世の中に出ている関数")
FUNCS = [
  # 登録まわり
  "regMasters","regList","regIsGoods","regThingName","regAddBreed","regRemoveBreeds",
  "regResetBreeds","regAddSimple","regItems","saveRegItems","regUnprinted","regQuantityText",
  "regPreviewNumber","regDoRegister","renderRegisterPanel","renderRegSteps","renderRegStepBody",
  "renderRegItems","renderRegDone","fitLabelRows","labelLinesOf",
  # 用品
  "goodsOf","goodsPhotoKeys","goodsAddPhotos","goodsRemovePhoto","setGoodsNumber","ensureGoodsNumbers",
  # テプラ
  "tepraAutoOn","setTepraAuto","tepraMarginMM","setTepraMarginMM","tepraCutMode","setTepraCutMode",
  "tepraRows","setTepraRows","tepraMinLenRatio","setTepraMinLenRatio",
  "tepraFontScale","setTepraFontScale",
  "tepraPrintOne","tepraPrintPending","tepraPrintPickedGoods","tepraPrintOnRegister",
  "renderTepraBar","hasTepraBridge","hasInk","setPrintLog","getPrintLog",
  # 保存先フォルダ
  "fsFolderName","fsSafeName","fsRestoreRoot","fsChooseRoot","fsEnsureFolder","fsLoadAuto",
  "fsLoadFromFolders","fsLoadFromFoldersAndroid","renderFsBar","fsCreateMissingFoldersAuto",
  # 取込・フォルダ表示
  "renderFolders","shiftBoundary","syncFolderPhotos","pushGoodsPhotos","ensureThumb",
  "fsWorkDir","fsDoneDir","fsDiagnose","fsCleanNested","fsWhy","showFsStatus","fsFixRootChoice","fsArchiveAll","fsArchiveOne","fsWriteFile","autoLoadForEdit",
  "renderEditFolderBar","renderEditPanel",
  # 拡大・やり直し
  "openLightbox","closeLightbox","renderLightbox","applyLbSize","syncZoomBar","lbVisibleRect",
  "lbSaveCrop","redoOnePhoto","addRedoReason","redoTopReasons",
  # 出品
  "buildTitle","planImages","buildAuctownExport","validateForExport","buildTepraCsv","exportTepraCsv",
  # ホイール・かな
  "wheelHtml","bindWheel","kanaGroupOf","estimateReading","normKana","regRange",
  "regSteps","regConfirmStep","regQtyStep","regRankHtml","bindRegRank","regQtyHtml","bindRegQty",
  "bindGoodsFixed","warmUpTepra","sharpenToBlackWhite","tepraFontScale",
  "tepraPrintableDots","tepraPrintableMM","showPrintImage","setPrintImage",
  "refreshFsConnected","installApp","isInstalledApp",
]
missing = [f for f in FUNCS if has(f) != "function"]
r.expect(f"{len(FUNCS)}個の関数がすべてある", not missing, "無い: " + ", ".join(missing) if missing else "")

print("■ テプラの窓口（TepraLink）")
LINK = ["kind","available","probe","status","connect","android","print","_send"]
lm = [m for m in LINK if b.ev(f"typeof TepraLink.{m}") != "function"]
r.expect("必要な手続きがそろっている", not lm, "無い: " + ", ".join(lm) if lm else "")

print("■ Windowsの窓口（TepraWin）")
WIN = ["fetchJson","available","isOnline","isBluetoothName","candidates","pick","status",
       "makePng","print","printOnce"]
wm = [m for m in WIN if b.ev(f"typeof TepraWin.{m}") != "function"]
r.expect("必要な手続きがそろっている", not wm, "無い: " + ", ".join(wm) if wm else "")

print("■ 保存先の窓口（FsLink）")
FS = ["kind","available","androidCall","status","chooseRoot","ensureFolder","listPhotos",
      "readPhoto","takePhoto","addFromGallery"]
fm = [m for m in FS if b.ev(f"typeof FsLink.{m}") != "function"]
r.expect("必要な手続きがそろっている", not fm, "無い: " + ", ".join(fm) if fm else "")

print("■ 取込タブは廃止された")
r.expect("取込タブは無い", not b.ev("!!document.querySelector('[data-tab=import]')"), "")
r.expect("取込のパネルも無い", not b.ev("!!document.getElementById('panel-import')"), "")
tabs = b.ev("[...document.querySelectorAll('.tab')].map(x=>x.textContent.trim())")
r.expect("タブは 登録/編集/出品/履歴/設定 の5つ", len(tabs or []) == 5, " | ".join(tabs or []))

print("■ 画面の部品")
IDS = ["fsStatusDialog","btnEditFsStatus","btnEditFsStatus2","panel-register","regSteps","regStepBody","regItemList","regTepraBar","regFsBar",
       "regTepraPrint","regGoodsPrint","regTepraCsv","regToImport","folderList",
       "panel-edit","editEmpty","editLoaded","editFolderInfo","btnEditReload","btnEditReload2",
       "btnEditPickRoot","btnArchive","editFolders",
       "lightbox","lbZoomRange","lbSaveCrop","lbRedo","redoDialog",
       "btnPrintLog","btnPrintImage","btnSaveLocal","btnTapeFeed","btnTapeFeedCut","printImageDialog","toast"]
im = [i for i in IDS if not b.ev(f"!!document.getElementById('{i}')")]
r.expect(f"{len(IDS)}個の部品がすべてある", not im, "無い: " + ", ".join(im) if im else "")


print("■ ソースに定義そのものが残っているか（まとめ書き換えで消える事故を止める）")
import os, re
SRC = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "index.html"),
           encoding="utf-8").read()
# const で作った入れ物は評価用スクリプトから見えないので、文字として確かめる
DEFS = ["FsLink", "TepraLink", "TepraWin",
        "ensureGoodsNumbers", "setGoodsNumber", "goodsPhotoPut", "goodsPhotoGet",
        "goodsPhotoDelete", "goodsOf", "goodsPhotoKeys", "goodsAddPhotos", "goodsRemovePhoto",
        "shrinkImage", "sharpenToBlackWhite", "hasTepraBridge", "hasInk", "labelLinesOf",
        "fsLoadFromFolders", "fsLoadFromFoldersAndroid", "fsArchiveOne", "fsArchiveAll",
        "fsDiagnose", "fsCleanNested", "showFsStatus", "fsParseFolderName", "fsWhy"]
lost = [d for d in DEFS
        if not re.search(r"^(?:async )?function " + d + r"\b|^(?:const|let|var) " + d + r"\s*=", SRC, re.M)]
r.expect(f"{len(DEFS)}個の定義がすべて残っている", not lost, ("消えている: " + ", ".join(lost)) if lost else "")

# 呼んでいるのに定義が無い、を見つける
called = set(re.findall(r"\b([A-Z][A-Za-z]+)\.[a-z]", SRC))
known = {"Object","Array","Math","JSON","String","Number","Promise","Date","Boolean","Image",
         "Map","Set","URL","Intl","RegExp","Blob","File","Error","TypeError","Uint8Array",
         "Uint8ClampedArray","Int32Array","Float32Array","ArrayBuffer","DataView","CSS",
         "FileReader","XMLHttpRequest","FormData","Notification","OffscreenCanvas","TextEncoder",
         "TextDecoder","WeakMap","WeakSet","Symbol","BigInt","Response","Request","Headers"}
undef = [c for c in sorted(called - known)
         if not re.search(r"^(?:const|let|var|function|class) " + c + r"\b", SRC, re.M)
         and ("window." + c) not in SRC]
r.expect("使っているのに定義が無い入れ物は無い", not undef, ("見当たらない: " + ", ".join(undef)) if undef else "")


print("■ 版がそろっているか（古い画面を掴んだままにしない）")
SW = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "service-worker.js"),
          encoding="utf-8").read()
app_v = (re.search(r"const APP_VERSION = '(v\d+)'", SRC) or [None, None])[1]
sw_v  = (re.search(r"medaka-cache-(v\d+)", SW) or [None, None])[1]
r.check("index.html と service-worker.js の版が同じ", app_v, sw_v)
r.expect("画面に出す版も同じ", app_v and f'<span id="appVersion">{app_v}</span>' in SRC,
         f"ボタンの表示 = {app_v}")
r.expect("更新ボタンがある", b.ev("!!document.getElementById('btnUpdateApp')"), "🔄 ボタン")
r.expect("押すと覚えている中身を捨てる", "caches.delete" in SRC, "caches.delete")
r.expect("押すと古い仕掛けを外す", "unregister()" in SRC, "unregister")
r.expect("押すと毎回ちがうURLで開き直す",
         "searchParams.set('v'" in SRC and "location.replace" in SRC, "?v=時刻 で開き直す")
r.expect("書体の読み込みで画面を待たせない", "media=\"print\" onload" in SRC, "非同期で読む")
r.expect("書体が届く前も日本語が出る", "Hiragino Sans" in SRC and "Yu Gothic UI" in SRC,
         "端末の書体を控えにする")
r.expect("自動で新しい版に入れ替わる仕掛けがある",
         "controllerchange" in SRC and "SKIP_WAITING" in SRC, "controllerchange + SKIP_WAITING")
r.expect("HTMLはHTTPキャッシュを通さず取り直す", "cache: 'reload'" in SW, "service-worker.js")
r.expect("押して最新にできる", "updateApp" in SRC, "版の表示を押すと更新")

print("■ 起動して例外が出ていないか")
r.check("登録タブが描かれている（品種/ランク/数量/確認）", b.ev("document.querySelectorAll('#regSteps .reg-step').length"), 4)
nBreeds = b.ev("document.querySelectorAll('#regBreedList button').length") or 0
r.expect("品種が並んでいる", nBreeds > 0, str(nBreeds) + "件")

print("■ 印刷の入口が、どんな時も結果を返す")
b.ev("window.TepraBridge=undefined; TepraLink._kind='none'")
for arg in ["[]", "null", "[{}]", "[{variety:'幹之',rank:'',quantityText:'',controlNo:''}]"]:
    res = b.ev(f"TepraLink.print({arg})")
    r.expect(f"print({arg}) が結果を返す", isinstance(res, dict) and 'ok' in res, str(res)[:80])

b.close(); r.finish()
