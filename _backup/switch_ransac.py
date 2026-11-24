from pathlib import Path
import shutil
p = Path(r'H:\tool\silkworm-trajectory\_backup\r43_module.js')
shutil.copy2(p, p.with_name('r48_before_ransac.js'))
s = p.read_text(encoding='utf-8')
a = s.index('      const circles = distanceCircles(')
b = s.index('      b.outline = modelOutline(', a)
new = '''      const rc = ransacCircles(localGray, W, H2, localThr, minHoleFrac);
      b.islands = [];
      b.polys = [];
      rc.forEach(c => {
        const pts = [];
        for (let k = 0; k < 64; k++) {
          const ang = k * Math.PI * 2 / 64;
          pts.push({ x: (c.cx + Math.cos(ang) * c.r - W / 2) * scale, y: (c.cy + Math.sin(ang) * c.r - H2 / 2) * scale });
        }
        if (c.full) {
          if (!wantHoles) return;
          const isl = { cx: (c.cx - W / 2) * scale, cy: (c.cy - H2 / 2) * scale, r: c.r * scale };
          b.islands.push(isl);
          holes.push({ wx: b.wx + isl.cx, wy: b.wy + isl.cy, wr: isl.r });
          holeN++;
        } else if (wantNotch) {
          b.polys.push({ pts, area: Math.PI * c.r * c.r });
        }
      });
'''
p.write_text(s[:a] + new + s[b:], encoding='utf-8', newline='')
print('switched to ransac', a, b)
