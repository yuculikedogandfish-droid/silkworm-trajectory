import cv2, os
vpath = r'F:\xwechat_files\wxid_fjajtzndf5l612_8f26\msg\video\2026-11\3425b780ab8aa5d37e09e0fa81ababaa.mp4'
out_dir = r'H:\tool\silkworm-trajectory\data\samples'
os.makedirs(out_dir, exist_ok=True)

v = cv2.VideoCapture(vpath)
print('opened:', v.isOpened())
W = int(v.get(cv2.CAP_PROP_FRAME_WIDTH))
H = int(v.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = v.get(cv2.CAP_PROP_FPS)
n = int(v.get(cv2.CAP_PROP_FRAME_COUNT))
print(f'res: {W}x{H}  fps: {fps:.2f}  frames: {n}  dur: {n/fps:.2f}s')

# 抽 6 帧：0%, 20%, 40%, 60%, 80%, 100%
for i, frac in enumerate([0.0, 0.2, 0.4, 0.6, 0.8, 0.99]):
    v.set(cv2.CAP_PROP_POS_FRAMES, int(n*frac))
    ok, frame = v.read()
    if not ok: continue
    p = os.path.join(out_dir, f'frame_{i}_{int(frac*100)}.jpg')
    cv2.imwrite(p, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    print('saved', p, frame.shape)
v.release()
