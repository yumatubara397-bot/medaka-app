# -*- coding: utf-8 -*-
"""テプラにつながらないとき、理由が具体的に出るかを確かめる。
   「応答を読めませんでした」で終わらせず、何が返ってきたかまで見せること。"""
import time
from common import Browser, Report

b = Browser(9407, 1100, 900); r = Report()
b.ev("localStorage.clear()"); time.sleep(0.3)

def reply(js):
    """通信モジュールの返事を差し替える"""
    b.ev(f"TepraWin.fetchJson = async (path) => ({js});")

print("■ 返事の形ごとに、理由が変わる")
reply("[{printerName:'KING JIM SR-R5600P-BT'}]")
r.check("一覧が返れば使える", b.ev("(async()=>await TepraWin.available())()"), True)
r.check("そのときは理由なし", b.ev("TepraWin.lastError"), "")

reply("[]")
r.check("空の一覧なら使えない", b.ev("(async()=>await TepraWin.available())()"), False)
r.expect("プリンターが入っていないと伝える",
         "プリンターとして入っていません" in (b.ev("TepraWin.lastError") or ""), b.ev("TepraWin.lastError"))

reply("{__err:'Failed to fetch'}")
b.ev("(async()=>await TepraWin.available())()")
r.expect("つながらないときは、起動を促す",
         "起動" in (b.ev("TepraWin.lastError") or ""), b.ev("TepraWin.lastError"))

reply("{__http:500, __why:'内部エラー'}")
b.ev("(async()=>await TepraWin.available())()")
r.expect("コードと理由を出す",
         "500" in (b.ev("TepraWin.lastError") or "") and "内部エラー" in (b.ev("TepraWin.lastError") or ""),
         b.ev("TepraWin.lastError"))

reply("{__empty:true}")
b.ev("(async()=>await TepraWin.available())()")
r.expect("空の返事だと分かる", "空" in (b.ev("TepraWin.lastError") or ""), b.ev("TepraWin.lastError"))
r.expect("直し方も出る", "起動し直" in (b.ev("TepraWin.lastError") or ""), "対処を書く")

reply("{__raw:'Not Found (unexpected text)'}")
b.ev("(async()=>await TepraWin.available())()")
r.expect("何が返ってきたかを見せる",
         "Not Found" in (b.ev("TepraWin.lastError") or ""), b.ev("TepraWin.lastError"))
r.expect("「読めませんでした」で終わらせない",
         "応答を読めませんでした" not in (b.ev("TepraWin.lastError") or ""), "中身を出す")


print("■ アプリ自身のHTMLが返ってきたときは、そうと言う")
reply("{__raw:'<!DOCTYPE html> <html lang=\\'ja\\'> <title>メダカ出品アシスタント</title>'}")
b.ev("(async()=>await TepraWin.available())()")
msg = b.ev("TepraWin.lastError") or ""
r.expect("横取りされていると伝える", "横取り" in msg, msg[:70])
r.expect("直し方も出す", "🔄" in msg or "fix.html" in msg, "直し方を書く")
r.expect("HTMLの中身をそのまま並べない", "<!DOCTYPE" not in msg, "読みにくい生データは出さない")

print("■ 入口は「/」の有無の両方をためす")
b.ev("""window.__paths = [];
TepraWin.fetchJson = async (path) => { window.__paths.push(path);
  return path === '/' ? [{printerName:'KING JIM SR-R5600P-BT'}] : {__empty:true}; };""")
r.check("片方がだめでも、もう片方で見つける", b.ev("(async()=>await TepraWin.available())()"), True)
r.check("両方ためした", b.ev("window.__paths.join('|')"), "|/")
r.check("通った入口を覚える", b.ev("TepraWin.listPath"), "/")


print("■ つながっているかを聞けないときは、テープの状態で確かめる")
b.ev("""window.__asked = [];
TepraWin.fetchJson = async (path) => { window.__asked.push(path);
  if(path === '' || path === '/') return [{printerName:'KING JIM SR-R5600P'},
                                          {printerName:'KING JIM SR-R5600P-BT'}];
  if(path.startsWith('/onlinestatus/')) return {__http:500};        // 聞けない
  if(path.startsWith('/lwstatus/')) return path.includes('-BT') ? {tapeID:5} : {__http:500};
  return {};
};""")
r.check("聞けなければ「分からない」を返す",
        b.ev("(async()=>await TepraWin.isOnline('KING JIM SR-R5600P'))()"), None)
r.check("テープの状態が読めれば生きている",
        b.ev("(async()=>await TepraWin.isAlive('KING JIM SR-R5600P-BT'))()"), True)
r.check("読めなければ生きていない",
        b.ev("(async()=>await TepraWin.isAlive('KING JIM SR-R5600P'))()"), False)

b.ev("TepraWin.lastCandidates = []; TepraWin._candAt = 0; 'ok'")
names = b.ev("(async()=>(await TepraWin.candidates(true)).join('|'))()")
r.check("生きているほうを先に選ぶ", (names or "").split("|")[0], "KING JIM SR-R5600P-BT")
r.expect("どうやって調べたかも残す",
         b.ev("(TepraWin.lastCandidates.find(x=>x.bt)||{}).how") == "lwstatus", "lwstatus で確かめた")
r.expect("テープを送る呼び出しはしていない",
         not any("tapefeed" in p for p in (b.ev("window.__asked") or [])), "テープは1mmも出さない")


print("■ 「接続する」は、だめだったものを避けて次をためす")
b.ev("""window.__asked = [];
TepraWin.printerName = ''; TepraWin.lastCandidates = []; TepraWin._candAt = 0; TepraWin.forgetMemo();
TepraWin.fetchJson = async (path) => { window.__asked.push(path);
  if(path === '' || path === '/') return [{printerName:'KING JIM SR-R5600P'},
                                          {printerName:'KING JIM SR-R5600P-BT'}];
  if(path.startsWith('/onlinestatus/')) return {__http:500};
  if(path.startsWith('/lwstatus/'))
    return path.includes('-BT') ? {tapeID:5} : {__http:500, __why:'printer offline'};
  if(path.startsWith('/info/')) return {dpi:180, driverName:'x'};
  return {};
};""")
st = b.ev("(async()=>JSON.stringify(await TepraWin.connectBest()))()")
import json; st = json.loads(st)
r.check("つながる", st.get("ok"), True)
r.check("生きているほうを使う", st.get("printer"), "KING JIM SR-R5600P-BT")
r.expect("テープを送る呼び出しはしない",
         not any("tapefeed" in p for p in (b.ev("window.__asked") or [])), "テープは1mmも出さない")
r.expect("印刷もしない",
         not any(p.startswith("/print") for p in (b.ev("window.__asked") or [])), "確認のために刷らない")


print("■ onlinestatus が「つながっている」と嘘をついても、使えるほうを選ぶ")
# 実機で起きた形：USBはオフラインなのに online:true を返し、lwstatus で 500(errcode 202)
b.ev("""window.__asked = []; TepraWin._bad = {};
TepraWin.printerName=''; TepraWin.lastCandidates=[]; TepraWin._candAt=0; TepraWin.forgetMemo();
TepraWin.fetchJson = async (path) => { window.__asked.push(path);
  if(path === '' || path === '/') return [{printerName:'KING JIM SR-R5600P'},
                                          {printerName:'KING JIM SR-R5600P-BT'}];
  if(path.startsWith('/onlinestatus/')) return {online:true};          // 両方とも「つながっている」
  if(path.startsWith('/lwstatus/'))
    return path.includes('-BT') ? {statusType:5, tapeID:262, error:0}
                                : {__http:500, __why:'{"errcode":202}'};
  if(path.startsWith('/info/')) return {dpi:180};
  return {};
};""")
import json
st = json.loads(b.ev("(async()=>JSON.stringify(await TepraWin.connectBest()))()"))
r.check("つながる", st.get("ok"), True)
r.check("実際に使えるほうを選ぶ", st.get("printer"), "KING JIM SR-R5600P-BT")
r.check("Bluetooth と分かる", st.get("route"), "Bluetooth")
r.check("テープ幅も読める（tapeID 262 は 18mm）", st.get("tapeMM"), 18)
r.expect("テープを送っていない",
         not any("tapefeed" in p for p in (b.ev("window.__asked") or [])), "テープは1mmも出さない")
r.expect("印刷もしていない",
         not any(p.startswith("/print") for p in (b.ev("window.__asked") or [])), "確認のために刷らない")

print("■ 次からは、だめだったほうを後回しにする（USB優先は崩さない）")
r.check("だめだったものを覚えている", b.ev("TepraWin.isBad('KING JIM SR-R5600P')"), True)
r.check("使えたものは覚えていない", b.ev("TepraWin.isBad('KING JIM SR-R5600P-BT')"), False)
b.ev("window.__asked = []; TepraWin.forgetMemo(); TepraWin.printerName='KING JIM SR-R5600P'; 'ok'")
st2 = json.loads(b.ev("(async()=>JSON.stringify(await TepraWin.status({fresh:true})))()"))
r.check("いきなり使えるほうにつながる", st2.get("printer"), "KING JIM SR-R5600P-BT")
lw = [p for p in (b.ev("window.__asked") or []) if p.startswith("/lwstatus/")]
r.check("だめなほうに問い合わせない（待たされない）", len(lw), 1)

print("■ 自動印刷のときも、使えるほうに切り替わる")
b.ev("TepraWin.forgetMemo(); TepraWin.printerName=''; 'ok'")
st3 = json.loads(b.ev("(async()=>JSON.stringify(await TepraWin.status()))()"))
r.check("登録時の確認でも使えるほうを掴む", st3.get("printer"), "KING JIM SR-R5600P-BT")

print("■ どれもだめなら、どこで何が起きたか伝える")
b.ev("""TepraWin.printerName=''; TepraWin.lastCandidates=[]; TepraWin._candAt=0; TepraWin.forgetMemo();
TepraWin.fetchJson = async (path) => {
  if(path === '' || path === '/') return [{printerName:'KING JIM SR-R5600P'}];
  if(path.startsWith('/lwstatus/')) return {__http:500, __why:'printer offline'};
  return {__http:500};
};""")
st2 = json.loads(b.ev("(async()=>JSON.stringify(await TepraWin.connectBest()))()"))
r.check("つながらない", st2.get("ok"), False)
r.expect("プリンター名を出す", "KING JIM SR-R5600P" in (st2.get("error") or ""), (st2.get("error") or "")[:50])
r.expect("コードを出す", "500" in (st2.get("error") or ""), "コード")
r.expect("モジュールが返した理由も出す", "printer offline" in (st2.get("error") or ""), "生の理由")
r.expect("何を確認すればよいか出す", "電源" in (st2.get("error") or ""), "対処")

print("■ 詳しく見る画面")
b.ev("""TepraWin.fetchJson = async (path) => (path === '/' ? {__http:404} : {__err:'Failed to fetch'});
TepraWin.lastError = 'つながりません'; 'ok'""")
b.ev("showTepraDiag()"); time.sleep(0.8)
txt = b.ev("document.getElementById('tepraDiagDialog').textContent") or ""
r.expect("送り先が出る", "localhost:29108" in txt, "送り先")
r.expect("版が出る", "アプリの版" in txt, "版")
r.expect("ブラウザが出る", "ブラウザ" in txt, "端末")
r.expect("両方の入口の結果が出る", txt.count("localhost:29108") >= 2, "/ の有無の両方")
r.expect("つながらない理由が出る", "Failed to fetch" in txt, "生の理由")
r.expect("コードも出る", "404" in txt, "HTTPコード")
r.expect("コピーできる", b.ev("!!document.getElementById('tdCopy')"), "コピーボタン")
b.ev("document.getElementById('tdClose').click()"); time.sleep(0.2)
r.expect("閉じられる", b.ev("document.getElementById('tepraDiagDialog').classList.contains('hidden')"), "hidden")

print("■ USB が戻れば USB に戻る（優先順は崩さない）")
b.ev("""TepraWin._bad = {}; TepraWin.forgetMemo();
TepraWin.printerName=''; TepraWin.lastCandidates=[]; TepraWin._candAt=0;
TepraWin.fetchJson = async (path) => {
  if(path === '' || path === '/') return [{printerName:'KING JIM SR-R5600P'},
                                          {printerName:'KING JIM SR-R5600P-BT'}];
  if(path.startsWith('/onlinestatus/')) return {online:true};
  if(path.startsWith('/lwstatus/')) return {statusType:5, tapeID:263, error:0};   // 両方とも読める
  if(path.startsWith('/info/')) return {dpi:180};
  return {};
};""")
st4 = json.loads(b.ev("(async()=>JSON.stringify(await TepraWin.connectBest()))()"))
r.check("両方使えるなら USB を選ぶ", st4.get("printer"), "KING JIM SR-R5600P")
r.check("USB と表示する", st4.get("route"), "USB")
r.check("しばらく経てば、だめだった印も消える",
        b.ev("(()=>{ TepraWin._bad = {'x': Date.now() - TepraWin.BAD_MS - 1}; return TepraWin.isBad('x'); })()"),
        False)

b.close(); r.finish()
