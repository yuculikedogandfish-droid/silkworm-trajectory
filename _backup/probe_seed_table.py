# -*- coding: utf-8 -*-
"""多 seed 覆盖扫描：12 个 seed 逐块渲染，算「自由区覆盖 / 孔内残留 / 孔缘比值」，
结果写进 <pre id="out">，用 chrome --dump-dom 读回。"""
import io, json

src = r'H:\tool\silkworm-trajectory\docs\index.html'
dst = r'C:\Users\54364\AppData\Local\Temp\qa-seeds.html'

INJECT = r'''
<script>
window.addEventListener('load', function () {
  var out = document.createElement('pre');
  out.id = 'out';
  document.body.appendChild(out);
  try {
    var h = window.__studioHabitat;
    if (!h || !h.drawWeave) { out.textContent = 'NOHOOK'; return; }
    h.agents.length = 0;
    h.addWeave();
    var a = h.agents[0];
    a.w = a.h = 300;
    a.coverage = 0.55;
    a.scaleK = 0.9;
    var seeds = [101, 202, 303, 404, 505, 606, 707, 808, 909, 1010, 1111, 1212];
    var rows = [];
    seeds.forEach(function (sd) {
      a.seed = sd >>> 0;
      a.cache = new Map();
      h.buildWeave(a);
      a.u = 1;
      var cv = document.createElement('canvas');
      var N = 420;
      cv.width = N; cv.height = N;
      var g = cv.getContext('2d');
      g.fillStyle = '#000'; g.fillRect(0, 0, N, N);
      var s = N / a.w;
      var v = {
        w: N, h: N, s: s, cx: N / 2, cy: N / 2,
        px: function (x) { return N / 2 + x * s; },
        py: function (y) { return N / 2 + y * s; },
      };
      h.drawWeave(g, a, v);
      var spec = h.weaveCellSpecAt ? h.weaveCellSpecAt(a, 0, 0) : null;
      var cellRect = { w: a.w, h: a.h, gap: spec && spec.gap != null ? spec.gap : 0 };
      var isl = (spec && (spec.islands || (spec.island ? [spec.island] : []))) || [];
      var notch = spec && spec.notch;
      var data = g.getImageData(0, 0, N, N).data;
      var lit = 0, free = 0, holeAll = 0, holeLit = 0, bandAll = 0, bandLit = 0, o1 = 0, o2 = 0;
      var hw = (a.w - cellRect.gap) / 2, hh = (a.h - cellRect.gap) / 2;
      for (var y = 0; y < N; y++) {
        for (var x = 0; x < N; x++) {
          var wx = (x - N / 2) / s, wy = (y - N / 2) / s;
          var lum = data[(y * N + x) * 4] + data[(y * N + x) * 4 + 1] * 0.6 + data[(y * N + x) * 4 + 2] * 0.3;
          var isLit = lum > 18;
          if (Math.abs(wx) > hw || Math.abs(wy) > hh) continue;
          var inHole = false, nearRim = false, far = false;
          isl.forEach(function (o) {
            var d = Math.hypot(wx - o.cx, wy - o.cy);
            if (d < o.r) inHole = true;
            else if (d < o.r + a.w * 0.05) nearRim = true;
            else if (d < o.r + a.w * 0.16) far = true;
          });
          if (notch) {
            var dn = Math.hypot(wx - notch.cx, wy - notch.cy);
            if (dn < notch.r) inHole = true;
            else if (dn < notch.r + a.w * 0.05) nearRim = true;
            else if (dn < notch.r + a.w * 0.16) far = true;
          }
          if (inHole) { holeAll++; if (isLit) holeLit++; continue; }
          free++; if (isLit) lit++;
          if (nearRim) { bandAll++; if (isLit) bandLit++; }
          if (far) { o2++; if (isLit) o1++; }
        }
      }
      var res = {
        seed: sd,
        threads: a.paths.length,
        points: a.paths.reduce(function (t, p) { return t + p.pts.length; }, 0),
        cov: free ? +(lit / free).toFixed(3) : 0,
        hole_in: holeAll ? +(holeLit / holeAll).toFixed(3) : 0,
        rim: (bandAll && o2) ? +((bandLit / bandAll) / (o1 / o2 || 1)).toFixed(2) : 0,
        freeArea: free,
        holeArea: holeAll,
      };
      rows.push(res);
    });
    out.textContent = 'SEEDTABLE' + JSON.stringify(rows);
    // 把表格画成图（本机 headless 拿不到 dump-dom 的 stdout，用截图读）
    var tc = document.createElement('canvas');
    tc.width = 840; tc.height = 470;
    tc.style.cssText = 'position:fixed;left:0;top:0;width:840px;height:470px;background:#000';
    document.body.innerHTML = '';
    document.body.appendChild(tc);
    var tg = tc.getContext('2d');
    tg.fillStyle = '#000'; tg.fillRect(0, 0, 840, 470);
    tg.fillStyle = '#e8eee9'; tg.font = '15px Consolas, monospace';
    tg.fillText('seed   threads  points  cov    holeIn  rimX', 16, 26);
    rows.forEach(function (r, i) {
      tg.fillText(String(r.seed).padEnd(7) + String(r.threads).padEnd(9) + String(r.points).padEnd(8) +
        String(r.cov).padEnd(7) + String(r.hole_in).padEnd(8) + String(r.rim), 16, 52 + i * 26);
    });
    var avg = rows.reduce(function (t, r) { return t + r.cov; }, 0) / rows.length;
    tg.fillStyle = '#f0b45a';
    tg.fillText('avg cov ' + avg.toFixed(3), 16, 440);
  } catch (e) {
    out.textContent = 'QAERR ' + e.message;
  }
});
</script>
'''

with io.open(src, 'r', encoding='utf-8') as f:
    s = f.read()
s = s.replace('</body>', INJECT + '</body>')
with io.open(dst, 'w', encoding='utf-8', newline='') as f:
    f.write(s)
print(dst)
