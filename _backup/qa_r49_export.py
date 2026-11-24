# -*- coding: utf-8 -*-
"""r49 P0-7 验收探针：导出与预览同源（时间 / 样式 / 无 uFloor）"""
import io, os, subprocess, re

ROOT = r'H:\tool\silkworm-trajectory'
SRC = ROOT + r'\docs\index.html'
TMP = r'C:\Users\54364\AppData\Local\Temp'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

src = io.open(SRC, encoding='utf-8').read()
TAG = r'''<script>window.__errs=[];window.addEventListener("error",function(e){__errs.push(e.message);});</script>'''

TEST = r'''<script>
window.addEventListener('load', function () {
  var H = window.__studioHabitat, out = document.getElementById('qaout');
  var L = [], log = function (s) { L.push(s); };
  setTimeout(function () {
    try {
      H.addWeave(); H.addWeave();
      var units = H.agents().filter(function (a) { return a.kind === 'weave'; });
      units[0].x = -110; units[0].y = 0; units[0].w = units[0].h = 190;
      units[1].x = 110; units[1].y = 0; units[1].w = units[1].h = 190;
      units.forEach(function (u) { H.buildWeave(u); });
      // 让两块几何完全一样，只差样式：A 更亮更粗
      units[0].seed = units[1].seed = 12345;
      units[0].coverage = units[1].coverage = 0.55;
      units[0].worms = units[1].worms = 6;
      units[0].style = { pathBoost: null, silkWidth: 1.8, silkGain: 2.2, silkMode: null };
      units[1].style = { pathBoost: null, silkWidth: 1, silkGain: 1, silkMode: null };
      H.buildWeave(units[0]); H.buildWeave(units[1]);
      // 顺序出场 + 速度 0.8 + 第二块织造时长 15 秒（截断）
      var t = H.timeline();
      t.mode = 'sequence'; t.interval = 2; t.speed = 0.8; t.rangeStart = 0; t.rangeEnd = null; t.tail = 3;
      units[1].duration = 15; units[1].shortMode = 'cut';
      H.refreshTimeline();

      var sc = H.ledScene();
      log('units=' + sc.units.length + ' first=' + JSON.stringify({ x: sc.units[0].x, y: sc.units[0].y, w: sc.units[0].w, h: sc.units[0].h }));
      log('range=' + JSON.stringify(sc.range));
      log('starts=' + sc.units.map(function (u) { return u.start; }).join(',') +
          ' effDur=' + sc.units.map(function (u) { return u.effDuration; }).join(',') +
          ' cap=' + sc.units.map(function (u) { return u.progressCap; }).join(','));
      log('styles_export=' + JSON.stringify(sc.units.map(function (u) { return u.style; })));

      var W = 1024, Hh = 768;
      var cv = document.createElement('canvas'); cv.width = W; cv.height = Hh;
      var g = cv.getContext('2d', { alpha: false });
      var cache = [];
      // 与 ledFrameView 同一套换算
      var minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
      sc.units.forEach(function (u) {
        minX = Math.min(minX, u.x - u.w / 2); maxX = Math.max(maxX, u.x + u.w / 2);
        minY = Math.min(minY, u.y - u.h / 2); maxY = Math.max(maxY, u.y + u.h / 2);
      });
      var bw = maxX - minX, bh = maxY - minY;
      var s = Math.min(W * 0.94 / bw, Hh * 0.94 / bh);
      var cxp = (minX + maxX) / 2, cyp = (minY + maxY) / 2;
      function lumAt(wx, wy) {
        var side = Math.round(190 * s * 0.92);
        var px = Math.round(W / 2 + (wx - cxp) * s - side / 2), py = Math.round(Hh / 2 + (wy - cyp) * s - side / 2);
        px = Math.max(0, Math.min(W - side - 1, px)); py = Math.max(0, Math.min(Hh - side - 1, py));
        var d = g.getImageData(px, py, side, side).data;
        var sum = 0, n = 0;
        for (var i = 0; i < d.length; i += 4) { sum += (d[i] + d[i + 1] + d[i + 2]) / 3; n++; }
        return sum / n;
      }
      var rs = sc.range, span = rs.end - rs.start;
      function frameAt(tAbs) { H.ledCompose(g, sc, (tAbs - rs.start) / span, false, W, Hh, cache); }

      frameAt(0);
      log('t0  A=' + lumAt(-110, 0).toFixed(2) + ' B=' + lumAt(110, 0).toFixed(2) + '（应为 ~0，旧版会 62% 满）');
      frameAt(28);
      var a28 = lumAt(-110, 0), b28 = lumAt(110, 0);
      var all = g.getImageData(0, 0, W, Hh).data, sumAll = 0;
      for (var q = 0; q < all.length; q += 4) sumAll += (all[q] + all[q + 1] + all[q + 2]) / 3;
      log('frame_mean=' + (sumAll / (all.length / 4)).toFixed(2) + ' at px(' + Math.round(W / 2 - 110 * s) + ',' + Math.round(Hh / 2) + ') s=' + s.toFixed(2));
      log('t28 A=' + a28.toFixed(2) + ' B=' + b28.toFixed(2) + ' A>B(' + (a28 > b28) + ') 样式差异生效(' + (a28 > b28 * 1.15) + ')');
      frameAt(14);
      var a14 = lumAt(-110, 0), b14 = lumAt(110, 0);
      log('t14 A=' + a14.toFixed(2) + ' B=' + b14.toFixed(2) + ' A>B(' + (a14 > b14) + ')');
      frameAt(rs.end);
      var aEnd = lumAt(-110, 0), bEnd = lumAt(110, 0);
      frameAt(rs.end - 0.5);
      var aEndp = lumAt(-110, 0);
      log('end A=' + aEnd.toFixed(2) + ' B=' + bEnd.toFixed(2) + ' 末端抖动=' + (Math.abs(aEnd - aEndp) / Math.max(1, aEnd) * 100).toFixed(2) + '%');
      log('cap命中(15/22=0.682): ' + (Math.abs(sc.units[1].progressCap - 0.682) < 0.002));
      log('jserrs=' + JSON.stringify(window.__errs));
      out.textContent = L.join('\n');
      out.setAttribute('done', '1');
    } catch (e) {
      out.textContent = 'ERR ' + e.message + '\n' + (e.stack || '');
      out.setAttribute('done', '1');
    }
  }, 800);
});
</script>
<div id="qaout" style="position:fixed;left:6px;top:6px;z-index:99999;background:#000;color:#8FF;font:12px monospace;padding:6px;white-space:pre-wrap">pending</div>'''

style = '<style>body > *:not(#habitat):not(script):not(style):not(#qaout){display:none !important}</style>'
h = src.replace('<head>', '<head>\n' + TAG, 1).replace('</head>', style + TEST + '</head>', 1)
tmp = os.path.join(TMP, 'qa-r49-export.html')
io.open(tmp, 'w', encoding='utf-8', newline='').write(h)

cmd = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
       '--disable-extensions', '--window-size=1400,900', '--virtual-time-budget=9000',
       '--dump-dom', 'file:///' + tmp.replace('\\', '/')]
r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=180)
m = re.search(r'<div id="qaout"[^>]*>([\s\S]*?)</div>', r.stdout)
print((m.group(1) if m else '(not found)').strip())
