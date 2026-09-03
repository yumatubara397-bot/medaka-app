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
  "renderFolders","shiftBoundary","syncFolderPhotos","assignPhotosToRegistered","refreshAssignBar",
  "pushGoodsPhotos","ensureThumb",
  # 拡大・やり直し
  "openLightbox","closeLightbox","renderLightbox","applyLbSize","syncZoomBar","lbVisibleRect",
  "lbSaveCrop","redoOnePhoto","addRedoReason","redoTopReasons",
  # 出品
  "buildTitle","planImages","buildAuctownExport","validateForExport","buildTepraCsv","exportTepraCsv",
  # ホイール・かな
  "wheelHtml","bindWheel","kanaGroupOf","estimateReading","normKana","regRange",
  "regSteps","regConfirmStep","regQtyStep","regRankHtml","bindRegRank","regQtyHtml","bindRegQty",
  "bindGoodsFixed","warmUpTepra",
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

print("■ 画面の部品")
IDS = ["panel-register","regSteps","regStepBody","regItemList","regTepraBar","regFsBar",
       "regTepraPrint","regGoodsPrint","regTepraCsv","regToImport","folderList","assignBar",
       "assignPerItem","lightbox","lbZoomRange","lbSaveCrop","lbRedo","redoDialog",
       "btnPrintLog","btnSaveLocal","toast","tepraFont","tepraRows","tepraLen","tepraCut","tepraMargin","tepraAuto"]
im = [i for i in IDS if not b.ev(f"!!document.getElementById('{i}')")]
r.expect(f"{len(IDS)}個の部品がすべてある", not im, "無い: " + ", ".join(im) if im else "")

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
