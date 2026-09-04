#!/usr/bin/env python3
"""すべての動作確認を、正しい順番で実行する。

resptest / wintest は「通信モジュールが止まっているとき」を確かめるために
偽モジュールを止めるので、最後に回す。その手前で必ず起動し直す。
"""
import subprocess, sys, time, os, glob, pathlib

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
    time.sleep(2)

def stop_fake():
    subprocess.run(["pkill", "-f", "fake_webapi.py"], capture_output=True)
    time.sleep(0.5)

# 偽モジュールが要らないもの
PLAIN = ["registertest", "wheeltest", "foldertest", "fstest", "fsandroidtest",
         "exporttest", "redotest", "croptest", "tidytest", "goodstest",
         "goodsfixedtest", "autoprinttest", "goodsprinttest", "surfacetest",
         "labeltest", "blanktest", "glyphtest", "fittest", "nesttest", "readfoldertest", "flowtest", "phonetest"]
# 偽モジュールが要るもの（止めるものは最後）
WITH_FAKE = ["structtest", "sharptest", "dpitest", "cuttest", "speedtest", "usbtest", "resptest", "wintest"]

def run(name):
    start = time.time()
    # 前のブラウザが残っていると次が起動できないことがあるので、必ず片付けてから始める
    subprocess.run(["pkill", "-f", "remote-debugging-port"], capture_output=True)
    time.sleep(1.5)
    p = subprocess.run([sys.executable, str(HERE / f"{name}.py")],
                       capture_output=True, text=True)
    if p.returncode != 0 and "件失敗" not in p.stdout:
        # ブラウザが立ち上がらなかった等。1度だけやり直す
        subprocess.run(["pkill", "-f", "remote-debugging-port"], capture_output=True)
        time.sleep(3)
        p = subprocess.run([sys.executable, str(HERE / f"{name}.py")],
                           capture_output=True, text=True)
    last = [l for l in p.stdout.strip().split("\n") if l.strip()]
    tail = last[-1] if last else "(出力なし)"
    print(f"{name:<16} {tail}   ({time.time()-start:.0f}秒)")
    return p.returncode == 0, tail

ok = ng = 0
print("■ 偽モジュール不要のもの")
for t in PLAIN:
    good, _ = run(t)
    ok, ng = (ok + 1, ng) if good else (ok, ng + 1)

print("\n■ 偽の通信モジュールを使うもの")
for t in WITH_FAKE:
    start_fake()          # 前のテストが止めていても、毎回立て直す
    good, _ = run(t)
    ok, ng = (ok + 1, ng) if good else (ok, ng + 1)
stop_fake()

print()
print(f"{'✅ 全部そろって成功' if ng == 0 else '❌ ' + str(ng) + ' 本が失敗'}"
      f"（{ok + ng}本中 {ok}本 成功）")
sys.exit(1 if ng else 0)
