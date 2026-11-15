"""从描图器导出的轨迹 JSON 统计运动指纹，产出 silkworm-motion-profile/v1。

用法（仓库根目录）：
    python tools\\derive_profile.py data\\projects\\sample1_track.json data\\projects\\sample2_track.json
    python tools\\derive_profile.py <track.json> --out profiles --top 6

口径与 prototype/weave-lab.html 的 profileFromPoints 一致：
    步长中位数 / P25、36 桶转角直方图、转向持续性、曲率半径、停顿率、自交环数、包络尺寸。
未标定（没有 x_mm）时长度单位记 px，并在 source.calibrated=false 标注，不得进论文。
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

TAU = math.pi * 2


def median(values):
    if not values:
        return 0.0
    s = sorted(values)
    return float(s[len(s) // 2])


def pct(values, p):
    if not values:
        return 0.0
    s = sorted(values)
    idx = min(len(s) - 1, max(0, int(len(s) * p)))
    return float(s[idx])


def ang_diff(a, b):
    d = a - b
    while d > math.pi:
        d -= TAU
    while d < -math.pi:
        d += TAU
    return d


def rdp(points, tol):
    """Douglas-Peucker，和原型 simplify() 同义。"""
    if len(points) < 3:
        return points
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        a, b = stack.pop()
        ax, ay = points[a]
        bx, by = points[b]
        dx, dy = bx - ax, by - ay
        seg = math.hypot(dx, dy)
        best, best_i = -1.0, -1
        for i in range(a + 1, b):
            px, py = points[i]
            if seg < 1e-9:
                dist = math.hypot(px - ax, py - ay)
            else:
                dist = abs(dy * px - dx * py + bx * ay - by * ax) / seg
            if dist > best:
                best, best_i = dist, i
        if best > tol and best_i > 0:
            keep[best_i] = True
            stack.append((a, best_i))
            stack.append((best_i, b))
    return [p for p, k in zip(points, keep) if k]


def count_crossings(points):
    n = min(len(points), 260)
    if n < 4:
        return 0
    stride = max(1, len(points) // n)
    p = points[::stride]

    def orient(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    def hit(a, b, c, d):
        o1, o2 = orient(a, b, c), orient(a, b, d)
        o3, o4 = orient(c, d, a), orient(c, d, b)
        return o1 * o2 < 0 and o3 * o4 < 0

    hits = 0
    for i in range(len(p) - 1):
        for j in range(i + 2, len(p) - 1):
            if i == 0 and j == len(p) - 2:
                continue
            if hit(p[i], p[i + 1], p[j], p[j + 1]):
                hits += 1
    return hits


def derive(points, worm_id, label, calibrated, seed, kind="assumption", quality="auto-track"):
    pts = [(float(p["x"]), float(p["y"])) for p in points
           if isinstance(p, dict) and isinstance(p.get("x"), (int, float))
           and isinstance(p.get("y"), (int, float))]
    if len(pts) < 8:
        return None

    # 先按“跳变”切段：轨迹里偶发的身份错配/丢帧会瞬移，不能当运动学证据
    raw_steps = [math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
                 for i in range(1, len(pts))]
    moving_raw = [v for v in raw_steps if v > 1e-6]
    jump = max(6 * (median(moving_raw) or 1.0), pct(moving_raw, 0.9) * 2.0)
    segs, cur = [], [pts[0]]
    for i in range(1, len(pts)):
        if raw_steps[i - 1] > jump:
            if len(cur) >= 4:
                segs.append(cur)
            cur = [pts[i]]
        else:
            cur.append(pts[i])
    if len(cur) >= 4:
        segs.append(cur)
    if not segs:
        return None

    steps, turns, signed = [], [], []
    for seg in segs:
        for i in range(1, len(seg)):
            steps.append(math.hypot(seg[i][0] - seg[i - 1][0], seg[i][1] - seg[i - 1][1]))
            if i > 1:
                a1 = math.atan2(seg[i - 1][1] - seg[i - 2][1], seg[i - 1][0] - seg[i - 2][0])
                a2 = math.atan2(seg[i][1] - seg[i - 1][1], seg[i][0] - seg[i - 1][0])
                d = ang_diff(a2, a1)
                turns.append(abs(d))
                signed.append(d)

    moving = [v for v in steps if v > 1e-6]
    step_mean = median(moving) or 1.8
    step_sd = pct(moving, 0.25)
    pause_rate = (sum(1 for v in steps if v < step_mean * 0.25) / len(steps)) if steps else 0.0

    hist = [0.0] * 36
    for t in turns:
        b = min(35, max(0, int((t / math.pi) * 36)))
        hist[b] += 1.0
    h_sum = sum(hist) or 1.0
    hist = [round(v / h_sum, 5) for v in hist]

    runs, run_len, last_sign, acc = 0, 0, 0, 0
    for d in signed:
        if abs(d) < 0.02:
            continue
        s = 1 if d > 0 else -1
        if s == last_sign:
            run_len += 1
        else:
            if run_len > 0:
                acc += run_len
                runs += 1
            run_len, last_sign = 1, s
    if run_len > 0:
        acc += run_len
        runs += 1
    persistence = round(acc / runs, 2) if runs else 1.0

    radii, total_len = [], 0.0
    for seg in segs:
        for i in range(2, len(seg)):
            ds = math.hypot(seg[i][0] - seg[i - 1][0], seg[i][1] - seg[i - 1][1])
            total_len += ds
            a1 = math.atan2(seg[i - 1][1] - seg[i - 2][1], seg[i - 1][0] - seg[i - 2][0])
            a2 = math.atan2(seg[i][1] - seg[i - 1][1], seg[i][0] - seg[i - 1][0])
            th = abs(ang_diff(a2, a1))
            if ds > step_mean * 0.3 and th > 1e-3:
                radii.append(ds / th)
    radius_typ = round(median(radii), 2)
    radius_min = round(pct(radii, 0.05), 2)

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    bbox = [round(max(xs) - min(xs), 2), round(max(ys) - min(ys), 2)]

    # 环数 = 自交次数 / 穿过外接框的“圈数”，避免长轨迹把环数算成几百
    crossings = 0
    for seg in segs:
        crossings += count_crossings(rdp(seg, max(0.4, step_mean * 0.7)))
    diag = math.hypot(bbox[0], bbox[1]) or 1.0
    encloses = max(1.0, total_len / (diag * 4))
    loops = round(crossings / encloses, 2)

    curve_amp = round(min(0.5, max(0.06, median(turns) or 0.22)), 3)
    max_turn = round(min(1.2, max(0.2, pct(turns, 0.95))), 3)

    return {
        "schema": "silkworm-motion-profile/v1",
        "wormId": int(worm_id),
        "label": ("实测指纹 · " if calibrated else "未标定（px）· ") + label,
        "source": {
            "kind": kind,
            "project": label,
            "calibrated": bool(calibrated),
            "quality": quality,
            "assumed": ["wallAffinity"],
            "note": ("长度单位 mm" if calibrated else "长度单位 px（未标定）") +
                    ("；自动追踪，含身份跳变，仅用于引擎联调" if quality == "auto-track" else "；人工描图"),
        },
        "fingerprint": {
            "stepMean": round(step_mean, 3),
            "stepSD": round(step_sd, 3),
            "turnHist": hist,
            "turnSignPersistence": persistence,
            "maxTurn": max_turn,
            "curveAmp": curve_amp,
            "radiusTyp": radius_typ,
            "radiusMin": radius_min,
            "pauseRate": round(pause_rate, 3),
            "wallAffinity": 0.5,
            "loopsPerEnvelope": loops,
            "bbox": bbox,
        },
        "sampler": {"type": "histogram", "seed": int(seed), "temperature": 0.35},
    }


def load_tracks(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    calibrated = bool(data.get("calibration"))
    worms = data.get("silkworms") or data.get("worms") or []
    if not worms and isinstance(data.get("curves"), list):
        worms = [{"id": i + 1, "points": [
            {"x": p.get("x_mm"), "y": p.get("y_mm")} for p in c.get("points", [])
        ]} for i, c in enumerate(data["curves"])]
        calibrated = True
    return data, worms, calibrated


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tracks", nargs="+")
    ap.add_argument("--out", default="profiles")
    ap.add_argument("--top", type=int, default=6, help="每个文件最多产出几条（按点数取前 N）")
    ap.add_argument("--seed", type=int, default=20261116)
    ap.add_argument("--measured", action="store_true", help="数据来自人工描图，标 measured；否则标 assumption/auto-track")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    for track in args.tracks:
        path = Path(track)
        data, worms, calibrated = load_tracks(path)
        ranked = sorted(worms, key=lambda w: len(w.get("points", [])), reverse=True)
        stem = path.stem.replace("_track", "")
        for w in ranked[: args.top]:
            wid = int(w.get("id", 1))
            label = f"{stem} / 蚕 {wid}（{len(w.get('points', []))} 点）"
            prof = derive(w.get("points", []), wid, label, calibrated, args.seed,
                          kind="measured" if args.measured else "assumption",
                          quality="manual" if args.measured else "auto-track")
            if not prof:
                continue
            target = out_dir / f"{stem}-w{wid}.json"
            target.write_text(json.dumps(prof, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            f = prof["fingerprint"]
            unit = "mm" if calibrated else "px"
            print(f"{target.name}\t步长 {f['stepMean']}{unit} ± {f['stepSD']}\t"
                  f"R {f['radiusTyp']}{unit}\t环 {f['loopsPerEnvelope']}\t"
                  f"转向持续 {f['turnSignPersistence']}\t停顿 {f['pauseRate']}\t"
                  f"bbox {f['bbox'][0]}x{f['bbox'][1]}")
            total += 1
    print(f"total profiles: {total} → {out_dir}")


if __name__ == "__main__":
    main()
