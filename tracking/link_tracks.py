"""
轨迹碎片拼接 + 可视化。
把 track_silkworm.py 输出的碎片化轨迹，按"末端点接近 + 时间间隔短"重新连接成完整轨迹。
"""
import csv, json, os, argparse
import numpy as np
import cv2

def load_tracks(csv_path):
    tracks = {}
    with open(csv_path, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            pid = int(r['id'])
            tracks.setdefault(pid, []).append((float(r['t']), float(r['x_px']), float(r['y_px'])))
    for pid in tracks: tracks[pid].sort()
    return tracks

def link_fragments(tracks, max_gap_s=3.0, max_dist=150):
    """贪心拼接：每条碎片的尾点找最近的另一条碎片的头点（时间间隔 < max_gap）"""
    # 取每条碎片的首尾
    frags = []
    for pid, pts in tracks.items():
        if len(pts) < 10: continue
        frags.append({'id': pid, 'start_t': pts[0][0], 'end_t': pts[-1][0],
                       'start_xy': (pts[0][1], pts[0][2]), 'end_xy': (pts[-1][1], pts[-1][2]),
                       'pts': pts, 'used': False})
    frags.sort(key=lambda f: f['start_t'])

    # 链式拼接
    chains = []
    for f in frags:
        if f['used']: continue
        chain = [f]; f['used'] = True
        # 向前找后继
        while True:
            last = chain[-1]
            best, best_d = None, max_dist
            for g in frags:
                if g['used']: continue
                gap = g['start_t'] - last['end_t']
                if gap < 0 or gap > max_gap_s: continue
                d = np.hypot(g['start_xy'][0]-last['end_xy'][0], g['start_xy'][1]-last['end_xy'][1])
                if d < best_d: best_d, best = d, g
            if best is None: break
            best['used'] = True; chain.append(best)
        chains.append(chain)
    return chains

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--csv', default=r'H:\tool\silkworm-trajectory\data\projects\sample1_track.csv')
    ap.add_argument('--bg', default=None, help='背景帧（可选，画轨迹用）')
    args = ap.parse_args()

    tracks = load_tracks(args.csv)
    print(f'载入 {len(tracks)} 条碎片')
    chains = link_fragments(tracks)
    print(f'拼接成 {len(chains)} 条完整轨迹')

    # 画总览图
    W, H = 1280, 1280
    canvas = np.zeros((H, W, 3), dtype=np.uint8)
    if args.bg and os.path.exists(args.bg):
        canvas = cv2.imread(args.bg)
    COLORS = [(232,160,76),(94,182,168),(217,107,90),(122,156,214),(182,120,201),(143,191,106),(217,194,90)]
    out_data = []
    for i, chain in enumerate(chains):
        col = COLORS[i % len(COLORS)]
        all_pts = []
        for f in chain:
            all_pts.extend(f['pts'])
        all_pts.sort()
        out_data.append({'id': i+1, 'points': all_pts})
        # 画轨迹
        for j in range(1, len(all_pts)):
            cv2.line(canvas,
                     (int(all_pts[j-1][1]), int(all_pts[j-1][2])),
                     (int(all_pts[j][1]), int(all_pts[j][2])),
                     col, 2)
        # 起点画圆
        cv2.circle(canvas, (int(all_pts[0][1]), int(all_pts[0][2])), 8, col, -1)
        cv2.putText(canvas, f'#{i+1} ({len(all_pts)}pt)',
                    (int(all_pts[0][1])+10, int(all_pts[0][2])),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, col, 2)
        print(f'  轨迹 #{i+1}: {len(all_pts)} 点, t={all_pts[0][0]:.1f}s~{all_pts[-1][0]:.1f}s, 由 {len(chain)} 片拼成')

    out_path = r'H:\tool\silkworm-trajectory\data\projects\sample1_overview.jpg'
    cv2.imwrite(out_path, canvas)
    print('总览图 ->', out_path)

    # 导出拼接后的 JSON
    json_out = r'H:\tool\silkworm-trajectory\data\projects\sample1_linked.json'
    with open(json_out, 'w', encoding='utf-8') as f:
        json.dump({
            'fps': 30, 'calibration': None,
            'silkworms': [
                {'id': c['id'], 'color': '#e8a04c',
                 'style': {'headWidth':0.3,'midWidth':1.0,'tailWidth':0.15,'opacity':0.9,'material':'ribbon'},
                 'points': [{'t':round(t,3),'x':round(x,1),'y':round(y,1)} for (t,x,y) in c['points']]}
                for c in out_data
            ]
        }, f, ensure_ascii=False, indent=2)
    print('拼接 JSON ->', json_out)

if __name__ == '__main__':
    main()
