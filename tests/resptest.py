"""通信モジュールの返事が想定外でも、印刷が失敗扱いにならないことを確かめる。"""
import time, os, glob
from common import Browser, Report

for f in glob.glob("/tmp/fake_tepra_resp_*"): os.unlink(f)
b = Browser(9373, 1200, 1000); r = Report()
b.ev("localStorage.clear();switchTab('register')"); time.sleep(0.6)
b.ev("TepraLink._kind=null"); b.ev("TepraLink.probe()"); time.sleep(1.5)
r.check("Windows経路", b.ev("TepraLink.kind()"), "windows")
LAB = "[{variety:'幹之',rank:'特上',quantityText:'2ペア',controlNo:'MD-1'}]"

print("■ ふつうの返事（JSON）")
for f in glob.glob("/tmp/fake_tepra/*"): os.unlink(f)
res = b.ev(f"TepraLink.print({LAB})"); time.sleep(0.5)
r.check("成功", res.get("ok"), True)
r.check("画像が届く", len(glob.glob("/tmp/fake_tepra/*.png")), 1)

print("■ 本文なしで返ってくる場合")
open("/tmp/fake_tepra_resp_empty","w").close()
for f in glob.glob("/tmp/fake_tepra/*"): os.unlink(f)
res = b.ev(f"TepraLink.print({LAB})"); time.sleep(0.5)
r.check("失敗にしない", res.get("ok"), True)
r.check("画像は届いている", len(glob.glob("/tmp/fake_tepra/*.png")), 1)
os.unlink("/tmp/fake_tepra_resp_empty")

print("■ JSONでない返事の場合")
open("/tmp/fake_tepra_resp_plain","w").close()
for f in glob.glob("/tmp/fake_tepra/*"): os.unlink(f)
res = b.ev(f"TepraLink.print({LAB})"); time.sleep(0.5)
r.check("失敗にしない", res.get("ok"), True)
r.check("画像は届いている", len(glob.glob("/tmp/fake_tepra/*.png")), 1)
os.unlink("/tmp/fake_tepra_resp_plain")

print("■ モジュールが止まっている場合")
import subprocess
subprocess.run(["pkill","-f","fake_webapi.py"], capture_output=True); time.sleep(1.5)
b.ev("TepraWin.printerName=null; TepraWin.lastCandidates=[]")
res = b.ev(f"TepraLink.print({LAB})"); time.sleep(1.0)
r.check("失敗として返る", res.get("ok"), False)
r.expect("理由が具体的", bool(res.get("error")) and "エラーが起きました" not in (res.get("error") or ""),
         res.get("error"))
r.expect("例外にならない（必ず結果が返る）", isinstance(res, dict), type(res).__name__)

print("■ 記録が残る")
b.ev(f"tepraPrintOne({{variety:'幹之',rank:'特上',quantityText:'2ペア',controlNo:'MD-1'}})"); time.sleep(1.5)
log = b.ev("getPrintLog()")
r.expect("経路・プリンター・内容・設定・結果が残る",
         all(k in (log or {}) for k in ["経路","プリンター","内容","設定","結果"]), str(log)[:150])
r.expect("失敗の理由も残る", "失敗" in (log or {}).get("結果",""), (log or {}).get("結果","")[:80])

b.close(); r.finish()
