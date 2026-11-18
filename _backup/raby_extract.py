"""从真实蚕样本 trajectories.json 提取八字运动模板。

输入: G:\raby model\trajectories.json (curves3d/v2, worm 1, 2 笔, 标定 61.06 px/mm)
输出:
  _backup/raby_template.json  — 嵌入 index.html 的归一化路径模板（JS 片段）
  profiles/raby-worm1.json    — silkworm-motion-profile/v1（measured）
"""

import json, io, os

SRC = r"G:\raby model\trajectories.json"
ROOT = r"H:\tool\silkworm-trajectory"
N_PER = 56

d = json.load(io.open(SRC, encoding="utf-8"))
curves = sorted(d["curves3d"], key=lambda c: c.get("strokeIndex", 0))
print("curves:", [(c["id"], c["pointCount"], c.get("length_mm")) for c in curves])


def resample(pts, n):
    # pts: [(x, y)] 按弧长等距重采样
    seg = []
    total = 0.0
    for i in range(len(pts) - 1):
        dx = pts[i + 1][0] - pts[i][0]
        dy = pts[i + 1][1] - pts[i][1]
        L = (dx * dx + dy * dy) ** 0.5
        seg.append(L)
        total += L
    out = []
    step = total / (n - 1)
    acc = 0.0
    j = 0
    for k in range(n):
        target = k * step
        while j < len(seg) - 1 and acc + seg[j] < target:
            acc += seg[j]
            j += 1
        if total <= 0:
            out.append(pts[0])
            continue
        t = (target - acc) / seg[j] if seg[j] > 0 else 0.0
        t = max(0.0, min(1.0, t))
        x = pts[j][0] + (pts[j + 1][0] - pts[j][0]) * t
        y = pts[j][1] + (pts[j + 1][1] - pts[j][1]) * t
        out.append((x, y))
    return out


strokes = []
for c in curves:
    raw = [(p["x_mm"], p["y_mm"]) for p in c["points"]]
    rs = resample(raw, N_PER)
    xs = [p[0] for p in rs]; ys = [p[1] for p in rs]
    cx = (min(xs) + max(xs)) / 2; cy = (min(ys) + max(ys)) / 2
    half = max(max(xs) - min(xs), max(ys) - min(ys)) / 2 or 1.0
    norm = [[round((x - cx) / half, 4), round((y - cy) / half, 4)] for x, y in rs]
    w = (max(xs) - min(xs)); h = (max(ys) - min(ys))
    strokes.append({
        "id": c["id"],
        "norm": norm,
        "aspect": round(h / w, 3) if w else 1.0,
        "length_mm": c.get("length_mm"),
        "bbox_mm": [round(w, 2), round(h, 2)],
    })
    print(c["id"], "aspect", strokes[-1]["aspect"], "bbox_mm", strokes[-1]["bbox_mm"])

allx = [p[0] for s in strokes for p in s["norm"]]
ally = [p[1] for s in strokes for p in s["norm"]]
bbox = [round(min(allx), 3), round(min(ally), 3), round(max(allx), 3), round(max(ally), 3)]
print("combined norm bbox:", bbox)

# --- JS 片段 ---
js = ("  // 实测八字模板：来自真实蚕样本 G:\\raby model\\trajectories.json\n"
      "  // (curves3d/v2, worm 1, 2 笔 272 点, 标定 61.06 px/mm, cell 10mm)，弧长重采样后归一化到 [-1,1]\n"
      "  const WEAVE_MEASURED_PATHS = [\n")
for s in strokes:
    js += "    " + json.dumps([p for pt in s["norm"] for p in pt], separators=(",", ":")) + ",\n"
js += "  ];\n"
io.open(os.path.join(ROOT, "_backup", "raby_template.js"), "w", encoding="utf-8", newline="\n").write(js)
print("wrote _backup/raby_template.js")

# --- profile v1 ---
prof = {
    "schema": "silkworm-motion-profile/v1",
    "id": "raby-worm1",
    "label": "实测样本 raby-1（真实蚕吐丝）",
    "source": {
        "kind": "measured",
        "note": "人工描图自真实视频；标定 61.06 px/mm，cell 10mm；模板 2 笔，弧长重采样 56 点/笔",
        "origin": "G:\\raby model\\trajectories.json",
        "calibration": {"scalePxPerMm": d["calibration"]["scalePxPerMm"], "cell_mm": d["calibration"]["cell_mm"]},
    },
    "assumed": False,
    "calibrated": True,
    "fingerprint": {
        "loopsPerEnvelope": 1,
        "bbox": [round(strokes[0]["bbox_mm"][0], 2), round(strokes[0]["bbox_mm"][1], 2)],
        "strokeAspects": [s["aspect"] for s in strokes],
        "strokeLengths_mm": [s["length_mm"] for s in strokes],
        "turnHist": [0] * 36,
        "turnSignPersistence": 0,
        "pauseRate": 0.0,
        "radiusTyp": 0, "radiusMin": 0,
    },
    "pathTemplate": {"nPerStroke": N_PER, "strokes": [s["norm"] for s in strokes]},
    "shapeSource": "measured-template",
}
os.makedirs(os.path.join(ROOT, "profiles"), exist_ok=True)
io.open(os.path.join(ROOT, "profiles", "raby-worm1.json"), "w", encoding="utf-8", newline="\n").write(
    json.dumps(prof, ensure_ascii=False, indent=2) + "\n")
print("wrote profiles/raby-worm1.json")
