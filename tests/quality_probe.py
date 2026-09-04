"""二値化と描画方法の組み合わせを、同じ文字で作り比べて数値で評価する。"""
import time, base64, io
from common import Browser
from PIL import Image

b = Browser(9384, 1100, 900)
b.ev("localStorage.clear(); setTepraFontScale(0.86); setTepraMinLenRatio(2.4)"); time.sleep(0.5)

# 方式ごとに画像を作る関数を、その場で用意する
b.ev(r"""
window.__make = function(lines, heightDots, opt){
  const pad = 12, gap = heightDots*0.03;
  const weights = lines.map((l,i)=> i===0 ? 1.15 : 1.0);
  const total = weights.reduce((a,b)=>a+b,0);
  const usable = heightDots - gap*(lines.length-1);
  const hs = weights.map(w=>usable*w/total);
  const tmp = document.createElement('canvas').getContext('2d');
  const scale = 0.86;
  const fonts = lines.map((t,i)=>`${i===0?'700':'500'} ${Math.round(hs[i]*scale)}px "Noto Sans JP", sans-serif`);
  let content=0; lines.forEach((t,i)=>{tmp.font=fonts[i]; content=Math.max(content,tmp.measureText(t).width);});
  const W = Math.ceil(Math.max(heightDots*2.4, content+pad*2)), H = heightDots;

  const SS = opt.ss||1;
  const cv = document.createElement('canvas'); cv.width=W*SS; cv.height=H*SS;
  const cx = cv.getContext('2d');
  cx.fillStyle='#fff'; cx.fillRect(0,0,cv.width,cv.height);
  cx.fillStyle='#000'; cx.textBaseline='middle';
  let y=0;
  lines.forEach((t,i)=>{
    const size=parseInt(fonts[i].match(/(\d+)px/)[1],10);
    const weight=fonts[i].startsWith('700')?'700':'500';
    cx.font=`${weight} ${size*SS}px "Noto Sans JP", sans-serif`;
    cx.fillText(t, pad*SS, (y+hs[i]/2)*SS);
    y += hs[i]+gap;
  });

  let out = cv, ox = cx;
  if(SS>1){
    out = document.createElement('canvas'); out.width=W; out.height=H;
    ox = out.getContext('2d');
    ox.imageSmoothingEnabled=true; ox.imageSmoothingQuality='high';
    ox.fillStyle='#fff'; ox.fillRect(0,0,W,H);
    ox.drawImage(cv,0,0,W,H);
  }

  const img = ox.getImageData(0,0,W,H), d = img.data;
  // 明るさの並びを作る
  const gray = new Uint8Array(W*H);
  for(let i=0,p=0;i<d.length;i+=4,p++) gray[p]=(d[i]*299+d[i+1]*587+d[i+2]*114)/1000|0;

  let th = opt.th;
  if(opt.method==='otsu'){
    const hist=new Array(256).fill(0);
    for(const v of gray) hist[v]++;
    const n=gray.length; let sum=0; for(let i=0;i<256;i++) sum+=i*hist[i];
    let sumB=0,wB=0,best=0,bestT=128;
    for(let t=0;t<256;t++){
      wB+=hist[t]; if(!wB) continue;
      const wF=n-wB; if(!wF) break;
      sumB+=t*hist[t];
      const mB=sumB/wB, mF=(sum-sumB)/wF, v=wB*wF*(mB-mF)*(mB-mF);
      if(v>best){best=v;bestT=t;}
    }
    th = bestT;
  }
  for(let i=0,p=0;i<d.length;i+=4,p++){
    const bw = gray[p] < th ? 0 : 255;
    d[i]=d[i+1]=d[i+2]=bw; d[i+3]=255;
  }
  ox.putImageData(img,0,0);
  return { png: out.toDataURL('image/png').split(',')[1], th: th, w: W, h: H };
};
""")
time.sleep(0.5)

def holes(im):
    w,h = im.size; px = im.load()
    seen=[[False]*h for _ in range(w)]
    st=[(x,y) for x in range(w) for y in (0,h-1) if px[x,y]>128]
    st+=[(x,y) for y in range(h) for x in (0,w-1) if px[x,y]>128]
    for x,y in st: seen[x][y]=True
    while st:
        x,y=st.pop()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx,ny=x+dx,y+dy
            if 0<=nx<w and 0<=ny<h and not seen[nx][ny] and px[nx,ny]>128:
                seen[nx][ny]=True; st.append((nx,ny))
    c=0
    for x in range(w):
        for y in range(h):
            if px[x,y]>128 and not seen[x][y]:
                c+=1; s2=[(x,y)]; seen[x][y]=True
                while s2:
                    a,bq=s2.pop()
                    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                        na,nb=a+dx,bq+dy
                        if 0<=na<w and 0<=nb<h and not seen[na][nb] and px[na,nb]>128:
                            seen[na][nb]=True; s2.append((na,nb))
    return c

def ink(im):
    px=im.load(); w,h=im.size
    return sum(1 for x in range(w) for y in range(h) if px[x,y]<128)/(w*h)

def min_stroke(im):
    """横方向に連続する黒の長さのうち、いちばん多い長さ（本線の太さの目安）"""
    px=im.load(); w,h=im.size
    from collections import Counter
    c=Counter()
    for y in range(h):
        run=0
        for x in range(w):
            if px[x,y]<128: run+=1
            elif run: c[run]+=1; run=0
        if run: c[run]+=1
    return c.most_common(3)

L = ["忘却の翼","通常 雄5 雌8","MD-260902-004"]
print(f"{'方式':<28}{'しきい値':>8}{'字の穴':>8}{'黒の割合':>10}   よくある線の太さ")
for name, opt in [
    ("いま(3倍縮小 + 150)", {"ss":3,"method":"fixed","th":150}),
    ("3倍縮小 + 128",       {"ss":3,"method":"fixed","th":128}),
    ("3倍縮小 + Otsu",      {"ss":3,"method":"otsu"}),
    ("等倍 + 150",          {"ss":1,"method":"fixed","th":150}),
    ("等倍 + 128",          {"ss":1,"method":"fixed","th":128}),
    ("等倍 + Otsu",         {"ss":1,"method":"otsu"}),
    ("等倍 + 100",          {"ss":1,"method":"fixed","th":100}),
]:
    import json
    r = b.ev(f"__make({L!r}, 128, {json.dumps(opt)})")
    im = Image.open(io.BytesIO(base64.b64decode(r["png"]))).convert("L")
    print(f"{name:<28}{r['th']:>8}{holes(im):>8}{ink(im)*100:>9.1f}%   {min_stroke(im)}")
b.close()
