# -*- coding: utf-8 -*-
"""r49 按钮级验收：真的点「导出当前画面 PNG」和「导出母版场景 JSON」"""
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
  var step = function (fn, ms) { return new Promise(function (res) { setTimeout(function () { fn(); res(); }, ms); }); };

  setTimeout(async function () {
    try {
      H.addWeave(); H.addWeave();
      var units = H.agents().filter(function (a) { return a.kind === 'weave'; });
      units[0].x = -110; units[0].y = 0; units[0].w = units[0].h = 190;
      units[1].x = 110; units[1].y = 0; units[1].w = units[1].h = 190;
      units.forEach(function (u) { u.seed = 12345; u.coverage = 0.55; u.worms = 6; });
      units[0].style = { pathBoost: null, silkWidth: 1.8, silkGain: 2.2, silkMode: null };
      units[1].style = { pathBoost: null, silkWidth: 1, silkGain: 1, silkMode: null };
      units.forEach(function (u) { H.buildWeave(u); });
      var t = H.timeline();
      t.mode = 'sequence'; t.interval = 2; t.speed = 0.8; t.rangeStart = 0; t.rangeEnd = null; t.tail = 3;
      H.refreshTimeline();
      H.seekTo(14);

      // 拦 toBlob，拿到导出用的那张 canvas（真实点击按钮触发）
      var origToBlob = HTMLCanvasElement.prototype.toBlob;
      HTMLCanvasElement.prototype.toBlob = function (cb, type) {
        window.__last = this; return origToBlob.call(this, cb, type);
      };
      document.getElementById('habImgExport').click();
      await step(function () {}, 500);

      var cv = window.__last;
      if (!cv) { log('PNG: 没有 canvas 被导出'); }
      else {
        var W = cv.width, Hh = cv.height, g = cv.getContext('2d');
        var sc = H.ledScene();
        var minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
        sc.units.forEach(function (u) {
          minX = Math.min(minX, u.x - u.w / 2); maxX = Math.max(maxX, u.x + u.w / 2);
          minY = Math.min(minY, u.y - u.h / 2); maxY = Math.max(maxY, u.y + u.h / 2);
        });
        var s = Math.min(W * 0.94 / (maxX - minX), Hh * 0.94 / (maxY - minY));
        var cxp = (minX + maxX) / 2, cyp = (minY + maxY) / 2;
        var side = Math.round(190 * s * 0.92);
        function lum(wx) {
          var px = Math.round(W / 2 + (wx - cxp) * s - side / 2), py = Math.round(Hh / 2 + (0 - cyp) * s - side / 2);
          px = Math.max(0, Math.min(W - side - 1, px)); py = Math.max(0, Math.min(Hh - side - 1, py));
          var d = g.getImageData(px, py, side, side).data, sum = 0, n = 0;
          for (var i = 0; i < d.length; i += 4) { sum += (d[i] + d[i + 1] + d[i + 2]) / 3; n++; }
          return sum / n;
        }
        var a = lum(-110), b = lum(110);
        // 没有 letterbox：四角必须是画过的画面（不是纯黑遮罩）
        var corners = [lum(-110), lum(110)];
        log('PNG size=' + W + 'x' + Hh + ' (应为 2048×1536)');
        log('PNG t14 A=' + a.toFixed(2) + ' B=' + b.toFixed(2) + ' A>B(' + (a > b) + ') A/B=' + (a / Math.max(0.01, b)).toFixed(2));
        log('PNG 顶部 6px 亮度(应≈0 黑场)=' + (function () {
          var d = g.getImageData(0, 0, W, 6).data, su = 0, nn = 0;
          for (var i = 0; i < d.length; i += 4) { su += (d[i] + d[i + 1] + d[i + 2]) / 3; nn++; }
          return (su / nn).toFixed(2);
        })());
      }

      // 拦 createObjectURL，读回母版场景 JSON
      var origURL = URL.createObjectURL;
      URL.createObjectURL = function (blob) { window.__blob = blob; return origURL.call(URL, blob); };
      document.getElementById('habLedScene').click();
      await step(function () {}, 400);
      if (!window.__blob) { log('场景 JSON: 没抓到 blob'); }
      else {
        var txt = await window.__blob.text();
        var j = JSON.parse(txt);
        log('scene range=' + JSON.stringify(j.range) + ' timeline.speed=' + (j.timeline && j.timeline.speed) +
            ' mode=' + (j.timeline && j.timeline.mode));
        log('scene starts=' + j.units.map(function (u) { return u.start; }).join(',') +
            ' caps=' + j.units.map(function (u) { return u.progressCap; }).join(',') +
            ' styleA.width=' + j.units[0].style.silkWidth);
      }
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
<div id="qaout" style="position:fixed;left:6px;top:6px;z-index:99999;background:#000;color:#9FE;font:12px monospace;padding:6px;white-space:pre-wrap">pending</div>'''

style = '<style>body > *:not(#habitat):not(script):not(style):not(#qaout){display:none !important}</style>'
h = src.replace('<head>', '<head>\n' + TAG, 1).replace('</head>', style + TEST + '</head>', 1)
tmp = os.path.join(TMP, 'qa-r49-buttons.html')
io.open(tmp, 'w', encoding='utf-8', newline='').write(h)

cmd = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
       '--disable-extensions', '--window-size=1400,900', '--virtual-time-budget=12000',
       '--dump-dom', 'file:///' + tmp.replace('\\', '/')]
r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=240)
m = re.search(r'<div id="qaout"[^>]*>([\s\S]*?)</div>', r.stdout)
print((m.group(1) if m else '(not found)').strip())
