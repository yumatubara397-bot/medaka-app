"""テプラ クリエイター WebAPI の通信モジュールを真似たもの（検証用）。
実際の Windows と同じ URL・同じ応答を返し、送られてきた画像を保存する。"""
import json, base64, pathlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

OUT = pathlib.Path("/tmp/fake_tepra"); OUT.mkdir(exist_ok=True)
for f in OUT.glob("*"): f.unlink()

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, obj, code=200):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers(); self.wfile.write(b)
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.end_headers()
    def do_GET(self):
        p = self.path
        if p == "/api/printer":
            names = ["TEPRA PRO SR-R5600P", "TEPRA PRO SR-R5600P (Bluetooth)"]
            if pathlib.Path("/tmp/fake_tepra_usb_gone").exists():
                names = names[1:]
            self._send([{"printerName": n} for n in names])
        elif p.startswith("/api/printer/info/"):
            self._send({"driverName": "SR-R5600P", "dpi": 180, "tapeList": [263]})
        elif p.startswith("/api/printer/lwstatus/"):
            self._send({"tapeID": 263, "tapeKind": 0, "error": 0, "brTapeKind": 0})
        else:
            self._send({"error": "not found"}, 404)
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(n) or b"{}")
        # 公式SDKが送っている項目がそろっているか調べ、足りなければ本物と同じく 400 を返す
        need = ["copies","tapeCut","halfCut","printSpeed","density","tapeID",
                "priorityCutSetting","halfCutSeparate","marginLeftRight","displayTapeWidth",
                "errorMessage","displayTransferTape","displayPrintSetting","cutTitle",
                "kanaZen","displayPrintPreview","stretchImage"]
        pp = body.get("printParameter", {})
        missing = [k for k in need if k not in pp]
        bad = []
        if not isinstance(pp.get("density"), dict): bad.append("density")
        if not isinstance(pp.get("errorMessage"), dict): bad.append("errorMessage")
        for k in ["tapeCut","halfCut","printSpeed","priorityCutSetting","halfCutSeparate",
                  "displayTapeWidth","displayTransferTape","displayPrintSetting","displayPrintPreview"]:
            if k in pp and pp[k] not in (1,2,3): bad.append(k)
        if missing or bad:
            self._send({"error": "invalid parameter",
                        "missing": missing, "bad": bad}, 400)
            return
        # USB機が「印刷だけ失敗する」状態を作れるようにする
        if pathlib.Path("/tmp/fake_tepra_usb_fail").exists() and "Bluetooth" not in self.path:
            self._send({"error": "printer offline"}, 500)
            return
        img = body.get("printFile", {}).get("imageFile", {})
        idx = len(list(OUT.glob("*.png"))) + 1
        if img.get("base64Str"):
            (OUT / f"{idx:02d}_{img.get('fileName','label.png')}").write_bytes(base64.b64decode(img["base64Str"]))
        (OUT / f"{idx:02d}_param.json").write_text(json.dumps(body.get("printParameter", {}), ensure_ascii=False))
        self._send({"errorCode": 0, "printJob": {"jobId": idx}})

ThreadingHTTPServer(("127.0.0.1", 29108), H).serve_forever()
