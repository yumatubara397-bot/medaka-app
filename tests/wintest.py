import json, subprocess, time, urllib.request, websocket, sys, datetime, glob, os
import os
APP=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"index.html")
PORT=9342
subprocess.run(["pkill","-f",f"remote-debugging-port={PORT}"],capture_output=True); time.sleep(1)
pr=subprocess.Popen(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome","--headless=new",
  f"--remote-debugging-port={PORT}","--no-first-run","--user-data-dir=/tmp/wintest","--remote-allow-origins=*",
  "--window-size=1280,1000","file://"+APP],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(3)
t=[x for x in json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json")) if x["type"]=="page"][0]
ws=websocket.create_connection(t["webSocketDebuggerUrl"],timeout=60); i=[0]
def ev(e):
    i[0]+=1; ws.send(json.dumps({"id":i[0],"method":"Runtime.evaluate","params":{"expression":e,"returnByValue":True,"awaitPromise":True}}))
    while True:
        m=json.loads(ws.recv())
        if m.get("id")==i[0]:
            r=m.get("result",{})
            if "exceptionDetails" in r: return "ERR:"+str(r["exceptionDetails"].get("exception",{}).get("description",""))[:200]
            return r.get("result",{}).get("value")
ev("for(let k=0;k<400 && typeof renderRegisterPanel==='undefined';k++){}"); time.sleep(1)
ok=ng=0
def check(n,g,w):
    global ok,ng
    if g==w: print(f"  ✅ {n}: {g!r}"); ok+=1
    else: print(f"  ❌ {n}: 期待 {w!r} / 実際 {g!r}"); ng+=1
def expect(n,c,d=""):
    global ok,ng
    if c: print(f"  ✅ {n} — {d}"); ok+=1
    else: print(f"  ❌ {n} — {d}"); ng+=1

for f in glob.glob("/tmp/fake_tepra/*"): os.unlink(f)
ev("localStorage.clear();switchTab('register')"); time.sleep(0.5)

print("■ Windowsの通信モジュールを見つける")
check("経路の判定", ev("TepraLink.probe()"), "windows")
check("直接印刷できる", ev("TepraLink.available()"), True)
st = ev("TepraLink.status()")
check("プリンター名", st.get("printer"), "KING JIM SR-R5600P")
check("テープ幅を読む", st.get("tapeMM"), 24)
ev("renderRegisterPanel()"); time.sleep(1.2)
expect("状態バーに出る", "SR-R5600P" in (ev("document.getElementById('regTepraBar').textContent") or ""),
       (ev("document.getElementById('regTepraBar').textContent") or "").strip()[:60])

print("■ 登録すると、その場で1枚出る")
today = datetime.date.today().strftime("%y%m%d")
ev("regSel.breed=regMasters().breeds.find(b=>b.name==='幹之');regSel.rank='SS';regSel.qty='3匹';regDoRegister()")
time.sleep(2.5)
pngs = sorted(glob.glob("/tmp/fake_tepra/*.png"))
expect("テプラへ画像が届いた", len(pngs)==1, f"{len(pngs)}枚 " + (os.path.basename(pngs[0]) if pngs else ""))
check("印刷済みになる", ev("regUnprinted().length"), 0)

if pngs:
    from PIL import Image
    im = Image.open(pngs[0])
    check("画像の高さ＝24mmの印字ドット数", im.height, 128)
    expect("横幅は文字ぶんだけ伸びる", im.width > 128, f"{im.width}x{im.height}")
    expect("白地に黒", im.convert("RGB").getpixel((1,1)) == (255,255,255), str(im.convert("RGB").getpixel((1,1))))
    dark = sum(1 for px in im.convert("L").getdata() if px < 100)
    expect("文字が描かれている", dark > 200, f"黒い点 {dark}個")
    params = json.load(open(sorted(glob.glob("/tmp/fake_tepra/*_param.json"))[0]))
    check("テープIDは24mm", params["tapeID"], 263)
    check("ラベルごとに切る", params["tapeCut"], 2)
    check("テープ幅の確認を出さない", params["displayTapeWidth"], 1)
    check("エラー画面を出さない", params["errorMessage"]["mode"], 1)
    check("印刷設定の確認を出さない", params["displayPrintSetting"], 1)
    check("プレビューを出さない", params["displayPrintPreview"], 1)
    check("部数は1", params["copies"], 1)
    # 公式SDKが送る項目がすべて入っているか
    need = ["copies","tapeCut","halfCut","printSpeed","density","tapeID",
            "priorityCutSetting","halfCutSeparate","marginLeftRight","displayTapeWidth",
            "errorMessage","displayTransferTape","displayPrintSetting","cutTitle",
            "kanaZen","displayPrintPreview","stretchImage"]
    missing = [k for k in need if k not in params]
    expect("公式SDKと同じ項目がそろっている", not missing, "足りない: " + str(missing))

print("■ まとめて印刷")
for f in glob.glob("/tmp/fake_tepra/*"): os.unlink(f)
ev("""{ regSel.breed=regMasters().breeds.find(b=>b.name==='夜桜');regSel.rank='A';regSel.qty='1ペア';regSel.step=4;regDoRegister(); }""")
time.sleep(2.5)
ev("""{ const l=regItems(); l.forEach(x=>x.tepraExportedAt=null); saveRegItems(l); renderRegisterPanel(); }""")
time.sleep(0.5)
for f in glob.glob("/tmp/fake_tepra/*"): os.unlink(f)
check("未印刷が2件", ev("regUnprinted().length"), 2)
ev("tepraPrintPending()"); time.sleep(3.0)
pngs = sorted(glob.glob("/tmp/fake_tepra/*.png"))
check("2枚届いた", len(pngs), 2)
check("全部印刷済みになる", ev("regUnprinted().length"), 0)

print("■ 通信モジュールが止まっているとき")
subprocess.run(["pkill","-f","fake_webapi.py"],capture_output=True); time.sleep(1)
ev("TepraLink._kind=null; TepraWin.printerName=null;")
check("経路なしと判定", ev("TepraLink.probe()"), "none")
r = ev("TepraLink.print([{variety:'幹之',rank:'SS',quantityText:'3匹',controlNo:'X-1'}])")
check("印刷せず理由を返す", r.get("ok"), False)
expect("理由が入っている", bool(r.get("error")), r.get("error"))

print()
print(f"{'✅ すべて成功' if ng==0 else '❌ '+str(ng)+' 件失敗'}（全{ok+ng}項目）")
ws.close(); pr.terminate(); sys.exit(1 if ng else 0)
