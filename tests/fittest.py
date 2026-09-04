"""文字が上下で切れていないかを、画素の位置で確かめる。"""
import time, base64, io
from common import Browser, Report
from PIL import Image

b = Browser(9386, 1000, 800); r = Report()
b.ev("localStorage.clear(); setTepraFontScale(0.86)"); time.sleep(0.5)

def check(lines, rows, name):
    b.ev(f"setTepraRows({rows})")
    im = Image.open(io.BytesIO(base64.b64decode(b.ev(f"TepraWin.makePng(fitLabelRows({lines!r}),128)")))).convert("L")
    px = im.load(); w,h = im.size
    dark_rows = [y for y in range(h) if any(px[x,y] < 128 for x in range(w))]
    top, bot = (min(dark_rows), max(dark_rows)) if dark_rows else (None, None)
    print(f"   {name}: 文字がある範囲 {top}〜{bot} 行（画像の高さ {h}）")
    r.expect(f"{name}：上が切れていない", top is not None and top >= 1, f"いちばん上の文字 = {top}行目")
    r.expect(f"{name}：下が切れていない", bot is not None and bot <= h - 2, f"いちばん下の文字 = {bot}行目（端は {h-1}）")
    # 左右
    dark_cols = [x for x in range(w) if any(px[x,y] < 128 for y in range(h))]
    r.expect(f"{name}：左右も切れていない", dark_cols and dark_cols[0] >= 1 and dark_cols[-1] <= w-2,
             f"{dark_cols[0]}〜{dark_cols[-1]} 列（幅 {w}）")

print("■ 3行のとき")
check(["忘却の翼","通常 雄5 雌8","MD-260902-004"], 3, "ふつうの3行")
print("■ 背の高い文字（ぎ・ぱ・ヴ・漢字）")
check(["ぎょぱヴ髙","通常 雄5 雌8","MD-260902-004"], 3, "背の高い文字")
print("■ 2行のとき")
check(["忘却の翼","通常 雄5 雌8  MD-260902-004"], 2, "2行")
print("■ 長い名前")
check(["めだかの黒発泡スチロール","特上 10ペア","MD-260902-999"], 3, "長い名前")

b.close(); r.finish()
