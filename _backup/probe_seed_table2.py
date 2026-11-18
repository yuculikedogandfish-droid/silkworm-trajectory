# -*- coding: utf-8 -*-
"""多 seed 覆盖扫描（console 版）：结果 console.log 出来，chrome stderr 抓"""
import io

src = r'H:\tool\silkworm-trajectory\docs\index.html'
dst = r'C:\Users\54364\AppData\Local\Temp\qa-seeds2.html'

INJECT = r'''
<script>
window.addEventListener('load', function () {
  setTimeout(function () {
  try {
    var h = window.__studioHabitat;
    if (!h || !h.drawWeave) { console.log('SEEDTABLE_NO_HOOK'); return; }
    var A0 = h.agents();
    A0.length = 0;
    h.addWeave();
    var a = A0[0];
    a.coverage = 0.55;
    a.scaleK = 0.9;
    var seeds = [101, 202, 303, 404, 505, 606, 707, 808, 909, 1010, 1111, 1212];
    var rows = [];
    seeds.forEach(function (sd) {
      a.w = a.h = 300;
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
      var cc = h.weaveCellContent(a, 0, 0);
      var spec = cc.cell || null;
      var isl = (spec && (spec.islands || (spec.island ? [spec.island] : []))) || [];
      var notch = spec && spec.notch;
      var gap = spec && spec.gap != null ? spec.gap : 0;
      var data = g.getImageData(0, 0, N, N).data;
      var lit = 0, free = 0, holeAll = 0, holeLit = 0, bandAll = 0, bandLit = 0, o1 = 0, o2 = 0;
      var hw = (a.w - gap) / 2, hh = (a.h - gap) / 2;
      for (var y = 0; y < N; y++) {
        for (var x = 0; x < N; x++) {
          var wx = (x - N / 2) / s, wy = (y - N / 2) / s;
          var idx = (y * N + x) * 4;
          var lum = data[idx] + data[idx + 1] * 0.6 + data[idx + 2] * 0.3;
          var isLit = lum > 18;
          if (Math.abs(wx) > hw || Math.abs(wy) > hh) continue;
          var inHole = false, nearRim = false, far = false;
          for (var ii = 0; ii < isl.length; ii++) {
            var o = isl[ii];
            var d = Math.hypot(wx - o.cx, wy - o.cy);
            if (d < o.r) inHole = true;
            else if (d < o.r + a.w * 0.05) nearRim = true;
            else if (d < o.r + a.w * 0.16) far = true;
          }
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
      rows.push({
        seed: sd,
        threads: (cc.paths || []).length,
        points: (cc.paths || []).reduce(function (t, q) { return t + q.pts.length; }, 0),
        cov: free ? +(lit / free).toFixed(3) : 0,
        holeIn: holeAll ? +(holeLit / holeAll).toFixed(3) : 0,
        rim: (bandAll && o2) ? +((bandLit / bandAll) / (o1 / o2 || 1)).toFixed(2) : 0,
      });
    });
    var avgCov = rows.reduce(function (t, r) { return t + r.cov; }, 0) / rows.length;
    console.log('SEEDTABLE_START');
    rows.forEach(function (r) {
      console.log('SD ' + r.seed + ' threads=' + r.threads + ' pts=' + r.points +
        ' cov=' + r.cov + ' holeIn=' + r.holeIn + ' rim=' + r.rim);
    });
    console.log('SD_AVG cov=' + avgCov.toFixed(3));
    console.log('SEEDTABLE_END');
  } catch (e) {
    console.log('QAERR ' + e.message);
  }
  }, 1200);
});
</script>
'''

with io.open(src, 'r', encoding='utf-8') as f:
    s = f.read()
s = s.replace('</body>', INJECT + '</body>')
with io.open(dst, 'w', encoding='utf-8', newline='') as f:
    f.write(s)
print(dst)
