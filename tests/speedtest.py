"""登録を押してからテプラに送るまでの、問い合わせ回数と時間を測る。"""
import time, os, glob
from common import Browser, Report

REQ = "/tmp/fake_tepra/requests.log"
def reqs():
    if not os.path.exists(REQ): return []
    return [l.strip() for l in open(REQ) if l.strip()]
def clear():
    for f in glob.glob("/tmp/fake_tepra/*"):
        try: os.unlink(f)
        except OSError: pass

b = Browser(9377, 1200, 1000); r = Report()
b.ev("localStorage.clear();switchTab('register')"); time.sleep(0.6)
b.ev("TepraLink._kind=null"); b.ev("TepraLink.probe()"); time.sleep(1.5)
b.ev("TepraWin.printerName=null; TepraWin.lastCandidates=[]; TepraWin.forgetMemo(); TepraWin._candAt=0")

print("■ 1枚目（何も分かっていない状態）")
clear()
t0 = time.time()
b.ev("TepraLink.print([{variety:'幹之',rank:'特上',quantityText:'2ペア',controlNo:'MD-1'}])")
t1 = time.time()
first = reqs()
print("   問い合わせ:", " / ".join(x.split()[1].replace("/api/printer","") or "一覧" for x in first))
r.expect("1枚目にかかった時間", True, f"{t1-t0:.2f}秒 ・ 問い合わせ {len(first)}回")

print("■ 2枚目（続けて押したとき）")
clear()
t0 = time.time()
b.ev("TepraLink.print([{variety:'夜桜',rank:'上物',quantityText:'1ペア',controlNo:'MD-2'}])")
t1 = time.time()
second = reqs()
print("   問い合わせ:", " / ".join(x.split()[1].replace("/api/printer","") or "一覧" for x in second))
r.expect("2枚目にかかった時間", True, f"{t1-t0:.2f}秒 ・ 問い合わせ {len(second)}回")
r.expect("2枚目は1枚目より問い合わせが少ない", len(second) < len(first),
         f"1枚目 {len(first)}回 → 2枚目 {len(second)}回")
r.check("2枚目は印刷1回だけで済む", len([x for x in second if "/print/" in x]), 1)

print("■ 画面を開いた時点で下ごしらえしておいた場合（ふだんの使い方）")
b.ev("TepraWin.printerName=null; TepraWin.lastCandidates=[]; TepraWin.forgetMemo(); TepraWin._candAt=0; tepraWarmed=0")
b.ev("warmUpTepra()"); time.sleep(4.0)      # 画面を開いてしばらく経った状態
clear()
t0 = time.time()
b.ev("TepraLink.print([{variety:'オロチ',rank:'通常',quantityText:'3ペア',controlNo:'MD-3'}])")
t1 = time.time()
warm = reqs()
print("   問い合わせ:", " / ".join(x.split()[1].replace("/api/printer","") or "一覧" for x in warm))
r.expect("押してから送るまでの時間", True, f"{t1-t0:.2f}秒 ・ 問い合わせ {len(warm)}回")
r.check("印刷1回だけで済む", len(warm), 1)

b.close(); r.finish()
