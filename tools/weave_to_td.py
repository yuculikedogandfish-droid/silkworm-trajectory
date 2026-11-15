"""把 weave-curves.json 变成 TouchDesigner 可用的两种入口：
  1) Script SOP 代码（贴进 Script SOP 的 onCook），直接生成折线几何；
  2) 顶点表 CSV（按 DAT → Add SOP / Script SOP 读取，做逐点动画或着色）。

用法：
    python tools\\weave_to_td.py exports\\weave-curves.json --out exports\\td
产物：
    weave_td_script_sop.py   Script SOP 代码（单位 m，原点在屏体中心，z=层）
    weave_td_points.csv      每行一个顶点，带 cell/stratum/worm/u/width_mm
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

SCRIPT = '''"""由 tools/weave_to_td.py 生成 — 贴进 Script SOP 的 onCook 里。

TouchDesigner 侧步骤：
1. 新建 Script SOP，打开其 script DAT；
2. 用本文件覆盖 script DAT 内容；
3. 把 JSON_PATH 改成实际路径（建议放项目内绝对路径）；
4. 需要逐条曲线做动画时，给每条 poly 打 Primitive 属性 cell/stratum/worm（见下方注释）。
"""

import json

JSON_PATH = r"{json_path}"
SCALE = 0.001              # mm → m
LAYER_GAP = {layer_gap}     # 层间距（m）


def cook(scriptOp):
    scriptOp.clear()
    data = json.load(open(JSON_PATH, encoding="utf-8"))
    W = data["screen"]["widthMM"]
    H = data["screen"]["heightMM"]

    for c in data["curves"]:
        pts = c.get("points") or []
        if len(pts) < 2:
            continue
        poly = scriptOp.appendPoly(len(pts), closed=False, addPoints=True)
        z = (int(c["stratum"]) + 0.5) * LAYER_GAP
        for i, p in enumerate(pts):
            pnt = poly[i].point
            pnt.x = (p["x"] - W * 0.5) * SCALE
            pnt.y = -(p["y"] - H * 0.5) * SCALE
            pnt.z = z
        # 逐条属性（TD 里可用 Select SOP 按属性筛选）：
        # poly.setAttribute("cell", c["cell"]) 等 API 依版本而异，先保留注释

    return
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("curves", help="weave-curves.json")
    ap.add_argument("--out", default="exports/td")
    ap.add_argument("--layer-gap", type=float, default=0.00035, help="层间距 m（默认 0.35mm）")
    args = ap.parse_args()

    src = Path(args.curves)
    data = json.loads(src.read_text(encoding="utf-8"))
    if data.get("schema") != "silkworm-weave-curves/v1":
        raise SystemExit("不是 silkworm-weave-curves/v1：%s" % src)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    script_path = out / "weave_td_script_sop.py"
    script_path.write_text(
        SCRIPT.format(json_path=str(src.resolve()).replace("\\", "/"), layer_gap=args.layer_gap),
        encoding="utf-8",
    )

    W = data["screen"]["widthMM"]
    H = data["screen"]["heightMM"]
    rows = 0
    with (out / "weave_td_points.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["tx", "ty", "tz", "cell", "stratum", "worm", "idx", "u", "width_mm", "curve_id"])
        for c in data["curves"]:
            for i, p in enumerate(c.get("points") or []):
                w.writerow([
                    round((p["x"] - W * 0.5) * 0.001, 6),
                    round(-(p["y"] - H * 0.5) * 0.001, 6),
                    round((int(c["stratum"]) + 0.5) * args.layer_gap, 6),
                    c["cell"], c["stratum"], c["worm"], i,
                    round(float(p.get("u", 0)), 5),
                    c["width_mm"], c["id"],
                ])
                rows += 1

    print(f"script -> {script_path}")
    print(f"points -> {out / 'weave_td_points.csv'} ({rows} rows)")


if __name__ == "__main__":
    main()
