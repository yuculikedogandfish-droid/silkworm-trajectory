"""
丝轨迹提取：帧间差分找新丝。
原理：
- 每帧先检测蚕体（大亮块），把它mask掉（蚕体动，不是丝）
- 与参考帧（片段起始帧）做差分，新出现的亮线 = 这段时间新吐的丝
- 按时间染色（早=蓝，晚=红），看沉积顺序
"""
import cv2, numpy as np, os

vpath = r'F:\xwechat_files\wxid_fjajtzndf5l612_8f26\msg\video\2026-11\3425b780ab8aa5d37e09e0fa81ababaa.mp4'
out_dir = r'H:\tool\silkworm-trajectory\data\samples'

v = cv2.VideoCapture(vpath)
fps = v.get(cv2.CAP_PROP_FPS)
W = int(v.get(cv2.CAP_PROP_FRAME_WIDTH))
H = int(v.get(cv2.CAP_PROP_FRAME_HEIGHT))

# 取 t=20s 到 t=30s 的片段
t_start, t_end = 20.0, 30.0
f0 = int(t_start * fps)
f1 = int(t_end * fps)

# 读参考帧（片段开始）
v.set(cv2.CAP_PROP_POS_FRAMES, f0)
ok, ref = v.read()
ref_gray = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
print(f'参考帧: {t_start}s, shape={ref_gray.shape}')

# 累积画布：BGR，每个像素记录 (新丝mask, 时间)
# 用一个时间图：t=0 表示无新丝
time_map = np.full((H, W), -1.0, dtype=np.float32)

# 蚕体mask核
k_body = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25,25))

# 输出动画帧
frames_out = []
idx = f0
while idx <= f1:
    ok, frame = v.read()
    if not ok: break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    t = (idx - f0) / fps  # 片段内时间

    # 1. 检测蚕体（大亮块）
    _, body_mask = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)
    body_mask = cv2.morphologyEx(body_mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)))
    body_mask = cv2.morphologyEx(body_mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(21,21)))
    # 膨胀蚕体区域，把附近新丝也算进去（蚕头正在吐丝的位置）
    body_dilated = cv2.dilate(body_mask, k_body, iterations=2)

    # 2. 差分：当前帧 vs 参考帧
    diff = cv2.absdiff(gray, ref_gray)
    # 只保留变亮的部分（新丝），且不在蚕体mask里
    new_silk = ((diff > 15) & (gray > 80) & (body_dilated == 0)).astype(np.uint8) * 255
    # 去噪：去掉孤立小点
    new_silk = cv2.morphologyEx(new_silk, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT,(2,2)))

    # 3. 记录新丝的时间
    new_pixels = new_silk > 0
    # 只记录第一次出现的（时间最早）
    first_time = time_map == -1.0
    time_map[new_pixels & first_time] = t

    if idx % 30 == 0:
        print(f'帧 {idx} t={t_start+t:.1f}s  新丝像素={new_pixels.sum()}')
    idx += 1

v.release()

# 可视化：按时间染色
# 时间范围 0~10s
vis = np.zeros((H, W, 3), dtype=np.uint8)
# 背景暗一点
vis[:] = (20, 20, 25)
# 把参考帧的网格淡显
ref_small = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
vis[ref_small < 60] = (15, 15, 20)  # 暗底
# 网格线淡显
grid_mask = (ref_small > 100) & (ref_small < 160)
vis[grid_mask] = (50, 50, 55)

# 新丝按时间染色：蓝(早) -> 青 -> 绿 -> 黄 -> 红(晚)
valid = time_map >= 0
if valid.any():
    tmax = time_map[valid].max()
    print(f'新丝总像素: {valid.sum()}, 最晚时间: {tmax:.1f}s')
    # HSV 染色：色相从 240(蓝) 到 0(红)
    ratio = time_map[valid] / max(tmax, 0.01)
    hue = (240 - ratio * 240).astype(np.uint8)  # 240->0
    sat = np.full_like(hue, 220)
    val = np.full_like(hue, 255)
    silk_hsv = np.stack([hue, sat, val], axis=-1)
    silk_bgr = cv2.cvtColor(silk_hsv.reshape(-1,1,3), cv2.COLOR_HSV2BGR).reshape(-1,3)
    vis[valid] = silk_bgr

# 画色条
bar_h = 30
bar = np.zeros((bar_h, 300, 3), dtype=np.uint8)
for x in range(300):
    ratio = x / 300.0
    hue = int(240 - ratio * 240)
    hsv = np.uint8([[[hue, 220, 255]]])
    bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0][0]
    bar[:, x] = bgr
vis[H-bar_h-10:H-10, 10:310] = bar
cv2.putText(vis, '0s (start)', (10, H-15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
cv2.putText(vis, f'{t_end-t_start:.0f}s (end)', (230, H-15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

out_path = os.path.join(out_dir, 'silk_timeline.jpg')
cv2.imwrite(out_path, vis)
print('保存 ->', out_path)

# 也存一份原始参考帧对照
cv2.imwrite(os.path.join(out_dir, 'silk_ref_frame.jpg'), ref)
