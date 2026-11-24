# -*- coding: utf-8 -*-
"""r49g 验收：成品无白点 / 丝线不发绿 / 手描线自动平滑 / 默认 0.2×"""
import io, os, subprocess, re, base64, math
ROOT = r'H:\tool\silkworm-trajectory'
SRC = ROOT + r'\docs\index.html'
TMP = r'C:\Users\54364\AppData\Local\Temp'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
src = io.open(SRC, encoding='utf-8').read()
TEST = r'''<script>
window.addEventListener('load', function () {
  var H = window.__studioHabitat, out = document.getElementById('qaout');
  var L = [], log = function (s) { L.push(s); };
  var step = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
  setTimeout(async function () {
    try {
      /* ---------- ① 成品帧：只有丝线，没有白点 ---------- */
      log('=== ① 成品帧里不该有吐丝头白点 ===');
      H.addWeave();
      await step(300);
      var A = H.agents().filter(function (a) { return a.kind === 'weave'; })[0];
      A.duration = 22; A.speedScale = 1; A.schedule = { order: 0, manualStart: 0 };
      H.buildWeave(A);
      var early = H.framePng(480, 480, 0.30);   // u≈0.3：正在织，最容易看到"头"
      log('composed@0.30 png=' + early.length + ' chars');
      log('__PNG_EARLY__' + early);

      /* ---------- ② 丝线颜色（低亮度 / 哑光 / 墨色）都不能偏绿 ---------- */
      log('=== ② 低亮度与低亮材质的色偏 ===');
      function chanStats(url) {
        return new Promise(function (res) {
          var im = new Image();
          im.onload = function () {
            var c = document.createElement('canvas');
            c.width = im.width; c.height = im.height;
            var g = c.getContext('2d');
            g.drawImage(im, 0, 0);
            var d = g.getImageData(0, 0, c.width, c.height).data;
            var r = 0, gg = 0, b = 0, n = 0;
            for (var i = 0; i < d.length; i += 4) {
              var lum = (d[i] + d[i + 1] + d[i + 2]) / 3;
              if (lum > 40) { r += d[i]; gg += d[i + 1]; b += d[i + 2]; n++; }
            }
            res(n ? { r: Math.round(r / n), g: Math.round(gg / n), b: Math.round(b / n), n: n }
                  : { r: 0, g: 0, b: 0, n: 0 });
          };
          im.src = url;
        });
      }
      var modes = [['silk 默认', null], ['matte 哑光', 'matte'], ['ink 墨色', 'ink'], ['bright 亮丝', 'bright']];
      for (var mi = 0; mi < modes.length; mi++) {
        A.tone = 0.45;                       // 调低块亮度
        A.style = { pathBoost: null, silkWidth: null, silkGain: 0.55, silkMode: modes[mi][1] };
        H.buildWeave(A);
        var st = await chanStats(H.framePng(480, 480, 1));
        log(modes[mi][0] + '（tone .45 / gain .55）通道均值 R=' + st.r + ' G=' + st.g + ' B=' + st.b +
            ' → G 不超过 R：' + (st.g <= st.r) + '，不算发绿(G-R=' + (st.g - st.r) + ')');
      }
      A.style = { pathBoost: null, silkWidth: null, silkGain: null, silkMode: null };
      A.tone = 0.85;
      H.buildWeave(A);

      /* ---------- ③ 手描抖动 → 自动平滑 ---------- */
      log('=== ③ 手描线的平滑 ===');
      function jitterRoute(n, amp, span) {
        var pts = [], rnd = 12345;
        for (var i = 0; i < n; i++) {
          rnd = (rnd * 1103515245 + 12345) % 2147483648;
          var t = i / (n - 1);
          pts.push({
            x: t * span + (rnd % 1000 / 1000 - 0.5) * amp,
            y: Math.sin(t * Math.PI * 2) * span * 0.35 + (rnd % 777 / 777 - 0.5) * amp,
          });
        }
        return pts;
      }
      function turnEnergy(pts) {
        var s = 0, n = 0;
        for (var i = 1; i < pts.length - 1; i++) {
          var a1 = Math.atan2(pts[i].y - pts[i - 1].y, pts[i].x - pts[i - 1].x);
          var a2 = Math.atan2(pts[i + 1].y - pts[i].y, pts[i + 1].x - pts[i].x);
          var d = Math.abs(((a2 - a1 + Math.PI * 3) % (Math.PI * 2)) - Math.PI);
          s += d; n++;
        }
        return n ? s / n : 0;
      }
      // 理想曲线（光滑正弦八字）+ 手抖噪声；看平滑后离理想曲线近了多远
      function idealAt(t, span) {
        return { x: t * span, y: Math.sin(t * Math.PI * 4) * span * 0.32 };
      }
      function distToIdeal(pts, span) {
        var s2 = 0;
        pts.forEach(function (p) {
          var t = Math.max(0, Math.min(1, p.x / span));
          var q = idealAt(t, span);
          s2 += (p.x - q.x) * (p.x - q.x) + (p.y - q.y) * (p.y - q.y);
        });
        return Math.sqrt(s2 / pts.length);
      }
      var SPAN = 200, rnd2 = 777;
      var idealPts = [], noisy = [];
      for (var k = 0; k < 120; k++) {
        var t2 = k / 119;
        var ip = idealAt(t2, SPAN);
        idealPts.push(ip);
        rnd2 = (rnd2 * 1103515245 + 12345) % 2147483648;
        var nx = (rnd2 % 2000 / 1000 - 1) * 2.4;
        rnd2 = (rnd2 * 1103515245 + 12345) % 2147483648;
        var ny = (rnd2 % 2000 / 1000 - 1) * 2.4;
        noisy.push({ x: ip.x + nx, y: ip.y + ny });
      }
      /* 3b：真正进画面的丝迹模板（手描折线）平滑前后对比 */
      function flatToPts(flat) {
        var out = [];
        for (var i = 0; i + 1 < flat.length; i += 2) out.push({ x: flat[i], y: flat[i + 1] });
        return out;
      }
      function resampleN(pts, n) {
        var lens = [0], total = 0;
        for (var i = 1; i < pts.length; i++) {
          total += Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y);
          lens.push(total);
        }
        var out = [], seg = 0;
        for (var k = 0; k < n; k++) {
          var d = total * k / (n - 1);
          while (seg < lens.length - 2 && lens[seg + 1] < d) seg++;
          var t = (d - lens[seg]) / Math.max(1e-9, lens[seg + 1] - lens[seg]);
          out.push({
            x: pts[seg].x + (pts[seg + 1].x - pts[seg].x) * t,
            y: pts[seg].y + (pts[seg + 1].y - pts[seg].y) * t,
          });
        }
        return out;
      }
      var ti = H.templateInfo();
      var r200 = resampleN(flatToPts(ti.raw), 200);
      var s200 = resampleN(flatToPts(ti.sm), 200);
      log('丝迹模板（等弧长重采样 200 点后看转角）');
      function sharpCorners(pts, deg) {
        var c = 0, lim = deg / 57.3;
        for (var i = 1; i < pts.length - 1; i++) {
          var a1 = Math.atan2(pts[i].y - pts[i - 1].y, pts[i].x - pts[i - 1].x);
          var a2 = Math.atan2(pts[i + 1].y - pts[i].y, pts[i + 1].x - pts[i].x);
          var d = Math.abs(((a2 - a1 + Math.PI * 3) % (Math.PI * 2)) - Math.PI);
          if (d > lim) c++;
        }
        return c;
      }
      log('点数 ' + ti.rawN + ' → ' + ti.smN);
      log('尖折角（>25°）数量：' + sharpCorners(r200, 25) + ' → ' + sharpCorners(s200, 25) +
          '；平均转角 ' + (turnEnergy(r200) * 57.3).toFixed(1) + '° → ' + (turnEnergy(s200) * 57.3).toFixed(1) + '°');
      log('__PNG_SMOOTH__' + H.framePng(700, 700, 0.35));

      var sm = H.smoothRoute(noisy);
      var dbg = H.smoothDebugStages(noisy);
      log('蚕的行走轨迹（等弧长重采样 200 点后看转角）');
      log('分段点数：原 ' + dbg.nIn + ' → 重采样 ' + dbg.nResample + ' → 切角 ' + dbg.nChaikin +
          ' → 低通 ' + dbg.nLow + ' → 抽稀 ' + dbg.nOut);
      log('尖折角（>25°）数量：' + sharpCorners(resampleN(noisy, 200), 25) + ' → ' +
          sharpCorners(resampleN(sm, 200), 25) + '；平均转角 ' +
          (turnEnergy(resampleN(noisy, 200)) * 57.3).toFixed(1) + '° → ' +
          (turnEnergy(resampleN(sm, 200)) * 57.3).toFixed(1) + '°');
      log('端点保持：起点 ' + (Math.hypot(sm[0].x - noisy[0].x, sm[0].y - noisy[0].y) < 4) +
          '，终点 ' + (Math.hypot(sm[sm.length - 1].x - noisy[noisy.length - 1].x, sm[sm.length - 1].y - noisy[noisy.length - 1].y) < 4));

      /* ---------- ④ 默认速度 0.2 ---------- */
      log('=== ④ 默认全场速度 ===');
      log('timeline().speed=' + JSON.stringify(H.timeline()) + '，左栏=' +
          (document.getElementById('habTlSpeed') || {}).value);
      log('建议终点=' + H.suggestedEnd() + ' s');
      var dump = H.export();
      if (typeof dump === 'string') dump = JSON.parse(dump);
      dump.timeline.speed = 0.4;               // 旧默认 0.4 的工程
      H.import(dump);
      await step(200);
      log('导入"停在旧默认 0.4×"→ speed=' + H.timeline().speed + '（应 0.2）');
      var d2 = H.export();
      if (typeof d2 === 'string') d2 = JSON.parse(d2);
      d2.timeline.speed = 0.3;                 // 显式手填的
      H.import(d2);
      await step(200);
      log('导入显式 0.3×→ speed=' + H.timeline().speed + '（应保持 0.3）');

      log('jserrs=' + JSON.stringify(window.__errs));
    } catch (e) {
      log('ERR ' + e.message + '\n' + (e.stack || ''));
    }
    out.textContent = L.join('\n');
    out.setAttribute('done', '1');
  }, 700);
});
</script>
<div id="qaout" style="position:fixed;left:6px;top:6px;z-index:99999;background:#000;color:#FC8;font:12px monospace;padding:6px;white-space:pre-wrap">pending</div>'''
style = '<style>body > *:not(#habitat):not(script):not(style):not(#qaout){display:none !important}</style>'
h = src.replace('</head>', style + TEST + '</head>', 1)
tmp = os.path.join(TMP, 'qa-r49-g.html')
io.open(tmp, 'w', encoding='utf-8', newline='').write(h)
cmd = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run', '--disable-extensions',
       '--window-size=1400,900', '--virtual-time-budget=20000', '--dump-dom', 'file:///' + tmp.replace('\\', '/')]
r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=300)
m = re.search(r'<div id="qaout"[^>]*>([\s\S]*?)</div>', r.stdout)
txt = (m.group(1) if m else '(not found)')
pngs = re.findall(r'__PNG_EARLY__data:image/png;base64,([A-Za-z0-9+/=]+)', txt)
png2 = re.findall(r'__PNG_SMOOTH__data:image/png;base64,([A-Za-z0-9+/=]+)', txt)
txt = re.sub(r'__PNG_(EARLY|SMOOTH)__[^\n]+', '[png omitted]', txt)
print(txt.strip())
if png2:
    p2 = os.path.join(TMP, 'qa-r49-g-smooth.png')
    io.open(p2, 'wb').write(base64.b64decode(png2[-1]))
    print('smooth png ->', p2, os.path.getsize(p2), 'bytes')
if pngs:
    p = os.path.join(TMP, 'qa-r49-g-early.png')
    io.open(p, 'wb').write(base64.b64decode(pngs[-1]))
    print('frame png ->', p, os.path.getsize(p), 'bytes')
