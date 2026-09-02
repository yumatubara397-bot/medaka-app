"""印刷前のテープ送り・カットを出していないこと、送る設定が仕様どおりかを確かめる。"""
import time, os, glob, json, urllib.request
from common import Browser, Report

for f in glob.glob("/tmp/fake_tepra/*"): os.unlink(f)
b = Browser(9376, 1200, 1000); r = Report()
b.ev("localStorage.clear();switchTab('register')"); time.sleep(0.6)
b.ev("TepraLink._kind=null"); b.ev("TepraLink.probe()"); time.sleep(1.5)
r.check("Windows経路", b.ev("TepraLink.kind()"), "windows")

print("■ 印刷したときに、テープ送りを呼んでいないか")
res = b.ev("TepraLink.print([{variety:'幹之',rank:'特上',quantityText:'2ペア',controlNo:'MD-1'}])")
time.sleep(1.0)
r.check("印刷は成功", res.get("ok"), True)
r.expect("テープ送りは1度も呼んでいない", not os.path.exists("/tmp/fake_tepra/tapefeed.log"),
         "tapefeed の記録なし")
r.check("送ったのは印刷1回だけ", len(glob.glob("/tmp/fake_tepra/*.png")), 1)

print("■ 送っている設定（仕様書どおりか）")
params = json.load(open(sorted(glob.glob("/tmp/fake_tepra/*_param.json"))[0]))
r.check("カット設定はこちらを優先（2）", params["priorityCutSetting"], 2)
r.check("印刷後のカットはラベルごと（2）", params["tapeCut"], 2)
r.check("ハーフカットはしない（1）", params["halfCut"], 1)
b.ev("setTepraMarginMM(3)"); time.sleep(0.4)
for f in glob.glob("/tmp/fake_tepra/*"): os.unlink(f)
b.ev("TepraLink.print([{variety:'幹之',rank:'特上',quantityText:'2ペア',controlNo:'MD-2'}])"); time.sleep(1.2)
params = json.load(open(sorted(glob.glob("/tmp/fake_tepra/*_param.json"))[0]))
r.check("左右余白は0.1mm単位で送る（3mm→30）", params["marginLeftRight"], 30)
b.ev("setTepraMarginMM(0)"); time.sleep(0.4)
for f in glob.glob("/tmp/fake_tepra/*"): os.unlink(f)
b.ev("TepraLink.print([{variety:'幹之',rank:'特上',quantityText:'2ペア',controlNo:'MD-3'}])"); time.sleep(1.2)
params = json.load(open(sorted(glob.glob("/tmp/fake_tepra/*_param.json"))[0]))
r.check("0mmなら0（余白を指定しない）", params["marginLeftRight"], 0)

print("■ 接続の確認でテープを動かしていないか")
for f in glob.glob("/tmp/fake_tepra/*"): os.unlink(f)
b.ev("TepraWin.printerName=null; TepraWin.lastCandidates=[]")
b.ev("TepraLink.connect()"); time.sleep(1.5)
b.ev("TepraLink.status()"); time.sleep(0.8)
b.ev("TepraWin.candidates()"); time.sleep(1.0)
r.expect("接続確認ではテープ送りを呼ばない", not os.path.exists("/tmp/fake_tepra/tapefeed.log"), "")
r.check("接続確認では印刷もしない", len(glob.glob("/tmp/fake_tepra/*.png")), 0)

print("■ 手動のテープ送りだけが呼べる")
res = b.ev("TepraWin.tapeFeed(false)"); time.sleep(1.0)
r.check("送りは成功", res.get("ok"), True)
r.expect("cutflag=false で呼ばれる", "cutflag=false" in open("/tmp/fake_tepra/tapefeed.log").read(),
         open("/tmp/fake_tepra/tapefeed.log").read().strip())
res = b.ev("TepraWin.tapeFeed(true)"); time.sleep(1.0)
r.expect("送り＋カットは cutflag=true", "cutflag=true" in open("/tmp/fake_tepra/tapefeed.log").read(), "")
r.check("手動でも印刷は起きない", len(glob.glob("/tmp/fake_tepra/*.png")), 0)
r.expect("画面にボタンがある",
         b.ev("!!document.getElementById('btnTapeFeed') && !!document.getElementById('btnTapeFeedCut')"), "")

print("■ 連続3枚：余計なカットが増えない")
for f in glob.glob("/tmp/fake_tepra/*"): os.unlink(f)
b.ev("""TepraLink.print([
  {variety:'幹之',rank:'特上',quantityText:'1ペア',controlNo:'MD-A'},
  {variety:'夜桜',rank:'上物',quantityText:'2ペア',controlNo:'MD-B'},
  {variety:'オロチ',rank:'通常',quantityText:'3ペア',controlNo:'MD-C'}])""")
time.sleep(2.5)
r.check("3枚届く", len(glob.glob("/tmp/fake_tepra/*.png")), 3)
r.expect("テープ送りは呼ばない", not os.path.exists("/tmp/fake_tepra/tapefeed.log"), "")
b.ev("setTepraCutMode(3)"); time.sleep(0.4)
for f in glob.glob("/tmp/fake_tepra/*"): os.unlink(f)
b.ev("""TepraLink.print([
  {variety:'幹之',rank:'特上',quantityText:'1ペア',controlNo:'MD-A'},
  {variety:'夜桜',rank:'上物',quantityText:'2ペア',controlNo:'MD-B'}])""")
time.sleep(2.0)
ps = [json.load(open(f)) for f in sorted(glob.glob("/tmp/fake_tepra/*_param.json"))]
r.expect("「最後に1回」を選べば全部3で送る", all(x["tapeCut"] == 3 for x in ps), str([x["tapeCut"] for x in ps]))

print("■ 記録に前後のカットが残る")
b.ev("tepraPrintOne({variety:'幹之',rank:'特上',quantityText:'1ペア',controlNo:'MD-Z'})"); time.sleep(1.5)
log = b.ev("getPrintLog()") or {}
r.expect("印刷前のテープ送り＝なし", "なし" in log.get("印刷前のテープ送り",""), log.get("印刷前のテープ送り"))
r.expect("印刷前のカット＝なし", "なし" in log.get("印刷前のカット",""), log.get("印刷前のカット"))
r.expect("印刷後のカットが分かる", bool(log.get("印刷後のカット")), log.get("印刷後のカット"))
r.expect("カット設定の優先が分かる", "priorityCutSetting=2" in log.get("カット設定の優先",""), log.get("カット設定の優先"))

b.close(); r.finish()
