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

reply("{__raw:'<html>Not Found</html>'}")
b.ev("(async()=>await TepraWin.available())()")
r.expect("何が返ってきたかを見せる",
         "Not Found" in (b.ev("TepraWin.lastError") or ""), b.ev("TepraWin.lastError"))
r.expect("「読めませんでした」で終わらせない",
         "応答を読めませんでした" not in (b.ev("TepraWin.lastError") or ""), "中身を出す")

print("■ 入口は「/」の有無の両方をためす")
b.ev("""window.__paths = [];
TepraWin.fetchJson = async (path) => { window.__paths.push(path);
  return path === '/' ? [{printerName:'KING JIM SR-R5600P-BT'}] : {__empty:true}; };""")
r.check("片方がだめでも、もう片方で見つける", b.ev("(async()=>await TepraWin.available())()"), True)
r.check("両方ためした", b.ev("window.__paths.join('|')"), "|/")
r.check("通った入口を覚える", b.ev("TepraWin.listPath"), "/")

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

b.close(); r.finish()
