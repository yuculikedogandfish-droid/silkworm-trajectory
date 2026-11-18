from PIL import Image, ImageFilter
import statistics
for p in [r"data\projects\参考图.png", r"data\projects\参考图横.jpeg"]:
    im = Image.open(p).convert("L")
    k = min(1, 1400 / max(im.size))
    im = im.resize((int(im.size[0]*k), int(im.size[1]*k)))
    w, h = im.size
    g = list(im.getdata())
    thr = 90
    xs = []; ys = []
    for y in range(h):
        b = y*w
        for x in range(w):
            if g[b+x] > thr: xs.append(x); ys.append(y)
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    print(p, "bbox", (x0,y0,x1,y1))
    cols = [0]*(x1-x0+1); rows = [0]*(y1-y0+1)
    for y in range(y0, y1+1):
        b = y*w
        for x in range(x0, x1+1):
            if g[b+x] > thr: cols[x-x0] += 1; rows[y-y0] += 1
    def ac(prof, lo, hi, detrend=250):
        n = len(prof)
        ma = []
        run = 0; acc = 0
        for i in range(n):
            acc += prof[i]
            if i >= detrend: acc -= prof[i-detrend]
            ma.append(acc / min(i+1, detrend))
        d = [prof[i]-ma[i] for i in range(n)]
        mean = sum(d)/n
        out = []
        for lag in range(lo, hi):
            s = sum((d[i]-mean)*(d[i+lag]-mean) for i in range(n-lag))/(n-lag)
            out.append((s, lag))
        out.sort(reverse=True)
        return [(round(s,1), l) for s,l in out[:6]]
    print(" cols AC", ac(cols, 40, min(len(cols)//2, 500)))
    print(" rows AC", ac(rows, 40, min(len(rows)//2, 500)))
