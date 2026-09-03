"""USB優先の接続と、失敗時のBluetoothへの切り替えを検証する。"""
import time, os, json, glob
from common import Browser, Report

for f in ["/tmp/fake_tepra_usb_gone", "/tmp/fake_tepra_usb_fail"]:
    if os.path.exists(f): os.unlink(f)

b = Browser(9370, 1200, 1200); r = Report()
b.ev("localStorage.clear();switchTab('register')"); time.sleep(0.6)
b.ev("TepraLink._kind=null; renderRegisterPanel()"); time.sleep(2.0)

print("■ USBを優先して選ぶ")
r.check("経路はWindows", b.ev("TepraLink.kind()"), "windows")
cands = b.ev("TepraWin.candidates()")
r.check("2台見えている", len(cands or []), 2)
r.expect("USB側が先", (cands or [""])[0] == "KING JIM SR-R5600P", str(cands))
r.expect("Bluetoothは後ろ", (cands or ["",""])[1].upper().endswith("BT"), str(cands))
b.ev("TepraWin.printerName=null; TepraWin.pick()"); time.sleep(1.5)
r.check("選ばれるのはUSB側", b.ev("TepraWin.printerName"), "KING JIM SR-R5600P")

print("■ USBがオフラインなら、つながっているBluetoothを選ぶ")
import os as _os
open("/tmp/fake_tepra_usb_offline","w").close()
b.ev("TepraWin.printerName=null; TepraWin.lastCandidates=[]; TepraWin._candAt=0; TepraWin.forgetMemo(); TepraWin.pick(true)"); time.sleep(1.5)
r.expect("Bluetoothが選ばれる", (b.ev("TepraWin.printerName") or "").upper().endswith("BT"),
         b.ev("TepraWin.printerName"))
st = b.ev("TepraWin.status()")
r.check("どちらに繋がっているか分かる", st.get("route"), "Bluetooth")
_os.unlink("/tmp/fake_tepra_usb_offline")
b.ev("TepraWin.printerName=null; TepraWin.lastCandidates=[]; TepraWin._candAt=0; TepraWin.forgetMemo(); TepraWin.pick(true)"); time.sleep(1.5)
r.check("USBが戻ればUSBを使う", b.ev("TepraWin.printerName"), "KING JIM SR-R5600P")
st = b.ev("TepraWin.status()")
r.check("USBと表示される", st.get("route"), "USB")

print("■ USBが印刷に失敗したらBluetoothへ切り替える")
open("/tmp/fake_tepra_usb_fail", "w").close()
for f in glob.glob("/tmp/fake_tepra/*"): os.unlink(f)
res = b.ev("""TepraWin.print([{lines:['幹之','特上 2ペア','MD-1']}])""")
time.sleep(1.0)
r.check("印刷は成功する", res.get("ok"), True)
r.expect("Bluetooth側に切り替わったと分かる", (res.get("switched") or "").upper().endswith("BT"), str(res.get("switched")))
r.check("使うプリンターも切り替わる", (b.ev("TepraWin.printerName") or "").upper().endswith("BT"), True)
r.check("実際に1枚届いている", len(glob.glob("/tmp/fake_tepra/*.png")), 1)
os.unlink("/tmp/fake_tepra_usb_fail")

print("■ USBが抜けたらBluetoothだけを使う")
open("/tmp/fake_tepra_usb_gone", "w").close()
b.ev("TepraWin.printerName=null; TepraWin.lastCandidates=[]; TepraWin._candAt=0; TepraWin.forgetMemo(); TepraWin.pick(true)"); time.sleep(1.5)
r.expect("Bluetoothだけが残る", (b.ev("TepraWin.printerName") or "").upper().endswith("BT"), b.ev("TepraWin.printerName"))
os.unlink("/tmp/fake_tepra_usb_gone")

print("■ 画像が作れないときは切り替えない（接続の問題ではない）")
for f in glob.glob("/tmp/fake_tepra/*"): os.unlink(f)
res = b.ev("TepraWin.print([{lines:[]}])")
r.check("断る", res.get("ok"), False)
r.check("印刷は起きない", len(glob.glob("/tmp/fake_tepra/*.png")), 0)

print("■ 余白が二重にかからない")
b.ev("setTepraMarginMM(0)"); time.sleep(0.3)
w0 = b.ev("""(async()=>{ const b64=TepraWin.makePng(['幹之','特上 2ペア','MD-1'],128);
  const bin=atob(b64); const buf=new Uint8Array(bin.length);
  for(let i=0;i<bin.length;i++) buf[i]=bin.charCodeAt(i);
  const bmp=await createImageBitmap(new Blob([buf],{type:'image/png'})); return bmp.width; })()""")
b.ev("setTepraMarginMM(15)"); time.sleep(0.3)
w15 = b.ev("""(async()=>{ const b64=TepraWin.makePng(['幹之','特上 2ペア','MD-1'],128);
  const bin=atob(b64); const buf=new Uint8Array(bin.length);
  for(let i=0;i<bin.length;i++) buf[i]=bin.charCodeAt(i);
  const bmp=await createImageBitmap(new Blob([buf],{type:'image/png'})); return bmp.width; })()""")
r.check("画像の幅は余白で変わらない", w0, w15)
for f in glob.glob("/tmp/fake_tepra/*"): os.unlink(f)
b.ev("TepraWin.printerName=null; TepraWin.print([{lines:['幹之','特上','MD-1']}])"); time.sleep(1.5)
params = json.load(open(sorted(glob.glob("/tmp/fake_tepra/*_param.json"))[0]))
r.check("余白は本体側にだけ、0.1mm単位で渡す（15mm→150）", params["marginLeftRight"], 150)

print("■ テープの切り方を選べる")
r.check("既定はラベルごと", b.ev("tepraCutMode()"), 2)
b.ev("setTepraCutMode(3)"); time.sleep(0.4)
for f in glob.glob("/tmp/fake_tepra/*"): os.unlink(f)
b.ev("TepraWin.print([{lines:['夜桜','上物','MD-2']}])"); time.sleep(1.5)
params = json.load(open(sorted(glob.glob("/tmp/fake_tepra/*_param.json"))[0]))
r.check("最後に1回で送られる", params["tapeCut"], 3)
r.expect("画面にも切り方が出る", b.ev("!!document.getElementById('tepraCut')"), "")

b.close(); r.finish()
