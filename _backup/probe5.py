from PIL import Image, ImageFilter
import statistics, sys
sys.setrecursionlimit(20000)
for p in [r"data\projects\参考图.png", r"data\projects\参考图横.jpeg"]:
    im = Image.open(p).convert("L"); k = min(1, 1400/max(im.size))
    im = im.resize((int(im.size[0]*k), int(im.size[1]*k)))
    im = im.filter(ImageFilter.GaussianBlur(5))
    w,h = im.size; g=list(im.getdata())
    mx=max(g); thr = max(40, int(mx*0.35))
    M=[1 if v>thr else 0 for v in g]
    lab=[0]*(w*h); comps=[]
    for i in range(w*h):
        if M[i] and not lab[i]:
            stack=[i]; lab[i]=1; x0=x1=i%w; y0=y1=i//w; n=0
            while stack:
                q=stack.pop(); x=q%w; y=q//w; n+=1
                x0=min(x0,x);x1=max(x1,x);y0=min(y0,y);y1=max(y1,y)
                for nb in (q-1,q+1,q-w,q+w):
                    if 0<=nb<w*h and M[nb] and not lab[nb]:
                        lab[nb]=1; stack.append(nb)
            comps.append((n,x0,x1,y0,y1))
    big=[c for c in comps if c[0] > w*h*0.004]
    ws=[c[2]-c[1]+1 for c in big]; hs=[c[4]-c[3]+1 for c in big]
    print(p,"thr",thr,"comps",len(comps),"big",len(big),"w med",statistics.median(ws),"h med",statistics.median(hs))
    for c in sorted(big,key=lambda c:(c[3],c[1]))[:12]: print("   ",c)
