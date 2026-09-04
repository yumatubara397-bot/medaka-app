"""プリンターの実解像度に合わせて印刷データを作っているかを確かめる。"""
import time, base64, io, glob, os, json
from common import Browser, Report
from PIL import Image

b = Browser(9385, 1100, 900); r = Report()
b.ev("localStorage.clear()"); time.sleep(0.5)
b.ev("TepraLink._kind=null"); b.ev("TepraLink.probe()"); time.sleep(1.5)

print("■ 印字できる高さの計算（SDK付属の印字領域表どおりか）")
for mm, dots180 in [(24,128),(18,108),(12,72),(9,54),(6,36),(4,22)]:
    got = b.ev(f"tepraPrintableDots({mm}, 180)")
    r.check(f"{mm}mmテープ・180dpi", got, dots180)
r.check("24mmテープ・360dpiなら倍", b.ev("tepraPrintableDots(24, 360)"), 256)
mmv = b.ev("tepraPrintableMM(24)")
r.expect("24mmテープの印字できる高さ", abs(mmv - 18.06) < 0.1, f"{mmv:.2f} mm")

print("■ プリンターの解像度を読み取る")
st = b.ev("TepraLink.status()")
r.check("解像度を取得している", st.get("dpi"), 180)

print("■ 180dpi のとき")
for f in glob.glob("/tmp/fake_tepra/*"):
    try: os.unlink(f)
    except OSError: pass
b.ev("TepraLink.print([{variety:'忘却の翼',rank:'通常',quantityText:'雄5 雌8',controlNo:'MD-1'}])")
time.sleep(1.5)
im = Image.open(sorted(glob.glob("/tmp/fake_tepra/*.png"))[0])
r.check("画像の高さ＝128ドット", im.height, 128)
print(f"   画像 {im.width}×{im.height}px ＝ {im.width/180*25.4:.1f}×{im.height/180*25.4:.1f}mm")

print("■ もし本体が 360dpi だったら（実解像度に追随するか）")
b.ev("TepraWin.dpi=360; TepraWin.forgetMemo(); TepraWin._memo={at:Date.now(),printer:TepraWin.printerName,tapeMM:24,route:'USB',dpi:360}")
time.sleep(0.3)
for f in glob.glob("/tmp/fake_tepra/*"):
    try: os.unlink(f)
    except OSError: pass
b.ev("TepraLink.print([{variety:'忘却の翼',rank:'通常',quantityText:'雄5 雌8',controlNo:'MD-2'}])")
time.sleep(1.5)
im2 = Image.open(sorted(glob.glob("/tmp/fake_tepra/*.png"))[0])
r.check("画像の高さも倍になる", im2.height, 256)
r.expect("横も約2倍になる", abs(im2.width / im.width - 2) < 0.15, f"{im.width}px → {im2.width}px")
print(f"   画像 {im2.width}×{im2.height}px ＝ {im2.width/360*25.4:.1f}×{im2.height/360*25.4:.1f}mm")

print("■ 送っている設定（拡大縮小していないか）")
params = json.load(open(sorted(glob.glob("/tmp/fake_tepra/*_param.json"))[0]))
r.check("本体側で拡大縮小しない", params["stretchImage"], 0)

print("■ 白黒にする境目")
b.ev("TepraWin.dpi=180; TepraWin.forgetMemo()")
b.ev("TepraWin.makePng(['あいうえお','0123456789','MD-1'],128)"); time.sleep(0.5)
info = b.ev("lastPrintImage")
r.check("境目は128（明るさの真ん中）", info.get("threshold"), 128)
r.expect("画像の大きさを控えている", info.get("h") == 128 and info.get("w") > 0,
         f"{info.get('w')}×{info.get('h')}px")
r.expect("文字の大きさも控えている", len(info.get("fontPx") or []) == 3, str(info.get("fontPx")))

print("■ 確認画面")
b.ev("switchTab('settings')"); time.sleep(0.5)
r.expect("「印刷データを見る」がある", b.ev("!!document.getElementById('btnPrintImage')"), "")
b.ev("showPrintImage(false)"); time.sleep(1.2)
txt = b.ev("document.getElementById('printImageDialog').textContent") or ""
r.expect("画像の大きさが出る", "px" in txt, txt.replace("\n"," ")[:80])
r.expect("解像度が出る", "dpi" in txt, "")
r.expect("拡大縮小しないと明記", "1画素＝1ドット" in txt, "")

b.close(); r.finish()
