"""ブラウザ(Chrome)を裏で動かして index.html を検証するための共通部分。"""
import json, subprocess, time, urllib.request, websocket, sys, os

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "index.html")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

class Browser:
    def __init__(self, port, width=1280, height=1200):
        self.port = port
        subprocess.run(["pkill", "-f", f"remote-debugging-port={port}"], capture_output=True)
        time.sleep(1)
        self.proc = subprocess.Popen(
            [CHROME, "--headless=new", f"--remote-debugging-port={port}", "--no-first-run",
             f"--user-data-dir=/tmp/medaka_test_{port}", "--remote-allow-origins=*",
             f"--window-size={width},{height}", "file://" + APP],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)
        tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json"))
        page = [t for t in tabs if t["type"] == "page"][0]
        self.ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=60)
        self.n = 0
        self.ev("for(let k=0;k<400 && typeof renderRegisterPanel==='undefined';k++){}")
        time.sleep(1)

    def send(self, method, params=None):
        self.n += 1
        self.ws.send(json.dumps({"id": self.n, "method": method, "params": params or {}}))
        while True:
            m = json.loads(self.ws.recv())
            if m.get("id") == self.n:
                return m.get("result", {})

    def ev(self, expr):
        r = self.send("Runtime.evaluate",
                      {"expression": expr, "returnByValue": True, "awaitPromise": True})
        if "exceptionDetails" in r:
            return "ERR:" + str(r["exceptionDetails"].get("exception", {}).get("description", ""))[:200]
        return r.get("result", {}).get("value")

    def close(self):
        try: self.ws.close()
        except Exception: pass
        self.proc.terminate()

class Report:
    def __init__(self): self.ok = 0; self.ng = 0
    def check(self, name, got, want):
        if got == want: print(f"  ✅ {name}: {got!r}"); self.ok += 1
        else: print(f"  ❌ {name}: 期待 {want!r} / 実際 {got!r}"); self.ng += 1
    def expect(self, name, cond, detail=""):
        if cond: print(f"  ✅ {name} — {detail}"); self.ok += 1
        else: print(f"  ❌ {name} — {detail}"); self.ng += 1
    def finish(self):
        print()
        print(f"{'✅ すべて成功' if self.ng == 0 else '❌ ' + str(self.ng) + ' 件失敗'}（全{self.ok + self.ng}項目）")
        sys.exit(1 if self.ng else 0)
