from PIL import Image
for p in [r"data\projects\参考图.png", r"data\projects\参考图横.jpeg"]:
    im = Image.open(p).convert("L")
    k = min(1, 1400 / max(im.size))
    im = im.resize((int(im.size[0]*k), int(im.size[1]*k)))
    w, h = im.size
    g = list(im.getdata()); thr = 90
    xs = []; ys = []
    for y in range(h):
        b=y*w
        for x in range(w):
            if g[b+x] > thr: xs.append(x); ys.append(y)
    x0,x1,y0,y1 = min(xs),max(xs),min(ys),max(ys)
    def prof(axis):
        if axis=='x':
            P=[0]*(x1-x0+1)
            for y in range(y0,y1+1):
                b=y*w
                for x in range(x0,x1+1):
                    if g[b+x]>thr: P[x-x0]+=1
        else:
            P=[0]*(y1-y0+1)
            for y in range(y0,y1+1):
                b=y*w; c=0
                for x in range(x0,x1+1):
                    if g[b+x]>thr: c+=1
                P[y-y0]=c
        return P
    for axis in ('x','y'):
        P = prof(axis); n=len(P); mx=max(P)
        mins=[]
        for i in range(3, n-3):
            if P[i] <= P[i-1] and P[i] <= P[i+1] and P[i] < mx*0.62:
                mn = min(P[max(0,i-6):i+7])
                if P[i] == mn and i>0: mins.append((i, P[i]))
        # 合并相邻
        out=[]
        for i,v in mins:
            if out and i-out[-1][0] <= 4: 
                if v < out[-1][1]: out[-1]=(i,v)
            else: out.append((i,v))
        print(p, axis, "n", n, "mx", mx, "minima", [(a,b) for a,b in out][:30])
