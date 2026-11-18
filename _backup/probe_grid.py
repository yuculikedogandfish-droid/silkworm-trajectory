from PIL import Image
import statistics
for p in [r"data\projects\参考图.png", r"data\projects\参考图横.jpeg"]:
    im = Image.open(p).convert("L")
    k = min(1, 1400 / max(im.size))
    im = im.resize((int(im.size[0]*k), int(im.size[1]*k)))
    w, h = im.size
    px = list(im.getdata())
    thr = 90
    cols = [0]*w; rows = [0]*h
    for y in range(h):
        base = y*w
        for x in range(w):
            if px[base+x] > thr:
                cols[x] += 1; rows[y] += 1
    def stats(name, prof, n):
        mx = max(prof); med = statistics.median(prof)
        low = [i for i,v in enumerate(prof) if v < mx*0.12]
        print(name, "size", n, "max", mx, "median", med, "lowcols(<12%)", len(low))
    stats("cols", cols, w); stats("rows", rows, h)
    # 自相关主峰
    def ac(prof, lo, hi):
        mean = sum(prof)/len(prof)
        best = []
        for lag in range(lo, hi):
            s = sum((prof[i]-mean)*(prof[i+lag]-mean) for i in range(len(prof)-lag))/(len(prof)-lag)
            best.append((s, lag))
        best.sort(reverse=True)
        return best[:5]
    print("cols peaks", [(round(s,1), l) for s,l in ac(cols, 20, min(w//2, 600))])
    print("rows peaks", [(round(s,1), l) for s,l in ac(rows, 20, min(h//2, 600))])
