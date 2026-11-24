import cv2, numpy as np
p = r'C:\Users\54364\AppData\Local\Doubao\User Data\ClipboardTemp\6b643051-5cc5-4931-936f-e2e9517b281f.png'
im = cv2.imread(p)
g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
b = cv2.GaussianBlur(g, (5,5), 1.2)
for p2 in (100, 150, 200):
    cc = cv2.HoughCircles(b, cv2.HOUGH_GRADIENT, dp=1.2, minDist=32, param1=150, param2=p2, minRadius=15, maxRadius=180)
    out = im.copy()
    n = 0 if cc is None else len(cc[0])
    if cc is not None:
        for x,y,r in np.round(cc[0]).astype(int):
            cv2.circle(out,(x,y),r,(80,220,230),2)
            cv2.circle(out,(x,y),2,(0,0,255),3)
    cv2.imwrite(rf'C:\Users\54364\AppData\Local\Temp\cvhough{p2}.png',out)
    print(p2,n)
