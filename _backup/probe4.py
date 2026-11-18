from PIL import Image
import statistics, sys
sys.setrecursionlimit(10000)
for p in [r"data\projects\参考图.png", r"data\projects\参考图横.jpeg"]:
    im = Image.open(p).convert("L"); k = min(1, 1400/max(im.size))
    im = im.resize((int(im.size[0]*k), int(im.size[1]*k)))
    w,h = im.size; g=list(im.getdata()); M=[1 if v>90 else 0 for v in g]
    lab=[0]*(w*h); comps=[]; cur=0
    for i in range(w*h):
        if M[i] and not lab[i]:
            cur+=1; stack=[i]; lab[i]=cur; x0=x1=i%w; y0=y1=i//w; n=0
            while stack:
                q=stack.pop(); x=q%w; y=q//w; n+=1
                x0=min(x0,x);x1=max(x1,x);y0=min(y0,y);y1=max(y1,y)
                for nb in (q-1,q+1,q-w,q+w):
                    if 0<=nb<w*h and M[nb] and not lab[nb]:
                        lab[nb]=cur; stack.append(nb)
            comps.append((n,x0,x1,y0,y1))
    big=[c for c in comps if c[0] > w*h*0.002]
    print(p, "w,h",w,h,"comps",len(comps),"big",len(big))
    ws=[c[2]-c[1]+1 for c in big]; hs=[c[4]-c[3]+1 for c in big]
    print("  width median",statistics.median(ws),"height median",statistics.median(hs))
    ys=sorted(set(round((c[3]+c[4])/2/20)*20 for c in big))
    print("  row centers(bucket20)", ys[:20])
    print("  sample", sorted(big, key=lambda c:(c[3],c[1]))[:8])
