#!/usr/bin/env python3
"""すべての動作確認を実行する。

テストごとに使うポートが違うので、まとめて同時に走らせられる。
ただし resptest / wintest は「通信モジュールが止まっているとき」を
確かめるために偽モジュールを止めるので、最後に1本ずつ実行する。

  python3 runall.py            すべて
  python3 runall.py --quick    よく壊れるところだけ（速い）
  python3 runall.py fstest camtest   名前を指定して実行
  python3 runall.py -j 4       同時に走らせる本数を変える
"""
import subprocess, sys, time, os, glob, pathlib
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).parent
FAKE = None

def start_fake():
    global FAKE
    stop_fake()
    for f in glob.glob("/tmp/fake_tepra_usb_*") + glob.glob("/tmp/fake_tepra_resp_*"):
        try: os.unlink(f)
        except OSError: pass
    FAKE = subprocess.Popen([sys.executable, str(HERE / "fake_webapi.py")],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # 立ち上がるまで待つ（決め打ちで待たない）
    for _ in range(100):
        try:
            import urllib.request
            urllib.request.urlopen("http://localhost:29108/api/printer/", timeout=1)
            return
        except Exception:
            time.sleep(0.05)

def stop_fake():
    subprocess.run(["pkill", "-f", "fake_webapi.py"], capture_output=True)

# 偽モジュールが要らないもの（同時に走らせられる）
PLAIN = ["registertest", "wheeltest", "foldertest", "fstest", "fsandroidtest",
         "exporttest", "redotest", "croptest", "tidytest", "goodstest",
         "goodsfixedtest", "autoprinttest", "goodsprinttest", "surfacetest",
         "labeltest", "blanktest", "glyphtest", "fittest", "nesttest",
         "readfoldertest", "camtest", "backuptest", "donetest", "flowtest2", "zoomtest", "flowtest", "phonetest"]
# 偽モジュールは使うが、その作業場は触らないもの（同時に走らせられる）
WITH_FAKE = ["structtest"]
# 偽モジュールの作業場 /tmp/fake_tepra/ を使うもの。
# 送った内容を確かめるために毎回そこを空にするので、同時に走らせると
# 互いのファイルを消し合ってしまう。1本ずつ実行する。
SOLO = ["sharptest", "dpitest", "cuttest", "speedtest", "usbtest", "resptest", "wintest"]

# 直したところをすぐ確かめたいときの短い組み合わせ
QUICK = ["structtest", "registertest", "camtest", "backuptest", "nesttest", "readfoldertest", "fstest"]

def run(name):
    start = time.time()
    p = subprocess.run([sys.executable, str(HERE / f"{name}.py")],
                       capture_output=True, text=True)
    if p.returncode != 0 and "件失敗" not in p.stdout:
        # ブラウザが立ち上がらなかった等。1度だけやり直す
        subprocess.run(["pkill", "-f", f"medaka_test_"], capture_output=True)
        p = subprocess.run([sys.executable, str(HERE / f"{name}.py")],
                           capture_output=True, text=True)
    lines = [l for l in p.stdout.strip().split("\n") if l.strip()]
    tail = lines[-1] if lines else "(出力なし)"
    return name, p.returncode == 0, tail, time.time() - start, p.stdout

def run_group(names, jobs):
    """まとめて走らせ、終わったものから結果を出す"""
    out = []
    if not names:
        return out
    with ThreadPoolExecutor(max_workers=min(jobs, len(names))) as pool:
        for res in pool.map(run, names):
            name, good, tail, sec, _ = res
            print(f"{name:<16} {tail}   ({sec:.0f}秒)")
            out.append(res)
    return out

def main():
    args = [a for a in sys.argv[1:]]
    jobs = 6
    if "-j" in args:
        i = args.index("-j"); jobs = int(args[i + 1]); del args[i:i + 2]

    if "--quick" in args:
        plain = [t for t in QUICK if t in PLAIN]
        fake  = [t for t in QUICK if t in WITH_FAKE]
        solo  = []
    elif args:
        plain = [t for t in args if t in PLAIN]
        fake  = [t for t in args if t in WITH_FAKE]
        solo  = [t for t in args if t in SOLO]
        unknown = [t for t in args if t not in PLAIN + WITH_FAKE + SOLO]
        if unknown:
            print("知らないテスト:", ", ".join(unknown)); sys.exit(2)
    else:
        plain, fake, solo = PLAIN, WITH_FAKE, SOLO

    t0 = time.time()
    subprocess.run(["pkill", "-f", "remote-debugging-port"], capture_output=True)
    results = []

    if plain:
        print(f"■ 偽モジュール不要のもの（同時に{min(jobs, len(plain))}本）")
        results += run_group(plain, jobs)

    if fake:
        print(f"\n■ 偽の通信モジュールを使うもの（同時に{min(jobs, len(fake))}本）")
        start_fake()
        results += run_group(fake, jobs)

    if solo:
        print("\n■ 送った内容を確かめるもの（1本ずつ）")
        for t in solo:
            start_fake()
            results += run_group([t], 1)
    stop_fake()

    ng = [r for r in results if not r[1]]
    print()
    for name, good, tail, sec, out in ng:
        print(f"── {name} の失敗したところ " + "─" * 30)
        for line in out.split("\n"):
            if "❌" in line:
                print("  " + line.strip())
    if ng:
        print()
    print(f"{'✅ 全部そろって成功' if not ng else '❌ ' + str(len(ng)) + ' 本が失敗'}"
          f"（{len(results)}本中 {len(results) - len(ng)}本 成功）　{time.time() - t0:.0f}秒")
    sys.exit(1 if ng else 0)

main()
