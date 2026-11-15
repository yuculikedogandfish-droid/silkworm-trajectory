"""把 weave-curves.json 变成 Blender 可执行的导入脚本。

用法：
    python tools\\weave_to_blender.py exports\\weave-curves.json --out exports\\blender\\weave_import.py

在 Blender 里执行生成的 weave_import.py（Text Editor → Run Script，或
    blender --background --python exports\\blender\\weave_import.py
即可得到 SilkWeave 集合：每条丝一根 Curve（POLY，带 bevel），单位 m，原点在屏体中心。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

TEMPLATE = '''"""由 tools/weave_to_blender.py 生成 — 不要手改。

用法（任选）：
    Blender GUI：Text Editor 打开本文件 → Run Script
    命令行：blender --background --python "{script_name}"
依赖：weave-curves.json（同仓库 exports/ 下）。
"""

import json
import os

import bpy

JSON_PATH = r"{json_path}"
SCALE = 0.001              # mm → m
LAYER_GAP_MM = {layer_gap}  # 层间距，避免 z-fighting
BEVEL_RES = 2

data = json.load(open(JSON_PATH, encoding="utf-8"))
W = data["screen"]["widthMM"]
H = data["screen"]["heightMM"]

# 清掉上一次导入，保证可重复执行
old = bpy.data.collections.get("SilkWeave")
if old:
    for obj in list(old.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(old)
col = bpy.data.collections.new("SilkWeave")
bpy.context.scene.collection.children.link(col)

mat = bpy.data.materials.get("SilkEmission") or bpy.data.materials.new("SilkEmission")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.92, 0.96, 0.94, 1.0)
    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (0.85, 0.92, 0.88, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 0.6

made = 0
for c in data["curves"]:
    pts = c.get("points") or []
    if len(pts) < 2:
        continue
    cu = bpy.data.curves.new(name=c["id"], type="CURVE")
    cu.dimensions = "3D"
    cu.fill_mode = "FULL"
    cu.bevel_depth = max(0.0002, c["width_mm"] * SCALE * 0.5)
    cu.bevel_resolution = BEVEL_RES
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    z = (int(c["stratum"]) + 0.5) * LAYER_GAP_MM * SCALE
    for i, p in enumerate(pts):
        x = (p["x"] - W * 0.5) * SCALE
        y = -(p["y"] - H * 0.5) * SCALE
        sp.points[i].co = (x, y, z, 1.0)
        sp.points[i].radius = 1.0
    obj = bpy.data.objects.new(name=c["id"], object_data=cu)
    obj["cell"] = c["cell"]
    obj["stratum"] = int(c["stratum"])
    obj["worm"] = int(c["worm"])
    obj["length_mm"] = float(c.get("length_mm", 0))
    obj["coverage"] = float(c.get("coverage", 0))
    cu.materials.append(mat)
    col.objects.link(obj)
    made += 1

print("SilkWeave curves:", made, "of", len(data["curves"]))
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("curves", help="weave-curves.json")
    ap.add_argument("--out", default="exports/blender/weave_import.py")
    ap.add_argument("--layer-gap", type=float, default=0.35, help="层间距 mm")
    args = ap.parse_args()

    src = Path(args.curves)
    data = json.loads(src.read_text(encoding="utf-8"))
    if data.get("schema") != "silkworm-weave-curves/v1":
        raise SystemExit("不是 silkworm-weave-curves/v1：%s" % src)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    code = TEMPLATE.format(
        json_path=str(src.resolve()).replace("\\", "/"),
        layer_gap=args.layer_gap,
        script_name=out.name,
    )
    out.write_text(code, encoding="utf-8")

    total = sum(len(c["points"]) for c in data["curves"])
    print(f"curves={len(data['curves'])} points={total} -> {out}")


if __name__ == "__main__":
    main()
