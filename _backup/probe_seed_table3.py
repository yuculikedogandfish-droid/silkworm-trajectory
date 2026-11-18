# -*- coding: utf-8 -*-
"""多 seed 扫描：覆盖率 + 一格几份吐丝（1 份 = 70.42 mm = 7.042 格宽）"""
import subprocess, os, tempfile, re, json
HTML = r"H:\tool\silkworm-trajectory\docs\index.html"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
JS = r"""
<script>
window.addEventListener('load', function () {
  setTimeout(function () {
    var out = [];
    var put = function (o) {
      var d = document.getElementById('QAOUT');
      if (!d) { d = document.createElement('div'); d.id = 'QAOUT'; document.body.appendChild(d); }
      d.textContent = JSON.stringify(o);
    };
    try {
      var h = window.__studioHabitat;
      if (!h || !h.drawWeave) { put({ err: 'no hook' }); return; }
      var A0 = h.agents(); A0.length = 0;
      h.addWeave();
      var a = A0[0];
      a.coverage = 0.55;
      a.scaleK = 0.9;
      var PASS_GRID = 7.042;   // 一次吐丝 70.42 mm，格宽 10 mm
      var seeds = [101, 202, 303, 404, 505, 606, 707, 808, 909, 1010, 1111, 1212];
      seeds.forEach(function (sd) {
        a.w = a.h = 300; a.seed = sd >>> 0; a.cache = new Map();
        h.buildWeave(a); a.u = 1;
        var N = 420;
        var cv = document.createElement('canvas');
        cv.width = N; cv.height = N;
        var g = cv.getContext('2d');
        g.fillStyle = '#000'; g.fillRect(0, 0, N, N);
        var s = N / a.w;
        var v = { w: N, h: N, s: s, cx: N / 2, cy: N / 2,
          px: function (x) { return N / 2 + x * s; }, py: function (y) { return N / 2 + y * s; } };
        h.drawWeave(g, a, v);
        var cc = h.weaveCellContent(a, 0, 0);
        var spec = cc.cell || null;
        var isl = (spec && (spec.islands || (spec.island ? [spec.island] : []))) || [];
        var notch = spec && spec.notch;
        var gap = spec && spec.gap != null ? spec.gap : 0;
        // 丝长（格宽为单位）
        var lenW = 0, pts = 0;
        (cc.paths || []).forEach(function (p) {
          var q = p.pts || [];
          pts += q.length;
          for (var i = 1; i < q.length; i++) lenW += Math.hypot(q[i].x - q[i-1].x, q[i].y - q[i-1].y);
        });
        lenW = lenW / a.w;
        var data = g.getImageData(0, 0, N, N).data;
        var lit = 0, free = 0, holeAll = 0, holeLit = 0;
        var hw = (a.w - gap) / 2, hh = (a.h - gap) / 2;
        for (var y = 0; y < N; y++) {
          for (var x = 0; x < N; x++) {
            var wx = (x - N / 2) / s, wy = (y - N / 2) / s;
            if (Math.abs(wx) > hw || Math.abs(wy) > hh) continue;
            var idx = (y * N + x) * 4;
            var lum = data[idx] + data[idx + 1] * 0.6 + data[idx + 2] * 0.3;
            var isLit = lum > 18;
            var inHole = false;
            for (var ii = 0; ii < isl.length; ii++) {
              if (Math.hypot(wx - isl[ii].cx, wy - isl[ii].cy) < isl[ii].r) inHole = true;
            }
            if (notch && Math.hypot(wx - notch.cx, wy - notch.cy) < notch.r) inHole = true;
            if (inHole) { holeAll++; if (isLit) holeLit++; continue; }
            free++; if (isLit) lit++;
          }
        }
        out.push({ seed: sd, threads: (cc.paths || []).length, pts: pts,
          cov: free ? +(lit / free).toFixed(3) : 0,
          lenW: +lenW.toFixed(1), passes: +(lenW / PASS_GRID).toFixed(1),
          holeIn: holeAll ? +(holeLit / holeAll).toFixed(3) : 0 });
      });
      var avgCov = out.reduce(function (t, r) { return t + r.cov; }, 0) / out.length;
      var avgPass = out.reduce(function (t, r) { return t + r.passes; }, 0) / out.length;
      put({ rows: out, avgCov: +avgCov.toFixed(3), avgPass: +avgPass.toFixed(1) });
    } catch (e) { put({ err: String(e) }); }
  }, 1200);
});
</script>
"""
with open(HTML, 'r', encoding='utf-8') as f:
    s = f.read()
s = s.replace('</body>', JS + '</body>')
tmp = os.path.join(tempfile.gettempdir(), 'qa-seeds3.html')
open(tmp, 'w', encoding='utf-8').write(s)
r = subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--window-size=1400,1000',
                    '--virtual-time-budget=20000', '--dump-dom', 'file:///' + tmp.replace('\\', '/')],
                   capture_output=True, text=True, timeout=180)
m = re.search(r'id="QAOUT">(.*?)</div>', r.stdout, re.S)
if not m:
    print("NO OUT")
else:
    d = json.loads(m.group(1))
    if 'err' in d:
        print(d)
    else:
        for row in d['rows']:
            print(row)
        print('AVG cov=%s passes=%s' % (d['avgCov'], d['avgPass']))
