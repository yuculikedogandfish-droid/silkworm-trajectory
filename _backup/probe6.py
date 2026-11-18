from PIL import Image, ImageFilter
import statistics
for p in [r"data\projects\参考图.png", r"data\projects\参考图横.jpeg"]:
    im = Image.open(p).convert("L")
    k = 360/max(im.size); im = im.resize((int(im.size[0]*k), int(im.size[1]*k)))
    im = im.filter(ImageFilter.GaussianBlur(1.2))
    w,h=im.size; g=list(im.getdata())
    mx=max(g); thr=int(mx*0.4); M=[[1 if g[y*w+x]>thr else 0 for x in range(w)] for y in range(h)]
    # erode 1
    E=[[0]*w for _ in range(h)]
    for y in range(1,h-1):
        for x in range(1,w-1):
            if M[y][x] and M[y-1][x] and M[y+1][x] and M[y][x-1] and M[y][x+1]: E[y][x]=1
    comps=[]
    for y in range(h):
        for x in range(w):
            if E[y][x]:
                stack=[(y,x)]; E[y][x]=0; n=0; x0=x1=x; y0=y1=y
                while stack:
                    cy,cx=stack.pop(); n+=1
                    x0=min(x0,cx);x1=max(x1,cx);y0=min(y0,cy);y1=max(y1,cy)
                    for ny,nx in ((cy-1,cx),(cy+1,cx),(cy,cx-1),(cy,cx+1)):
                        if 0<=ny<h and 0<=nx<w and E[ny][nx]: E[ny][nx]=0; stack.append((ny,nx))
                comps.append((n,x0,x1,y0,y1))
    big=[c for c in comps if c[0]>= (w*h)*0.003]
    print(p,"at",w,h,"thr",thr,"comps",len(comps),"big",len(big))
    for c in sorted(big,key=lambda c:(c[3],c[1]))[:14]: print("   ",c, "wh", c[2]-c[1]+1, c[4]-c[3]+1)
    if big:
        print("   med w",statistics.median([c[2]-c[1]+1 for c in big]),"med h",statistics.median([c[4]-c[3]+1 for c in big]))
