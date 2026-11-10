import cv2, os
v = cv2.VideoCapture(r'H:\tool\silkworm-trajectory\data\projects\sample1.preview.mp4')
n = int(v.get(cv2.CAP_PROP_FRAME_COUNT))
out = r'H:\tool\silkworm-trajectory\data\samples'
for i, frac in enumerate([0.1, 0.3, 0.5, 0.7, 0.9]):
    v.set(cv2.CAP_PROP_POS_FRAMES, int(n*frac))
    ok, f = v.read()
    if ok: cv2.imwrite(os.path.join(out, f'preview_{i}.jpg'), f)
v.release()
print('done')
