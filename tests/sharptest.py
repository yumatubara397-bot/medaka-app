"""ラベル画像がにじまないこと（白と黒だけ）と、文字の大きさ設定が効くことを確かめる。"""
import time, base64, io, glob, os, json
from common import Browser, Report
from PIL import Image

def load(b64):
    return Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")
def gray_ratio(im):
    """白でも黒でもない画素の割合"""
    n = mid = 0
    for r, g, bl in im.getdata():
        n += 1
        v = (r*299 + g*587 + bl*114)//1000
        if 30 < v < 225: mid += 1
    return mid / max(1, n)
def bands(im):
    g = im.convert("L"); w,h = g.size; px = g.load()
    rows = [any(px[x,y] < 128 for x in range(0,w,2)) for y in range(h)]
    out, st = [], None
    for y,on in enumerate(rows):
        if on and st is None: st = y
        if not on and st is not None: out.append(y-st); st = None
    if st is not None: out.append(h-st)
    return out

b = Browser(9380, 1100, 900); r = Report()
b.ev("localStorage.clear()"); time.sleep(0.5)
L = ["忘却の翼", "通常 雄5 雌8", "MD-260902-004"]

print("■ にじみ（灰色）が残っていないか")
b.ev("setTepraFontScale(0.86)"); time.sleep(0.3)
im = load(b.ev(f"TepraWin.makePng({L!r},128)"))
gr = gray_ratio(im)
r.expect("白と黒だけでできている", gr == 0, f"中間色の画素 {gr*100:.2f}%")
cols = set(im.getdata())
r.expect("使われている色は2つだけ", len(cols) <= 2, str(sorted(cols)))

print("■ 文字の大きさの設定が効く")
sizes = {}
for v, name in [(0.74,"小さめ"),(0.86,"ふつう"),(0.98,"大きめ")]:
    b.ev(f"setTepraFontScale({v})"); time.sleep(0.3)
    hs = bands(load(b.ev(f"TepraWin.makePng({L!r},128)")))
    sizes[name] = hs
    print(f"   {name}: 1行目 {hs[0]}ドット = {hs[0]/180*25.4:.1f}mm")
r.expect("小さめ < ふつう < 大きめ",
         sizes["小さめ"][0] < sizes["ふつう"][0] < sizes["大きめ"][0],
         f"{sizes['小さめ'][0]} < {sizes['ふつう'][0]} < {sizes['大きめ'][0]} ドット")
r.expect("小さめは大きめより2割以上小さい",
         sizes["小さめ"][0] <= sizes["大きめ"][0] * 0.8,
         f"{sizes['小さめ'][0]} / {sizes['大きめ'][0]}")

print("■ 本体側で拡大縮小させていないか")
b.ev("TepraLink._kind=null"); b.ev("TepraLink.probe()"); time.sleep(1.5)
for f in glob.glob("/tmp/fake_tepra/*"):
    try: os.unlink(f)
    except OSError: pass
b.ev("TepraLink.print([{variety:'幹之',rank:'特上',quantityText:'2ペア',controlNo:'MD-1'}])"); time.sleep(1.5)
params = json.load(open(sorted(glob.glob("/tmp/fake_tepra/*_param.json"))[0]))
r.check("拡大縮小はしない（0）", params["stretchImage"], 0)

print("■ 送った画像そのものも白黒だけか")
png = sorted(glob.glob("/tmp/fake_tepra/*.png"))[0]
sent = Image.open(png).convert("RGB")
r.expect("送った画像に灰色がない", gray_ratio(sent) == 0, f"中間色 {gray_ratio(sent)*100:.2f}%")
r.check("高さはテープの印字ドット数", sent.height, 128)

print("■ 文字の大きさをAndroidにも渡している")
b.ev("""window.__sent=[]; window.TepraBridge={
  status(){return JSON.stringify({ok:true,connected:true,printer:'X',tapeMM:24});},
  connect(){return JSON.stringify({ok:true,connected:true});},
  printWithMargin(j,m){window.__sent.push(JSON.parse(j)); return JSON.stringify({ok:true,printed:1});} };
TepraLink._kind='android'; setTepraFontScale(0.74);""")
time.sleep(0.4)
b.ev("TepraLink.print([{variety:'幹之',rank:'特上',quantityText:'2ペア',controlNo:'MD-2'}])"); time.sleep(1.0)
r.check("文字の大きさが一緒に渡る", b.ev("window.__sent[0][0].fontScale"), 0.74)

b.close(); r.finish()
