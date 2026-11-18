import io
p=r"_backup\r43_module.js"
s=io.open(p,encoding="utf-8").read()
s=s.replace("      const dm = new Uint8Array(W * H2);\n      for (let y = 0; y < H2; y++) for (let x = 0; x < W; x++) dm[y * W + x] = mask[(y0 + y) * w + (x0 + x)] ? 0 : 1;",
"""      // 孔洞用"糊过的灰度"判定：丝线本身的细缝不会被当成洞
      const holeThr = Math.max(18, glob * 0.55);
      const dm = new Uint8Array(W * H2);
      for (let y = 0; y < H2; y++) for (let x = 0; x < W; x++) dm[y * W + x] = bg[(y0 + y) * w + (x0 + x)] < holeThr ? 1 : 0;""")
s=s.replace("        } else if (wantNotch) {","        } else if (wantNotch && circ >= 0.38) {")
s=s.replace("          b.polys.push({ pts: world });","          b.polys.push({ pts: world, area: cnt });")
s=s.replace("""      boxes.push(b);
      if (!b.present || (!wantHoles && !wantNotch)) return;""",
"""      boxes.push(b);
      if (!b.present || (!wantHoles && !wantNotch)) return;
      b.polys = [];""")
s=s.replace("""          b.polys.push({ pts: world, area: cnt });
          polyN++;""",
"""          b.polys.push({ pts: world, area: cnt });""")
# 每块只保留面积最大的 2 条轮廓，并统计
s=s.replace("""    state.boxes = boxes;
    state.holes = holes;""",
"""    boxes.forEach(b => {
      if (b.polys && b.polys.length > 2) b.polys = b.polys.sort((p, q) => q.area - p.area).slice(0, 2);
      polyN += (b.polys || []).length;
    });
    state.boxes = boxes;
    state.holes = holes;""")
s=s.replace("        const poly = b.polys.slice().sort((p, q) => q.pts.length - p.pts.length)[0];","        const poly = b.polys.slice().sort((p, q) => (q.area || 0) - (p.area || 0))[0];")
io.open(p,"w",encoding="utf-8").write(s)
print("holes smooth ok")
