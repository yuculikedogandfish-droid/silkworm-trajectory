"""测试分割：在一帧上跑阈值+形态学，看能不能把蚕从格子和丝里分离出来"""
import cv2, numpy as np, os

vpath = r'F:\xwechat_files\wxid_fjajtzndf5l612_8f26\msg\video\2026-11\3425b780ab8aa5d37e09e0fa81ababaa.mp4'
out_dir = r'H:\tool\silkworm-trajectory\data\samples'

v = cv2.VideoCapture(vpath)
n = int(v.get(cv2.CAP_PROP_FRAME_COUNT))
v.set(cv2.CAP_PROP_POS_FRAMES, int(n*0.4))
ok, frame = v.read()
v.release()

gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
print('gray shape:', gray.shape, 'min/max/mean:', gray.min(), gray.max(), int(gray.mean()))

# 不同阈值对比
for thr in [100, 130, 160]:
    _, mask = cv2.threshold(gray, thr, 255, cv2.THRESH_BINARY)
    # 形态学开运算：去掉细线（格子、丝），保留蚕体
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7,7))
    opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    # 再闭运算把蚕体填实
    kernel2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15,15))
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel2)
    cv2.imwrite(os.path.join(out_dir, f'threshold_{thr}.jpg'), closed)

    # 找轮廓
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = frame.copy()
    dets = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < 200: continue
        x,y,w,h = cv2.boundingRect(c)
        cx, cy = x+w/2, y+h/2
        # 轮廓上离质心最远的点
        M = cv2.moments(c)
        if M['m00']:
            mcxi, mcyi = M['m10']/M['m00'], M['m01']/M['m00']
        else:
            mcxi, mcyi = cx, cy
        pts = c.reshape(-1,2)
        d = ((pts[:,0]-mcxi)**2 + (pts[:,1]-mcyi)**2)
        k = np.argmax(d)
        hx, hy = pts[k]
        dets.append((area, x,y,w,h, hx,hy))
        cv2.rectangle(out, (x,y), (x+w,y+h), (0,255,0), 2)
        cv2.circle(out, (int(hx),int(hy)), 6, (0,0,255), -1)
        cv2.putText(out, f'{int(area)}', (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 1)
    cv2.imwrite(os.path.join(out_dir, f'detect_{thr}.jpg'), out)
    print(f'thr={thr}: 检测到 {len(dets)} 个蚕体')
    for d in dets: print('  area=%d bbox=(%d,%d,%d,%d) head=(%d,%d)' % d)
