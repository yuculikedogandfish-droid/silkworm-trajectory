import json, io
p = r"G:\raby model\trajectories.json"
d = json.load(io.open(p, encoding="utf-8"))
curves = d["curves3d"]
print("fps", d.get("fps"), "curves", len(curves))
worms = {}
for c in curves:
    wid = c.get("wormId")
    pts = c.get("points") or c.get("points3d") or []
    worms.setdefault(wid, []).append((c.get("strokeIndex"), len(pts), c.get("durationSec", c.get("duration"))))
for w, lst in sorted(worms.items()):
    total = sum(n for _, n, _ in lst)
    print("worm", w, "strokes", len(lst), "points", total, "durs", [x[2] for x in lst])
# sample point structure
c0 = curves[0]
print("curve keys:", list(c0.keys()))
pk = [k for k in c0.keys() if "point" in k.lower()]
print("point-ish keys:", pk)
for k in pk:
    v = c0[k]
    if isinstance(v, list) and v:
        print(k, "len", len(v), "first", v[0] if not isinstance(v[0], list) else v[0])
# bbox in mm of all points
xs, ys, zs = [], [], []
for c in curves:
    for k in ("points", "points3d", "pointsMm"):
        pts = c.get(k)
        if pts:
            for q in pts:
                if isinstance(q, dict):
                    xs.append(q.get("x_mm", q.get("x", 0))); ys.append(q.get("y_mm", q.get("y", 0))); zs.append(q.get("z_mm", q.get("z", 0)))
                elif isinstance(q, list):
                    xs.append(q[0]); ys.append(q[1]); zs.append(q[2] if len(q) > 2 else 0)
            break
if xs:
    print("bbox mm x", min(xs), max(xs), "y", min(ys), max(ys), "z", min(zs), max(zs))
