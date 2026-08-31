import time, base64
from common import Browser
b = Browser(9362, 1000, 1200)
b.ev("localStorage.clear();switchTab('register');renderRegisterPanel()"); time.sleep(0.8)
b.ev("document.getElementById('regTidyStart').click()"); time.sleep(0.6)
for n in ['錦鯉','蜃気楼','ブラックリム']:
    b.ev(f"[...document.querySelectorAll('#regBreedList button.tidy')].find(x=>x.querySelector('.bn').textContent==={n!r}).click()")
    time.sleep(0.4)
d = b.send("Page.captureScreenshot", {"captureBeyondViewport": True})
open("/tmp/tidy.png","wb").write(base64.b64decode(d["data"])); print("撮影OK")
b.close()
