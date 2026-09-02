"""ラベルの文字が実際に何ミリで印刷されるかを測る。"""
import time, base64, io
from common import Browser
from PIL import Image

def ink_bands(im):
    """黒い部分が縦にどこからどこまであるかを行ごとにまとめる"""
    g = im.convert("L")
    w, h = g.size
    px = g.load()
    rows = []
    for y in range(h):
        dark = sum(1 for x in range(0, w, 2) if px[x, y] < 128)
        rows.append(dark > 0)
    bands, start = [], None
    for y, on in enumerate(rows):
        if on and start is None: start = y
        if not on and start is not None:
            bands.append((start, y - 1)); start = None
    if start is not None: bands.append((start, h - 1))
    return [(a, b, b - a + 1) for a, b, _ in [(a, b, 0) for a, b in bands]]

b = Browser(9372, 1200, 900)
b.ev("localStorage.clear()"); time.sleep(0.5)
lines = ["忘却の翼", "通常 雄5 雌8", "MD-260902-004"]

for rows in (3, 2):
    b.ev(f"setTepraRows({rows}); setTepraMinLenRatio(3.5)"); time.sleep(0.3)
    b64 = b.ev(f"TepraWin.makePng(fitLabelRows({lines!r}), 128)")
    im = Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")
    bands = ink_bands(im)
    print(f"■ {rows}行  画像 {im.width}×{im.height}px（幅 {im.width/180*25.4:.0f}mm）")
    for i, (a, bb, hgt) in enumerate(bands, 1):
        print(f"   {i}行目の文字の高さ … {hgt:>3}ドット ＝ {hgt/180*25.4:.1f}mm")
b.close()
