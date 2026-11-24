# -*- coding: utf-8 -*-
"""r49f 验收：①全场速度对所有单元生效 ②点空白取消选择 ③编辑态亮度=导出亮度（可切换压暗）"""
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
  var step = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
  function ev(type, x, y, buttons) {
    var c = H.toClient(x, y), cv = document.getElementById('habWorld');
    cv.dispatchEvent(new PointerEvent(type, {
      clientX: c.clientX, clientY: c.clientY, button: 0, buttons: buttons,
      pointerId: 1, bubbles: true, cancelable: true,
    }));
  }
  function clickAt(x, y) { ev('pointerdown', x, y, 1); ev('pointerup', x, y, 0); return H.selectedId(); }
  function setSpeed(v) {
    var el = document.getElementById('habTlSpeed');
    el.value = String(v);
    el.dispatchEvent(new Event('input', { bubbles: true }));
  }
  function alphaAt(x, y) {
    var cv = document.getElementById('habWorld'), r = cv.getBoundingClientRect();
    var c = H.toClient(x, y);
    var px = Math.round((c.clientX - r.left) * (cv.width / r.width));
    var py = Math.round((c.clientY - r.top) * (cv.height / r.height));
    var d = cv.getContext('2d').getImageData(px, py, 1, 1).data;
    return { a: d[3], lum: Math.round((d[0] + d[1] + d[2]) / 3) };
  }
  function byId(id) { return H.agents().filter(function (a) { return a.id === id; })[0]; }
  function meanLum(x0, y0, w, h) {
    var cv = document.getElementById('habWorld'), r = cv.getBoundingClientRect();
    var c0 = H.toClient(x0 - w * 0.4, y0 - h * 0.4), c1 = H.toClient(x0 + w * 0.4, y0 + h * 0.4);
    var sx = (c0.clientX - r.left) * (cv.width / r.width);
    var sy = (c0.clientY - r.top) * (cv.height / r.height);
    var sw = Math.max(1, Math.round((c1.clientX - c0.clientX) * (cv.width / r.width)));
    var sh = Math.max(1, Math.round((c1.clientY - c0.clientY) * (cv.height / r.height)));
    var d = cv.getContext('2d').getImageData(Math.round(sx), Math.round(sy), sw, sh).data;
    var sum = 0, n = 0, mx = 0;
    for (var k = 0; k < d.length; k += 4) {
      var l = (d[k] * 0.3 + d[k + 1] * 0.59 + d[k + 2] * 0.11) * d[k + 3] / 255;
      sum += l; if (l > mx) mx = l; n++;
    }
    return { a: Math.round(sum / n), max: Math.round(mx) };
  }

  setTimeout(async function () {
    try {
      /* ---------- ① 全场速度 = 所有单元 ---------- */
      log('=== ① 全场速度作用于每一块 ===');
      H.addWeave(); H.addWeave(); H.addWeave();
      await step(300);
      var U = H.agents().filter(function (a) { return a.kind === 'weave'; });
      U.forEach(function (a, i) {
        a.duration = 22;
        a.speedScale = [1, 0.5, 2][i];
        a.schedule = { order: i, manualStart: null };
        a.x = -300 + i * 300; a.y = 0;
      });
      H.refreshTimeline();
      setSpeed(0.4);
      await step(200);
      var d04 = U.map(function (a) { return H.unitEff(a.id); });
      setSpeed(0.8);
      await step(200);
      var d08 = U.map(function (a) { return H.unitEff(a.id); });
      log('单块倍率=' + U.map(function (a) { return a.speedScale; }) + '，时长=22s');
      log('0.40× 有效时长=' + JSON.stringify(d04));
      log('0.80× 有效时长=' + JSON.stringify(d08));
      log('每块都随全场速度变化=' + JSON.stringify(d04.map(function (v, i) {
        return Math.abs(d08[i] * 2 - v) < 1.5;
      })) + '（应全为 true）');
      setSpeed(0.4);

      /* ---------- ② 点空白取消选择 ---------- */
      log('=== ② 点单元格外空白 = 取消选择 ===');
      U[0].x = -300; U[0].y = 0; U[1].x = 0; U[1].y = 0; U[2].x = 300; U[2].y = 0;
      U.forEach(function (a) { H.buildWeave(a); });
      await step(200);
      clickAt(0, 0);
      await step(200);
      log('先点中一块：选中=' + H.selectedId() + '，右栏=' +
          ((document.getElementById('habRouteInfo') || {}).textContent || '').slice(0, 12));
      clickAt(700, 500);            // 很远的外面（没有单元）
      await step(250);
      log('点空白后：选中=' + H.selectedId() + '，右栏=' +
          ((document.getElementById('habRouteInfo') || {}).textContent || '').slice(0, 12) +
          '，编辑=' + H.editingId());
      log('图层树选中数=' + (window.__layerSel ? window.__layerSel.size() : 'n/a'));

      /* ---------- ③ 编辑态亮度 ---------- */
      log('=== ③ 编辑时看到的亮度 = 导出亮度 ===');
      var A = U[1], B = U[2];
      A.x = 0; A.y = 0; B.x = 300; B.y = 0;
      H.buildWeave(A); H.buildWeave(B);
      var dimBox = document.getElementById('habDimOthers');
      log('压暗开关默认=' + (dimBox ? dimBox.checked : 'n/a') + '（应 false）');
      window.__weaveHooks.enter(A.id);
      await step(200);
      H.repaint();
      await step(50);
      log('进入编辑后 state=' + JSON.stringify(H.state()));
      var off = meanLum(300, 0, 200, 200);
      log('不压暗 state=' + JSON.stringify(H.state()));
      log('不压暗时，另一块区域平均亮度=' + off.a + ' / 峰值亮度 ' + off.max);
      if (dimBox) { dimBox.checked = true; dimBox.dispatchEvent(new Event('change', { bubbles: true })); }
      await step(150);
      H.repaint();
      await step(50);
      log('勾选后 state=' + JSON.stringify(H.state()));
      var on = meanLum(300, 0, 200, 200);
      log('勾上压暗后平均亮度=' + on.a + ' / 峰值亮度 ' + on.max + '，比值=' + (on.a / (off.a || 1)).toFixed(2) + '（应约 0.42）');
      if (dimBox) { dimBox.checked = false; dimBox.dispatchEvent(new Event('change', { bubbles: true })); }
      await step(150);
      H.repaint();
      await step(50);
      var back = meanLum(300, 0, 200, 200);
      log('结束 state=' + JSON.stringify(H.state()));
      log('取消勾选后平均亮度=' + back.a + '（应回到 ' + off.a + '）');

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
<div id="qaout" style="position:fixed;left:6px;top:6px;z-index:99999;background:#000;color:#FC8;font:12px monospace;padding:6px;white-space:pre-wrap">pending</div>'''

style = '<style>body > *:not(#habitat):not(script):not(style):not(#qaout){display:none !important}</style>'
h = src.replace('<head>', '<head>\n' + TAG, 1).replace('</head>', style + TEST + '</head>', 1)
tmp = os.path.join(TMP, 'qa-r49-bright.html')
io.open(tmp, 'w', encoding='utf-8', newline='').write(h)

cmd = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
       '--disable-extensions', '--window-size=1500,950', '--virtual-time-budget=14000',
       '--dump-dom', 'file:///' + tmp.replace('\\', '/')]
r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=240)
m = re.search(r'<div id="qaout"[^>]*>([\s\S]*?)</div>', r.stdout)
print((m.group(1) if m else '(not found)').strip())
