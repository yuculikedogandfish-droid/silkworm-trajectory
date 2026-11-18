from PIL import Image, ImageFilter
import statistics
p = r"data\projects\参考图.png"
im = Image.open(p).convert("L"); k=1400/max(im.size); im=im.resize((int(im.size[0]*k),int(im.size[1]*k)))
im = im.filter(ImageFilter.GaussianBlur(1.0))
w,h=im.size; g=list(im.getdata()); mx=max(g); thr=int(mx*0.28)
x0,x1,y0,y1=148,901,146,1281
dark=[0]*(x1-x0+1)
for y in range(y0,y1+1):
    b=y*w
    for x in range(x0,x1+1):
        if g[b+x] < thr: dark[x-x0]+=1
# 平滑
S=[sum(dark[max(0,i-3):i+4])/len(dark[max(0,i-3):i+4]) for i in range(len(dark))]
peaks=[]
for i in range(2,len(S)-2):
    if S[i]>=S[i-1] and S[i]>=S[i+1] and S[i] > (y1-y0)*0.55:
        if peaks and i-peaks[-1][0]<=6:
            if S[i]>S[peaks[-1][0]]: peaks[-1]=(i,S[i])
        else: peaks.append((i,S[i]))
print("cols",w,h,"thr",thr,"peaks",[(a,round(b)) for a,b in peaks])
dark2=[0]*(y1-y0+1)
for y in range(y0,y1+1):
    b=y*w
    for x in range(x0,x1+1):
        if g[b+x] < thr: dark2[y-y0]+=1
S2=[sum(dark2[max(0,i-3):i+4])/len(dark2[max(0,i-3):i+4]) for i in range(len(dark2))]
peaks2=[]
for i in range(2,len(S2)-2):
    if S2[i]>=S2[i-1] and S2[i]>=S2[i+1] and S2[i] > (x1-x0)*0.55:
        if peaks2 and i-peaks2[-1][0]<=6:
            if S2[i]>S[peaks2[-1][0]]: peaks2[-1]=(i,S2[i])
        else: peaks2.append((i,S2[i]))
print("row peaks",[(a,round(b)) for a,b in peaks2])
print("col gaps",[peaks[i+1][0]-peaks[i][0] for i in range(len(peaks)-1)])
print("row gaps",[peaks2[i+1][0]-peaks2[i][0] for i in range(len(peaks2)-1)])
