"""
改进版自动追踪：顶视视频 → 多蚕检测 → 头端定位 → 轨迹输出。

关键改进（基于实拍帧测试）：
- 不用背景相减：丝随时间积累会变成"准背景"，相减会误检。
- 直接阈值分割（亮蚕体 vs 暗底）+ 形态学去格子/细丝。
- 头端定位：PCA 找身体长轴两端，比较两端小圆盘内的亮度，
  蚕头壳略深褐色，较暗的一端 = 头。

用法:
    python track_silkworm.py --video <mp4> [--thr 160] [--min-area 5000]
"""
import argparse, json, os, csv
import cv2
import numpy as np


def detect_frame(gray, thr=160, min_area=8000):
    """返回 [(cx,cy, head_x,head_y, area, end_a_is_head), ...] 和 mask"""
    _, mask = cv2.threshold(gray, thr, 255, cv2.THRESH_BINARY)
    # 开运算去细线（格子、单根丝）
    k1 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7,7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k1)
    # 闭运算把蚕体填实
    k2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21,21))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area: continue
        x,y,w,h = cv2.boundingRect(c)
        # 长宽比过滤：蚕是长条的（>1.8），丝团是圆的（<1.5）
        ar = max(w,h) / max(1, min(w,h))
        if ar < 1.8: continue
        pts = c.reshape(-1, 2).astype(np.float32)
        # PCA 找主方向
        mean = pts.mean(axis=0)
        cov = np.cov((pts - mean).T)
        eigvals, eigvecs = np.linalg.eigh(cov)
        v = eigvecs[:, np.argmax(eigvals)]  # 长轴方向
        proj = (pts - mean) @ v
        # 两端点
        i_a, i_b = np.argmin(proj), np.argmax(proj)
        pa, pb = pts[i_a], pts[i_b]
        # 比较两端小圆盘内的灰度均值（头端略暗）
        def disk_mean(p, r=8):
            x, y = int(round(p[0])), int(round(p[1]))
            x0, x1 = max(0, x-r), min(gray.shape[1], x+r+1)
            y0, y1 = max(0, y-r), min(gray.shape[0], y+r+1)
            if x1<=x0 or y1<=y0: return 255
            yy, xx = np.mgrid[y0:y1, x0:x1]
            m = (xx-x)**2 + (yy-y)**2 <= r*r
            if m.sum() == 0: return 255
            return gray[y0:y1, x0:x1][m].mean()
        ma, mb = disk_mean(pa), disk_mean(pb)
        head = pa if ma < mb else pb  # 暗的一端 = 头
        out.append((float(mean[0]), float(mean[1]),
                    float(head[0]), float(head[1]),
                    float(area), pa, pb))
    return out, mask


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--video', required=True)
    ap.add_argument('--thr', type=int, default=160)
    ap.add_argument('--min-area', type=int, default=8000)
    ap.add_argument('--out-name', default=None)
    ap.add_argument('--preview', action='store_true', help='输出带框预览视频')
    args = ap.parse_args()

    cap = cv2.VideoCapture(args.video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f'视频 {W}x{H} @ {fps:.1f}fps, 共 {n} 帧, {n/fps:.1f}s')

    tracks = {}       # id -> [(t, hx, hy)]
    next_id = 1
    prev_cent = {}    # id -> (cx, cy) 最后一次体质心（用质心做跨帧匹配，稳定不跳）
    missed = {}       # id -> 连续丢失帧数
    MAX_MISS = 20     # 丢失 0.67s 内仍允许续上
    COLORS = [(232,160,76),(94,182,168),(217,107,90),(122,156,214),(182,120,201)]

    writer = None
    if args.preview:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        preview_path = os.path.join('data','projects', (args.out_name or 'preview')+'.preview.mp4')
        writer = cv2.VideoWriter(preview_path, fourcc, fps, (W, H))

    idx = 0
    while True:
        ok, frame = cap.read()
        if not ok: break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        dets, mask = detect_frame(gray, args.thr, args.min_area)
        t = idx / fps

        # 用体质心做跨帧匹配（稳定），头端位置每帧独立
        used = set()
        for (cx, cy, hx, hy, area, pa, pb) in dets:
            best_id, best_d = None, 80  # px，蚕体质心移动慢
            for pid, (px, py) in prev_cent.items():
                if pid in used: continue
                d = np.hypot(cx-px, cy-py)
                if d < best_d: best_d, best_id = d, pid
            if best_id is None:
                best_id = next_id; next_id += 1
                tracks[best_id] = []
            used.add(best_id)
            tracks[best_id].append((t, hx, hy))  # 记录头端位置
            prev_cent[best_id] = (cx, cy)
            missed[best_id] = 0

            if writer:
                col = COLORS[(best_id-1) % len(COLORS)]
                cv2.circle(frame, (int(hx), int(hy)), 8, col, -1)
                cv2.circle(frame, (int(cx), int(cy)), 4, (255,255,255), -1)
                cv2.putText(frame, f'#{best_id}', (int(cx)+10, int(cy)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, col, 2)
                for (tt, tx, ty) in tracks[best_id][-150:]:
                    cv2.circle(frame, (int(tx), int(ty)), 2, col, -1)
        for pid in list(prev_cent):
            if pid not in used:
                missed[pid] = missed.get(pid, 0) + 1
                if missed[pid] > MAX_MISS:
                    del prev_cent[pid]

        if writer: writer.write(frame)
        if idx % 300 == 0:
            print(f'帧 {idx:4d} t={t:6.2f}s  检测 {len(dets)} 只, 当前活跃 ID: {sorted(prev_cent.keys())}')
        idx += 1

    cap.release()
    if writer: writer.release(); print('预览视频 ->', preview_path)

    # 输出
    base = args.out_name or os.path.splitext(os.path.basename(args.video))[0]
    out_dir = os.path.join('data', 'projects')
    os.makedirs(out_dir, exist_ok=True)
    # 过滤掉过短的轨迹（误检/闪烁产生的假 ID），只保留 >=30 帧（约1秒）的
    MIN_POINTS = 30
    good_tracks = {pid: pts for pid, pts in tracks.items() if len(pts) >= MIN_POINTS}
    print(f'原始 {len(tracks)} 个 ID，过滤后保留 {len(good_tracks)} 条轨迹（>= {MIN_POINTS} 点）')

    csv_path = os.path.join(out_dir, base + '_track.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['t', 'id', 'x_px', 'y_px'])
        for pid, pts in good_tracks.items():
            for (t, x, y) in pts:
                w.writerow([f'{t:.3f}', pid, f'{x:.1f}', f'{y:.1f}'])
    print('CSV ->', csv_path)

    json_path = os.path.join(out_dir, base + '_track.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'fps': fps, 'calibration': None,
            'silkworms': [
                {'id': pid, 'color': '#e8a04c',
                 'style': {'headWidth':0.3,'midWidth':1.0,'tailWidth':0.15,'opacity':0.9,'material':'ribbon'},
                 'points': [{'t':round(t,3),'x':round(x,1),'y':round(y,1)} for (t,x,y) in pts]}
                for pid, pts in good_tracks.items()
            ]
        }, f, ensure_ascii=False, indent=2)
    print('JSON ->', json_path)
    print(f'共追踪 {len(good_tracks)} 只蚕')


if __name__ == '__main__':
    main()
