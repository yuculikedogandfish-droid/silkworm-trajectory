# -*- coding: utf-8 -*-
"""生成一个母版 native 渲染用的 QA 场景（结构同 led-scene.json），并拼出 URL。

用法：python _backup\make_led_qa_scene.py C:\Temp\qa-led-scene.json C:\Temp\qa-led-url.txt 1200 675 60 120
"""

import base64
import json
import math
import sys
from pathlib import Path


def build(w, h, frames, cols=4, rows=5):
    units = []
    tile = 200
    order = 0
    for j in range(rows):
        for i in range(cols):
            if (i + j) % 5 == 0 and order >= 1 and cols * rows > 4:
                continue
            units.append({
                "order": order,
                "x": (i - (cols - 1) / 2) * tile * 1.04,
                "y": (j - (rows - 1) / 2) * tile * 1.04,
                "w": tile,
                "h": tile,
                "coverage": 0.62,
                "shape": "island" if (i + j) % 3 else "notchIsland",
                "worms": 6,
                "seed": 20261116 + order * 977,
                "tone": 0.62 + (order % 7) * 0.06,
                "gap": 8,
                "strata": 2,
                "outline": None,
                "custom": {"walls": {}, "paths": {}, "shapes": {}},
            })
            order += 1
    xs, ys = [], []
    for u in units:
        xs.extend([u["x"] - u["w"] / 2, u["x"] + u["w"] / 2])
        ys.extend([u["y"] - u["h"] / 2, u["y"] + u["h"] / 2])
    bw, bh = max(xs) - min(xs), max(ys) - min(ys)
    s = min(w * 0.92 / bw, h * 0.92 / bh)
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    return {
        "schema": "silkworm-led-scene/v1",
        "createdAt": "2026-11-16T00:00:00.000Z",
        "px": {"w": w, "h": h},
        "fps": 30,
        "frames": frames,
        "scale": round(s, 6),
        "center": {"x": round(cx, 3), "y": round(cy, 3)},
        "source": {"silkPaths": "measured", "note": "QA 场景：4 列 × 5 行、缺 5 块"},
        "units": units,
    }


def main():
    dst = Path(sys.argv[1])
    urlpath = Path(sys.argv[2])
    w, h = int(sys.argv[3]), int(sys.argv[4])
    frame, total = int(sys.argv[5]), int(sys.argv[6])
    cols = int(sys.argv[7]) if len(sys.argv) > 7 else 4
    rows = int(sys.argv[8]) if len(sys.argv) > 8 else 5
    scene = build(w, h, total, cols, rows)
    dst.write_text(json.dumps(scene, ensure_ascii=False, indent=2), encoding="utf-8")
    raw = json.dumps(scene, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    token = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    html = (Path(__file__).resolve().parent.parent / "docs" / "index.html").as_uri()
    url = f"{html}?native=1&frame={frame}&total={total}&w={w}&h={h}&scene={token}"
    urlpath.write_text(url, encoding="utf-8")
    print(f"scene {dst.stat().st_size} B, url {len(url)} chars, units {len(scene['units'])}")


if __name__ == "__main__":
    main()
