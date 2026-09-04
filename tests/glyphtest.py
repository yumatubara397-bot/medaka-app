"""小さい文字がつぶれていないか（字の中の空白が残っているか）を測る。"""
import time, base64, io
from common import Browser, Report
from PIL import Image

def load(b64): return Image.open(io.BytesIO(base64.b64decode(b64))).convert("L")

def holes(im):
    """黒に囲まれた白いかたまり（字の中の空白）の数を数える。
       つぶれるとこれが減る。"""
    w, h = im.size
    px = im.load()
    seen = [[False]*h for _ in range(w)]
    # 外側の白から塗りつぶす
    stack = [(x, y) for x in range(w) for y in (0, h-1) if px[x, y] > 128]
    stack += [(x, y) for y in range(h) for x in (0, w-1) if px[x, y] > 128]
    for x, y in stack: seen[x][y] = True
    while stack:
        x, y = stack.pop()
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = x+dx, y+dy
            if 0 <= nx < w and 0 <= ny < h and not seen[nx][ny] and px[nx, ny] > 128:
                seen[nx][ny] = True; stack.append((nx, ny))
    # 残った白＝字の中の空白
    cnt = 0
    for x in range(w):
        for y in range(h):
            if px[x, y] > 128 and not seen[x][y]:
                cnt += 1
                st = [(x, y)]; seen[x][y] = True
                while st:
                    a, bq = st.pop()
                    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                        na, nb = a+dx, bq+dy
                        if 0 <= na < w and 0 <= nb < h and not seen[na][nb] and px[na, nb] > 128:
                            seen[na][nb] = True; st.append((na, nb))
    return cnt

def bands(im):
    w,h = im.size; px = im.load()
    rows = [any(px[x,y] < 128 for x in range(0,w,2)) for y in range(h)]
    out, st = [], None
    for y,on in enumerate(rows):
        if on and st is None: st = y
        if not on and st is not None: out.append(y-st); st = None
    if st is not None: out.append(h-st)
    return out

b = Browser(9381, 1000, 800); r = Report()
b.ev("localStorage.clear(); setTepraFontScale(0.86); setTepraMinLenRatio(2.4)"); time.sleep(0.5)
L = ["忘却の翼", "通常 雄5 雌8", "MD-260902-004"]
im = load(b.ev(f"TepraWin.makePng({L!r},128)"))
hs = bands(im)
print(f"   文字の高さ: {hs} ドット（{[round(x/180*25.4,1) for x in hs]} mm）")
r.expect("商品名が大きすぎない", hs[0] <= 42, f"1行目 {hs[0]}ドット = {hs[0]/180*25.4:.1f}mm")
r.expect("下の行が読める大きさ", hs[-1] >= 24, f"最終行 {hs[-1]}ドット = {hs[-1]/180*25.4:.1f}mm")
r.expect("行ごとの差が小さくなった", hs[0] - hs[-1] <= 16, f"{hs[0]} と {hs[-1]} の差 {hs[0]-hs[-1]}")

n = holes(im)
print(f"   字の中の空白: {n}個")
r.expect("字がつぶれていない（中の空白が残っている）", n >= 8, f"{n}個")

r.expect("白と黒だけ", len(set(im.getdata())) <= 2, str(sorted(set(im.getdata()))))

print("■ 小さめにしてもつぶれない")
b.ev("setTepraFontScale(0.74)"); time.sleep(0.3)
im2 = load(b.ev(f"TepraWin.makePng({L!r},128)"))
hs2 = bands(im2); n2 = holes(im2)
print(f"   小さめ: 文字の高さ {hs2} / 字の中の空白 {n2}個")
r.expect("小さめでもつぶれない", n2 >= 6, f"{n2}個")
r.expect("小さめは実際に小さい", hs2[0] < hs[0], f"{hs2[0]} < {hs[0]}")

b.close(); r.finish()
