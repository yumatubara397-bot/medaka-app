import time, base64, io
from common import Browser
from PIL import Image
b = Browser(9371, 1200, 900)
b.ev("localStorage.clear()"); time.sleep(0.5)
lines = ["忘却の翼", "通常 雄5 雌8", "MD-260902-004"]
imgs = []
for rows, ratio, label in [(3,3.5,"3行 長め"),(2,3.5,"2行 長め"),(2,4.5,"2行 もっと長く")]:
    b.ev(f"setTepraRows({rows}); setTepraMinLenRatio({ratio})"); time.sleep(0.3)
    b64 = b.ev(f"TepraWin.makePng(fitLabelRows({lines!r}), 128)")
    im = Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")
    print(f"{label}: {im.width}×{im.height} px  ≒ 幅 {im.width/180*25.4:.0f}mm")
    imgs.append((label, im))
# 実物大に近い比率で並べる（3倍に拡大して見やすく）
W = max(i.width for _, i in imgs) * 3
H = sum(i.height * 3 + 30 for _, i in imgs)
out = Image.new("RGB", (W, H), "#888")
y = 0
for label, im in imgs:
    big = im.resize((im.width*3, im.height*3), Image.NEAREST)
    out.paste(big, (0, y)); y += big.height + 30
out.save("/tmp/label_preview.png")
print("保存: /tmp/label_preview.png")
b.close()
