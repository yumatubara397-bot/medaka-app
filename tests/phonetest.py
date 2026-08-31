import json, subprocess, time, urllib.request, websocket, base64, sys
import os
APP=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"index.html")
PORT=9341
subprocess.run(["pkill","-f",f"remote-debugging-port={PORT}"],capture_output=True); time.sleep(1)
pr=subprocess.Popen(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome","--headless=new",
  f"--remote-debugging-port={PORT}","--no-first-run","--user-data-dir=/tmp/phonetest","--remote-allow-origins=*",
  "file://"+APP],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(4)
t=[x for x in json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json")) if x["type"]=="page"][0]
ws=websocket.create_connection(t["webSocketDebuggerUrl"],timeout=30); i=[0]
def send(m,p=None):
    i[0]+=1; ws.send(json.dumps({"id":i[0],"method":m,"params":p or {}}))
    while True:
        r=json.loads(ws.recv())
        if r.get("id")==i[0]: return r.get("result",{})
def ev(e):
    r=send("Runtime.evaluate",{"expression":e,"returnByValue":True,"awaitPromise":True})
    if "exceptionDetails" in r: return "ERR:"+str(r["exceptionDetails"].get("exception",{}).get("description",""))[:150]
    return r.get("result",{}).get("value")
def shot(path):
    d=send("Page.captureScreenshot",{"captureBeyondViewport":True})
    open(path,"wb").write(base64.b64decode(d["data"]))
ok=ng=0
def expect(n,c,d=""):
    global ok,ng
    if c: print(f"  ✅ {n} — {d}"); ok+=1
    else: print(f"  ❌ {n} — {d}"); ng+=1

time.sleep(1)
ev("localStorage.clear()")
# よくある携帯の画面幅
sizes=[("iPhone SE",375,667),("iPhone 15",393,852),("Pixel 8",412,915),("小さめAndroid",360,800)]
for name,w,h in sizes:
    send("Emulation.setDeviceMetricsOverride",{"width":w,"height":h,"deviceScaleFactor":2,"mobile":True})
    ev("switchTab('register');renderRegisterPanel()")
    time.sleep(0.6)
    r=json.loads(ev("""(()=>{
      const over=[...document.querySelectorAll('.tab,.reg-breeds button,.reg-big,.btn,.reg-step')]
        .filter(e=>e.getBoundingClientRect().right > window.innerWidth+1).length;
      const small=[...document.querySelectorAll('.reg-breeds button,.reg-big,.tab,.reg-kana button')]
        .filter(e=>e.getBoundingClientRect().height < 40).length;
      const smallList=[...document.querySelectorAll('.reg-breeds button,.reg-big,.tab,.reg-kana button')]
        .filter(e=>e.getBoundingClientRect().height < 40)
        .map(e=>e.className+':'+Math.round(e.getBoundingClientRect().height));
      return JSON.stringify({smallList, over, wide: document.body.scrollWidth > window.innerWidth+1,
        sw: document.body.scrollWidth, iw: window.innerWidth,
        cols: Math.round(window.innerWidth / (document.querySelector('.reg-breeds button')?.getBoundingClientRect().width||1)),
        small});})()"""))
    expect(f"{name} ({w}px) 横にはみ出さない", r["over"]==0 and not r["wide"],
           f"はみ出し{r['over']}個 / 横スクロール{'あり' if r['wide'] else 'なし'}({r['sw']}>{r['iw']}) / 品種{r['cols']}列")
    expect(f"{name} 押しやすい大きさ(40px以上)", r["small"]==0,
           f"小さすぎる要素 {r['small']}個 " + ("/".join(r["smallList"][:4]) if r["small"] else ""))
    if w==393: shot("/tmp/phone_reg.png")
send("Emulation.clearDeviceMetricsOverride")
print()
print(f"{'✅ すべて成功' if ng==0 else '❌ '+str(ng)+' 件失敗'}（全{ok+ng}項目）")
ws.close(); pr.terminate(); sys.exit(1 if ng else 0)
