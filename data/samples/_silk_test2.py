"""
改进版丝轨迹提取：
- 从参考帧检测格子线位置，专门mask掉
- 差分阈值提高，只抓真正新丝
- 蚕体mask更激进
"""
import cv2, numpy as np, os

vpath = r'F:\xwechat_files\wxid_fjajtzndf5l612_8f26\msg\video\2026-11\3425b780ab8aa5d37e09e0fa81ababaa.mp4'
out_dir = r'H:\tool\silkworm-trajectory\data\samples'

v = cv2.VideoCapture(vpath)
fps = v.get(cv2.CAP_PROP_FPS)
W = int(v.get(cv2.CAP_PROP_FRAME_WIDTH))
H = int(v.get(cv2.CAP_PROP_FRAME_HEIGHT))

t_start, t_end = 20.0, 30.0
f0 = int(t_start * fps)
f1 = int(t_end * fps)

v.set(cv2.CAP_PROP_POS_FRAMES, f0)
ok, ref = v.read()
ref_gray = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)

# === 检测格子线位置 ===
# 垂直投影：每列的平均亮度，峰就是竖格线
col_mean = ref_gray.mean(axis=0)
row_mean = ref_gray.mean(axis=1)
# 找峰（格线位置）
def find_lines(profile, min_dist=40, thresh_offset=8):
    thr = profile.mean() + thresh_offset
    peaks = []
    in_peak = False
    start = 0
    for i, v in enumerate(profile):
        if v > thr and not in_peak:
            in_peak = True; start = i
        elif v <= thr and in_peak:
            in_peak = False
            peaks.append((start + i)//2)
    if in_peak: peaks.append((start + len(profile))//2)
    # 合并近邻峰
    merged = []
    for p in peaks:
        if not merged or p - merged[-1] > min_dist:
            merged.append(p)
    return merged

v_lines = find_lines(col_mean)
h_lines = find_lines(row_mean)
print(f'竖格线 x: {v_lines}')
print(f'横格线 y: {h_lines}')

# 建格子mask：在每条格线 ±4px 内mask掉
grid_mask = np.zeros((H, W), dtype=bool)
for x in v_lines:
    grid_mask[:, max(0,x-4):min(W,x+5)] = True
for y in h_lines:
    grid_mask[max(0,y-4):min(H,y+5), :] = True

time_map = np.full((H, W), -1.0, dtype=np.float32)
k_body = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31,31))

idx = f0
frame_count = 0
while idx <= f1:
    ok, frame = v.read()
    if not ok: break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    t = (idx - f0) / fps

    # 蚕体mask
    _, body = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)
    body = cv2.morphologyEx(body, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)))
    body = cv2.morphologyEx(body, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(25,25)))
    body_dil = cv2.dilate(body, k_body, iterations=2) > 0

    # 差分
    diff = cv2.absdiff(gray, ref_gray)
    # 新丝 = 差分大 & 不在格子上 & 不在蚕体上
    new_silk = (diff > 25) & (gray > 90) & (~grid_mask) & (~body_dil)
    # 轻去噪
    new_silk_u8 = new_silk.astype(np.uint8)*255
    new_silk_u8 = cv2.morphologyEx(new_silk_u8, cv2.MORPH_OPEN, np.ones((2,2),np.uint8))
    new_silk = new_silk_u8 > 0

    # 记录首次出现时间
    first = time_map == -1.0
    time_map[new_silk & first] = t
    frame_count += 1
    idx += 1

v.release()
print(f'处理 {frame_count} 帧')

# === 可视化 ===
vis = np.full((H, W, 3), 20, dtype=np.uint8)
# 淡显网格背景
vis[ref_gray < 50] = (12, 12, 16)
# 格线淡灰
vis[grid_mask] = (45, 45, 50)

valid = time_map >= 0
if valid.any():
    tmax = time_map[valid].max()
    print(f'新丝总像素: {valid.sum()}, 最晚时间: {tmax:.1f}s')
    ratio = np.clip(time_map[valid] / max(tmax,0.01), 0, 1)
    hue = (240 - ratio*240).astype(np.uint8)
    silk_hsv = np.stack([hue, np.full_like(hue,230), np.full_like(hue,255)], axis=-1)
    silk_bgr = cv2.cvtColor(silk_hsv.reshape(-1,1,3), cv2.COLOR_HSV2BGR).reshape(-1,3)
    vis[valid] = silk_bgr

# 色条
bar = np.zeros((30,300,3), dtype=np.uint8)
for x in range(300):
    h = int(240 - (x/300)*240)
    bar[:,x] = cv2.cvtColor(np.uint8([[[h,230,255]]]), cv2.COLOR_HSV2BGR)[0][0]
vis[H-40:H-10, 10:310] = bar
cv2.putText(vis, '0s', (10, H-15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
cv2.putText(vis, f'{t_end-t_start:.0f}s', (270, H-15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

out = os.path.join(out_dir, 'silk_timeline_v2.jpg')
cv2.imwrite(out, vis)
print('保存 ->', out)
