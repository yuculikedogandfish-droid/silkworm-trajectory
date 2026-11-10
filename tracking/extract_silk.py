"""
丝轨迹完整提取：
1. 逐帧差分提取新丝，记录每个像素首次出现时间
2. 骨架细化（skeletonize）
3. 追踪骨架为矢量折线
4. 导出：时间热力图 PNG + 矢量 SVG（每段按时间染色）
"""
import cv2, numpy as np, os
from skimage.morphology import skeletonize

vpath = r'F:\xwechat_files\wxid_fjajtzndf5l612_8f26\msg\video\2026-11\3425b780ab8aa5d37e09e0fa81ababaa.mp4'
out_dir = r'H:\tool\silkworm-trajectory\data\projects'

v = cv2.VideoCapture(vpath)
fps = v.get(cv2.CAP_PROP_FPS)
W = int(v.get(cv2.CAP_PROP_FRAME_WIDTH))
H = int(v.get(cv2.CAP_PROP_FRAME_HEIGHT))

# 取 20s~35s（蚕活跃期）
t_start, t_end = 20.0, 35.0
f0 = int(t_start * fps)
f1 = int(t_end * fps)

v.set(cv2.CAP_PROP_POS_FRAMES, f0)
ok, ref = v.read()
ref_gray = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)

# 检测格子线
def find_lines(profile, min_dist=40, thresh_offset=8):
    thr = profile.mean() + thresh_offset
    peaks, in_peak, start = [], False, 0
    for i, val in enumerate(profile):
        if val > thr and not in_peak: in_peak, start = True, i
        elif val <= thr and in_peak:
            in_peak = False; peaks.append((start+i)//2)
    if in_peak: peaks.append((start+len(profile))//2)
    merged = []
    for p in peaks:
        if not merged or p - merged[-1] > min_dist: merged.append(p)
    return merged

v_lines = find_lines(ref_gray.mean(axis=0))
h_lines = find_lines(ref_gray.mean(axis=1))
grid_mask = np.zeros((H, W), dtype=bool)
for x in v_lines: grid_mask[:, max(0,x-4):min(W,x+5)] = True
for y in h_lines: grid_mask[max(0,y-4):min(H,y+5), :] = True

# 逐帧累积新丝时间
time_map = np.full((H, W), -1.0, dtype=np.float32)
k_body = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31,31))
k_close = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))

idx = f0
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

    # 差分找新丝
    diff = cv2.absdiff(gray, ref_gray)
    new_silk = (diff > 20) & (gray > 85) & (~grid_mask) & (~body_dil)
    new_silk_u8 = new_silk.astype(np.uint8)*255
    # 闭运算连接断丝
    new_silk_u8 = cv2.morphologyEx(new_silk_u8, cv2.MORPH_CLOSE, k_close)
    new_silk = new_silk_u8 > 0

    first = time_map == -1.0
    time_map[new_silk & first] = t
    if idx % 150 == 0:
        print(f'帧 {idx} t={t_start+t:.1f}s  累积新丝像素={(time_map>=0).sum()}')
    idx += 1
v.release()

# === 骨架化 ===
silk_mask = time_map >= 0
print(f'总新丝像素: {silk_mask.sum()}')
skeleton = skeletonize(silk_mask)
print(f'骨架像素: {skeleton.sum()}')

# === 追踪骨架为折线 ===
# 对每个连通区域，从端点开始追踪
from scipy import ndimage as ndi
labeled, n_labels = ndi.label(skeleton)
print(f'连通区域: {n_labels}')

def trace_skeleton(skel, label_id, labeled_img, time_map):
    """追踪一个连通骨架为折线，返回 [(x,y,t), ...]"""
    region = (labeled_img == label_id)
    ys, xs = np.where(region)
    pts_set = set(zip(xs.tolist(), ys.tolist()))
    if len(pts_set) < 3: return None

    # 找端点（只在一个邻居的点）
    endpoints = []
    for (x, y) in pts_set:
        nbr = 0
        for dx in [-1,0,1]:
            for dy in [-1,0,1]:
                if dx==0 and dy==0: continue
                if (x+dx, y+dy) in pts_set: nbr += 1
        if nbr == 1: endpoints.append((x,y))

    if not endpoints:
        # 环形，从任意点开始
        start = next(iter(pts_set))
    else:
        start = endpoints[0]

    # 追踪
    path = [start]
    visited = {start}
    cur = start
    while True:
        nxt = None
        for dx in [-1,0,1]:
            for dy in [-1,0,1]:
                if dx==0 and dy==0: continue
                p = (cur[0]+dx, cur[1]+dy)
                if p in pts_set and p not in visited:
                    nxt = p; break
            if nxt: break
        if nxt is None: break
        path.append(nxt); visited.add(nxt); cur = nxt
        if len(path) > 5000: break

    if len(path) < 3: return None
    return [(x, y, float(time_map[y,x])) for (x,y) in path]

all_paths = []
for lbl in range(1, n_labels+1):
    # 过滤太小的区域
    area = (labeled == lbl).sum()
    if area < 5: continue
    p = trace_skeleton(skeleton, lbl, labeled, time_map)
    if p and len(p) >= 3:
        all_paths.append(p)

print(f'提取矢量路径: {len(all_paths)} 条')

# === 导出 SVG ===
def t_to_color(t, tmax):
    ratio = t / max(tmax, 0.01)
    # HSV: 240(蓝)->0(红)
    h = 240 - ratio*240
    import colorsys
    r,g,b = colorsys.hsv_to_rgb(h/360, 0.9, 1.0)
    return f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'

tmax = time_map[silk_mask].max()
svg_paths = []
for p in all_paths:
    # 把路径按时间分段（同色段合并）
    d = f'M {p[0][0]:.1f} {p[0][1]:.1f}'
    for i in range(1, len(p)):
        d += f' L {p[i][0]:.1f} {p[i][1]:.1f}'
    avg_t = sum(pt[2] for pt in p) / len(p)
    color = t_to_color(avg_t, tmax)
    svg_paths.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.2" stroke-linecap="round" opacity="0.85"><desc>t={avg_t:.2f}s</desc></path>')

svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<rect width="{W}" height="{H}" fill="#0a0a0e"/>
{chr(10).join(svg_paths)}
</svg>'''
svg_path = os.path.join(out_dir, 'silk_trajectory.svg')
with open(svg_path, 'w', encoding='utf-8') as f:
    f.write(svg)
print('SVG ->', svg_path)

# === 导出热力图 PNG ===
vis = np.full((H, W, 3), 15, dtype=np.uint8)
vis[grid_mask] = (40, 40, 45)
valid = time_map >= 0
if valid.any():
    ratio = np.clip(time_map[valid]/max(tmax,0.01), 0, 1)
    hue = (240 - ratio*240).astype(np.uint8)
    hsv = np.stack([hue, np.full_like(hue,230), np.full_like(hue,255)], axis=-1)
    bgr = cv2.cvtColor(hsv.reshape(-1,1,3), cv2.COLOR_HSV2BGR).reshape(-1,3)
    vis[valid] = bgr
# 叠加骨架（白线描边）
vis[skeleton] = (255,255,255)

# 色条
bar = np.zeros((30,300,3), dtype=np.uint8)
for x in range(300):
    h = int(240 - (x/300)*240)
    bar[:,x] = cv2.cvtColor(np.uint8([[[h,230,255]]]), cv2.COLOR_HSV2BGR)[0][0]
vis[H-40:H-10, 10:310] = bar
cv2.putText(vis, '0s', (10, H-15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
cv2.putText(vis, f'{t_end-t_start:.0f}s', (270, H-15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

png_path = os.path.join(out_dir, 'silk_timeline_final.jpg')
cv2.imwrite(png_path, vis, [cv2.IMWRITE_JPEG_QUALITY, 90])
print('热力图 ->', png_path)
