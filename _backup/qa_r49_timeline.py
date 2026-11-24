# -*- coding: utf-8 -*-
"""r49 P0-2/3/5/6 验收探针：出场顺序 / 间隔 / 全场速度 / 时长与截断 / 区间夹取"""
import io, os, subprocess, re

ROOT = r'H:\tool\silkworm-trajectory'
SRC = ROOT + r'\docs\index.html'
TMP = r'C:\Users\54364\AppData\Local\Temp'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

src = io.open(SRC, encoding='utf-8').read()
probe = r'''<script>window.__errs=[];window.addEventListener("error",function(e){__errs.push(e.message+" @"+(e.filename||"")+":"+(e.lineno||0));});</script>'''

TEST = r'''<script>
window.addEventListener('load', function () {
  var H = window.__studioHabitat, out = document.getElementById('qaout');
  var L = [], log = function (s) { L.push(s); };
  function setIn(id, val, ev) {
    var el = document.getElementById(id);
    el.value = String(val);
    el.dispatchEvent(new Event(ev || 'input', { bubbles: true }));
  }
  setTimeout(function () {
    try {
      var A, B, C;
      for (var i = 0; i < 3; i++) H.addWeave();
      var units = H.agents().filter(function (a) { return a.kind === 'weave'; }).slice(-3);
      A = units[0]; B = units[1]; C = units[2];
      units.forEach(function (u, i) { u.w = u.h = 180; u.x = -200 + i * 200; u.y = 0; });
      A.schedule = { order: 0, manualStart: null };
      B.schedule = { order: 1, manualStart: null };
      C.schedule = { order: 2, manualStart: null };
      A.duration = 22; B.duration = 22; C.duration = 22;
      A.shortMode = B.shortMode = C.shortMode = 'cut';
      A.speedScale = B.speedScale = C.speedScale = 1;

      setIn('habTlMode', 'sequence', 'change');
      setIn('habTlInterval', 3);
      setIn('habTlSpeed', 0.8);
      setIn('habTlEnd', 90);

      var f = function (x) { return (Math.round(x * 1000) / 1000).toFixed(3); };
      H.seekTo(1);
      log('t1  uA=' + f(A.u) + ' uB=' + f(B.u) + ' uC=' + f(C.u));
      H.seekTo(4);
      log('t4  uA=' + f(A.u) + ' uB=' + f(B.u) + ' uC=' + f(C.u));
      H.seekTo(6);
      log('t6  uA=' + f(A.u) + ' uB=' + f(B.u) + ' uC=' + f(C.u));
      H.seekTo(74);
      log('t74 uA=' + f(A.u) + ' slider_max=' + document.getElementById('habTime').max +
          ' clock=' + document.getElementById('habClock').textContent);

      // 顺序字段改 2/0/1 → 起织顺序跟着字段变，不跟数组位置
      setIn('habUnitOrder', 0); // 作用于当前选中的块（最后选中 C）
      C.schedule.order = 2; B.schedule.order = 0; A.schedule.order = 1;
      document.getElementById('habTlInterval').dispatchEvent(new Event('input', { bubbles: true }));
      H.seekTo(1);
      log('reorder t1 uA=' + f(A.u) + ' uB=' + f(B.u) + ' uC=' + f(C.u) + ' (B 应为 0.036)');

      // 全场速度 0.5 → 有效时长翻倍
      setIn('habTlSpeed', 0.5);
      H.seekTo(44);
      log('speed0.5 t44 uB=' + f(B.u) + ' (start 0, 有效 44s)');

      // 区间夹取：终点 90 时拖 200 应被夹到 90
      H.seekTo(200);
      log('seek200 clamp simTime=' + H.agents().length + ' clock=' + document.getElementById('habClock').textContent);

      // 缩短：cut 织到 68%，compress 织满
      setIn('habTlSpeed', 0.8);
      B.duration = 15; B.shortMode = 'cut';
      document.getElementById('habUnitShort').value = 'cut';
      H.seekTo(18.75);
      log('cut15 t18.75 uB=' + f(B.u) + ' (应 0.682)');
      B.shortMode = 'compress';
      H.seekTo(18.75);
      log('compress15 t18.75 uB=' + f(B.u) + ' (应 1.000)');

      // 延长：30s → 丝量 1.36 倍
      B.duration = 30; B.shortMode = 'cut';
      var b30 = H.weaveCellContent(B, 0, 0).paths.length;
      B.duration = 22;
      var b22 = H.weaveCellContent(B, 0, 0).paths.length;
      log('bands d22=' + b22 + ' d30=' + b30 + ' ratio=' + (b30 / b22).toFixed(2));

      // 工程往返
      var doc = H.export();
      var tlOut = doc.timeline;
      H.import(doc);
      var u2 = H.agents().filter(function (a) { return a.kind === 'weave'; });
      log('timeline_out=' + JSON.stringify(tlOut));
      log('after_import uB_duration=' + u2.filter(function (u) { return u.id === B.id; })[0].duration +
          ' order=' + u2.filter(function (u) { return u.id === B.id; })[0].schedule.order);
      log('jserrs=' + JSON.stringify(window.__errs));
      out.textContent = L.join('\n');
      out.setAttribute('done', '1');
    } catch (e) {
      out.textContent = 'ERR ' + e.message + '\n' + (e.stack || '');
      out.setAttribute('done', '1');
    }
  }, 600);
});
</script>
<div id="qaout" style="position:fixed;left:6px;top:6px;z-index:99999;background:#000;color:#7CFFB2;font:12px monospace;padding:6px;white-space:pre-wrap">pending</div>'''

style = '<style>body > *:not(#habitat):not(script):not(style):not(#qaout){display:none !important}</style>'
h = src.replace('<head>', '<head>\n' + probe, 1).replace('</head>', style + TEST + '</head>', 1)
tmp = os.path.join(TMP, 'qa-r49-timeline.html')
io.open(tmp, 'w', encoding='utf-8', newline='').write(h)

cmd = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
       '--disable-extensions', '--window-size=1600,1000', '--virtual-time-budget=9000',
       '--dump-dom', 'file:///' + tmp.replace('\\', '/')]
r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=180)
m = re.search(r'<div id="qaout"[^>]*>([\s\S]*?)</div>', r.stdout)
print((m.group(1) if m else '(not found)').strip())
print('--- done ---', 'done="1"' in r.stdout)
