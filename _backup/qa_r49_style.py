# -*- coding: utf-8 -*-
"""r49 P0-1 验收探针：单元样式生效 / 全局继承 / 工程往返 / 98%·100% 亮度一致性"""
import io, os, subprocess, re

ROOT = r'H:\tool\silkworm-trajectory'
SRC = ROOT + r'\docs\index.html'
TMP = r'C:\Users\54364\AppData\Local\Temp'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

src = io.open(SRC, encoding='utf-8').read()

probe = r'''<script>window.__errs=[];window.addEventListener("error",function(e){__errs.push(e.message+" @"+(e.filename||"")+":"+(e.lineno||0));});</script>'''

TEST = r'''<script>
window.__R = [];
window.addEventListener('load', function () {
  var H = window.__studioHabitat, out = document.getElementById('qaout');
  var log = function (s) { window.__R.push(s); };
  setTimeout(function () {
    try {
      var W = 180;
      for (var i = 0; i < 4; i++) H.addWeave();
      window.__units = H.agents().filter(function (a) { return a.kind === 'weave'; }).slice(-4);
      window.__units.forEach(function (u, i) {
        u.x = -300 + i * 200; u.y = 0; u.w = W; u.h = W; u.u = 1; H.buildWeave(u);
      });
      var A = window.__units[0], B = window.__units[1];
      A.style = { pathBoost: 2.0, silkWidth: 1.8, silkGain: 0.6, silkMode: 'bright' };
      B.style = { pathBoost: null, silkWidth: null, silkGain: null, silkMode: null };
      window.__A = A; window.__B = B;

      var cv = document.getElementById('habWorld');
      var k = cv.width / cv.clientWidth;
      function meanLum(u) {
        var v = H.view();
        var hs = (u.w / 2) * 0.75;
        var x = Math.round(v.px(u.x - hs) * k), y = Math.round(v.py(u.y - hs) * k);
        var w = Math.round(2 * hs * v.s * k), h = Math.round(2 * hs * v.s * k);
        var d = cv.getContext('2d').getImageData(x, y, w, h).data;
        var s = 0, n = 0;
        for (var i = 0; i < d.length; i += 4) { s += (d[i] + d[i + 1] + d[i + 2]) / 3; n++; }
        return n ? s / n : -1;
      }
      function bands(u) { return H.weaveCellContent(u, 0, 0).paths.length; }
      function setGlobal(id, val) {
        var el = document.getElementById(id);
        el.value = String(val);
        el.dispatchEvent(new Event('input', { bubbles: true }));
      }
      var pending = [];
      function stage(fn, delay) { pending.push([fn, delay || 240]); }
      function run() {
        if (!pending.length) {
          log('A_lum=' + meanLum(A).toFixed(2) + ' B_lum=' + meanLum(B).toFixed(2));
          log('jserrs=' + JSON.stringify(window.__errs));
          out.textContent = window.__R.join('\n');
          out.setAttribute('done', '1');
          return;
        }
        var p = pending.shift();
        setTimeout(function () { try { p[0](); } catch (e) { log('STAGE_ERR ' + e.message); } run(); }, p[1]);
      }

      log('A_bands=' + bands(A) + ' B_bands=' + bands(B));
      log('A_style=' + JSON.stringify(A.style));
      log('leftPanel_width_val=' + document.getElementById('habSilkWidthVal').textContent);

      // 1) 改全局密度 → B 变密、A 独立块不变
      stage(function () {
        setGlobal('habPathBoost', 1.5);
        log('after_global1.5 B_bands=' + bands(B) + ' A_bands=' + bands(A));
      });
      stage(function () {
        setGlobal('habPathBoost', 1.0);
        log('back_global1.0 B_bands=' + bands(B));
      });

      // 2) 98% / 100% 同一块亮度
      stage(function () {
        A.u = 1; B.u = 0.98;
        window.__lum98 = meanLum(B);
        log('B_u0.98=' + window.__lum98.toFixed(2));
      }, 320);
      stage(function () {
        B.u = 1;
        var l100 = meanLum(B);
        var diff = Math.abs(l100 - window.__lum98) / Math.max(1, window.__lum98) * 100;
        log('B_u1.00=' + l100.toFixed(2) + ' diff%=' + diff.toFixed(2));
      }, 320);

      // 3) 工程往返：A 的独立值 / B 的继承关系都要活着回来
      stage(function () {
        var doc = H.export();
        window.__docStyle = JSON.stringify(doc.agents.filter(function (a) { return a.weave; })
          .map(function (a) { return { id: a.id, style: a.weave.style }; }));
        H.import(doc);
        var units = H.agents().filter(function (a) { return a.kind === 'weave'; });
        var a2 = units.filter(function (u) { return u.id === A.id; })[0];
        var b2 = units.filter(function (u) { return u.id === B.id; })[0];
        log('export_styles=' + window.__docStyle);
        log('after_import A_style=' + JSON.stringify(a2 && a2.style));
        log('after_import B_style=' + JSON.stringify(b2 && b2.style));
        log('after_import A_bands=' + (a2 ? H.weaveCellContent(a2, 0, 0).paths.length : -1));
      });
      run();
    } catch (e) {
      out.textContent = 'ERR ' + e.message + '\n' + (e.stack || '');
      out.setAttribute('done', '1');
    }
  }, 600);
});
</script>
<div id="qaout" style="position:fixed;left:6px;top:6px;z-index:99999;background:#000;color:#7CFFB2;font:12px monospace;padding:6px;white-space:pre-wrap">pending</div>'''

style = '<style>body > *:not(#habitat):not(script):not(style):not(#qaout){display:none !important}</style>'

h = src.replace('<head>', '<head>\n' + probe, 1)
h = h.replace('</head>', style + TEST + '</head>', 1)
tmp = os.path.join(TMP, 'qa-r49-style.html')
io.open(tmp, 'w', encoding='utf-8', newline='').write(h)

cmd = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
       '--disable-extensions', '--window-size=1600,1000', '--virtual-time-budget=8000',
       '--dump-dom', 'file:///' + tmp.replace('\\', '/')]
r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=150)
m = re.search(r'<div id="qaout"[^>]*>([\s\S]*?)</div>', r.stdout)
print((m.group(1) if m else '(not found)').strip())
print('--- done ---', 'done="1"' in r.stdout)
