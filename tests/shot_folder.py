import time, base64
from common import Browser
b = Browser(9354, 1100, 1500)
b.ev("localStorage.clear();switchTab('register');renderRegisterPanel()"); time.sleep(0.8)
b.ev("""{ TepraLink._kind='none';
  [['幹之','特上',3],['夜桜','上物',1],['オロチ','通常',5]].forEach(([nm,rk,n])=>{
    regSel.breed=regMasters().breeds.find(x=>x.name===nm);
    regSel.rank=rk; regSel.qtyMode='pair'; regSel.qtyN=n; regSel.step=3; regDoRegister(); }); }""")
time.sleep(1.0)
# 色つきのダミー写真を作る
b.ev("""{ const mk=(c)=>{const cv=document.createElement('canvas');cv.width=cv.height=200;
    const x=cv.getContext('2d');x.fillStyle=c;x.fillRect(0,0,200,200);
    x.fillStyle='#fff';x.font='bold 40px sans-serif';x.fillText(c.slice(1),20,110);return cv.toDataURL();};
  const cols=['#2b6cb0','#2f855a','#b7791f','#9b2c2c','#553c9a','#0987a0','#b83280','#4a5568','#276749','#975a16'];
  photos = cols.map((c,i)=>({name:'IMG_'+String(i+1).padStart(3,'0')+'.jpg',
    handle:null, blobUrl:mk(c), isLabel:false}));
  folderHandle={name:'テスト'}; }""")
b.ev("switchTab('edit');document.getElementById('assignPerItem').value=3;refreshAssignBar()"); time.sleep(0.3)
b.ev("assignPhotosToRegistered()"); time.sleep(1.5)
d = b.send("Page.captureScreenshot", {"captureBeyondViewport": True})
open("/tmp/folders.png","wb").write(base64.b64decode(d["data"]))
print("撮影OK")
b.close()
