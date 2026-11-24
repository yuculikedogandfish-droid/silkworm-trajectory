# -*- coding: utf-8 -*-
"""r49 视频导出：用假 MediaRecorder 验证「帧数 = 区间长度 × fps」与首末帧映射"""
import io, os, subprocess, re

ROOT = r'H:\tool\silkworm-trajectory'
SRC = ROOT + r'\docs\index.html'
TMP = r'C:\Users\54364\AppData\Local\Temp'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

src = io.open(SRC, encoding='utf-8').read()
TAG = r'''<script>window.__errs=[];window.__statusHist=[];window.addEventListener("error",function(e){__errs.push(e.message);});</script>'''

TEST = r'''<script>
window.addEventListener('load', function () {
  var H = window.__studioHabitat, out = document.getElementById('qaout');
  var L = [], log = function (s) { L.push(s); };

  // 假 MediaRecorder：只记录 start/stop，不做编码
  var recLog = { start: 0, stop: 0 };
  window.MediaRecorder = function (stream, opts) {
    var self = this;
    this.stream = stream; this.opts = opts;
    this.start = function () { recLog.start++; };
    this.stop = function () { recLog.stop++; if (self.onstop) self.onstop(); };
  };
  window.MediaRecorder.isTypeSupported = function () { return false; };
  // 抓最后创建的那张 canvas（录制用的离屏画布）
  var origCreate = document.createElement.bind(document);
  document.createElement = function (tag) {
    var el = origCreate(tag);
    return el;
  };
  // headless 的 rAF 触发次数远低于真实浏览器，无法用 24fps 对账；
  // 改成 fps=6 的等价小样本（每 tick 推进 1/6 s），验证「帧数 = 区间 × fps」与末帧不越界。
  var vt = 0, stepMs = 1000 / 6;
  performance.now = function () { return vt; };
  window.requestAnimationFrame = function (cb) {
    return setTimeout(function () { vt += stepMs; cb(vt); }, 0);
  };

  // 逐帧计数：ledComposeFrame 每帧都以 #000 铺一次整幅（fillRect(0,0,W,H)）
  window.__frames = 0;
  var origFill = CanvasRenderingContext2D.prototype.fillRect;
  CanvasRenderingContext2D.prototype.fillRect = function (x, y, w, h) {
    if (w >= 320 && h >= 240 && this.canvas && w === this.canvas.width && h === this.canvas.height) {
      window.__frames++; window.__recCv = this.canvas;
    }
    return origFill.apply(this, arguments);
  };

  var step = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };

  setTimeout(async function () {
    try {
      H.addWeave(); H.addWeave();
      var units = H.agents().filter(function (a) { return a.kind === 'weave'; });
      units[0].x = -110; units[0].y = 0; units[0].w = units[0].h = 190;
      units[1].x = 110; units[1].y = 0; units[1].w = units[1].h = 190;
      units.forEach(function (u) { u.seed = 999; u.coverage = 0.55; u.worms = 6; H.buildWeave(u); });
      units[0].style = { pathBoost: null, silkWidth: 1.8, silkGain: 2.2, silkMode: null };

      // 锁定 0→4 s，fps 24，低分辨率，避免真等 32 秒
      var t = H.timeline();
      t.mode = 'sequence'; t.interval = 2; t.speed = 0.8; t.rangeStart = 0; t.rangeEnd = 4; t.tail = 3;
      H.refreshTimeline();
      document.getElementById('habVidRes').value = '854x480';
      document.getElementById('habVidFps').value = '6';

      var sc = H.ledScene();
      log('scene.range=' + JSON.stringify(sc.range) + ' 期望帧数=round((end-start)*6)=' +
          Math.max(2, Math.round((sc.range.end - sc.range.start) * 6)));

      document.getElementById('habVidRecord').click();
      // 等录制结束（按钮文案恢复）
      var btn = document.getElementById('habVidRecord');
      for (var i = 0; i < 100; i++) {
        await step(150);
        if (btn && btn.textContent.indexOf('录制中') < 0 && recLog.stop > 0) break;
      }
      log('recorder start=' + recLog.start + ' stop=' + recLog.stop);
      log('status 末尾=' + (document.getElementById('habVidStatus').textContent || '(空)'));
      log('逐帧计数 __frames=' + window.__frames + '（含首帧，期望 25 = 1 + 4s×6fps）');
      log('btn=' + (btn ? btn.textContent : '(none)'));

      // 录制画布：按 854 宽筛，避开 512 的位图缓存画布
      var cvs = Array.prototype.slice.call(document.querySelectorAll('canvas'));
      var cv = window.__recCv || cvs.filter(function (c) { return c.width === 854; })[0];
      if (cv) {
        log('canvas=' + cv.width + 'x' + cv.height);
        var g = cv.getContext('2d');
        // 末帧：单位 1 应织满（区间 4s，速度 0.8 → 有效 27.5s，只织了 14.5%）
        var W = cv.width, Hh = cv.height;
        var minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
        sc.units.forEach(function (u) {
          minX = Math.min(minX, u.x - u.w / 2); maxX = Math.max(maxX, u.x + u.w / 2);
          minY = Math.min(minY, u.y - u.h / 2); maxY = Math.max(maxY, u.y + u.h / 2);
        });
        var s = Math.min(W * 0.94 / (maxX - minX), Hh * 0.94 / (maxY - minY));
        var cxp = (minX + maxX) / 2, cyp = (minY + maxY) / 2;
        var px = Math.round(W / 2 + (-110 - cxp) * s), py = Math.round(Hh / 2 - cyp * s);
        var side = Math.round(190 * s * 0.92);
        px = Math.max(0, Math.min(W - side - 1, px)); py = Math.max(0, Math.min(Hh - side - 1, py));
        var d = g.getImageData(px, py, side, side).data, su = 0, nn = 0;
        for (var q = 0; q < d.length; q += 4) { su += (d[q] + d[q + 1] + d[q + 2]) / 3; nn++; }
        log('末帧 A 区域亮度=' + (su / nn).toFixed(2) + '（4s/27.5s≈14.5% 进度，应明显低于织满）');
      } else log('没抓到录制画布');

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
<div id="qaout" style="position:fixed;left:6px;top:6px;z-index:99999;background:#000;color:#BF8;font:12px monospace;padding:6px;white-space:pre-wrap">pending</div>'''

style = '<style>body > *:not(#habitat):not(script):not(style):not(#qaout){display:none !important}</style>'
h = src.replace('<head>', '<head>\n' + TAG, 1).replace('</head>', style + TEST + '</head>', 1)
tmp = os.path.join(TMP, 'qa-r49-webm.html')
io.open(tmp, 'w', encoding='utf-8', newline='').write(h)

cmd = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
       '--disable-extensions', '--window-size=1400,900', '--virtual-time-budget=25000',
       '--dump-dom', 'file:///' + tmp.replace('\\', '/')]
r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=300)
m = re.search(r'<div id="qaout"[^>]*>([\s\S]*?)</div>', r.stdout)
print((m.group(1) if m else '(not found)').strip())
