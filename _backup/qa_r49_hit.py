# -*- coding: utf-8 -*-
"""r49b 验收：两块重叠时点中谁 / 锁定层是否让路 / 拖动是否跟着选中的那块"""
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
    var c = H.toClient(x, y);
    var cv = document.getElementById('habWorld');
    cv.dispatchEvent(new PointerEvent(type, {
      clientX: c.clientX, clientY: c.clientY,
      button: 0, buttons: buttons, pointerId: 1, bubbles: true, cancelable: true,
    }));
  }
  function clickAt(x, y) { ev('pointerdown', x, y, 1); ev('pointerup', x, y, 0); return H.selectedId(); }
  function dragFrom(x, y, tx, ty) { ev('pointerdown', x, y, 1); ev('pointermove', tx, ty, 1); ev('pointerup', tx, ty, 0); }

  setTimeout(async function () {
    try {
      H.addWeave(); H.addWeave();
      var units = H.agents().filter(function (a) { return a.kind === 'weave'; });
      var A = units[0], B = units[1];
      // 两块大面积重叠：中心相距 80，块宽 200（重叠 120 宽）
      A.x = -40; A.y = 0; A.w = A.h = 200;
      B.x = 40; B.y = 0; B.w = B.h = 200;
      [A, B].forEach(function (u) { u.seed = 4242; u.coverage = 0.55; u.worms = 6; H.buildWeave(u); });
      await step(300);

      log('A.id=' + A.id + ' B.id=' + B.id + '  B 后放 = 上层');
      log('重叠区 (0,0) 点到：' + clickAt(0, 0) + '（应 = ' + B.id + '，旧逻辑会是 ' + A.id + '）');
      await step(120);
      log('只属于 A 的点 (-120,0)：' + clickAt(-120, 0) + '（应 = ' + A.id + '）');
      await step(120);
      log('只属于 B 的点 (120,0)：' + clickAt(120, 0) + '（应 = ' + B.id + '）');
      await step(120);

      // 锁定上层 B：重叠区应让给 A
      B.locked = true;
      await step(160);
      log('锁定 B 后点重叠区 (0,0)：' + clickAt(0, 0) + '（应 = ' + A.id + '）');
      await step(120);

      // 拖动：先退出编辑态（编辑态里点另一块是"切过去"，不起拖），再选 A 拖它
      H.exitEdit();
      await step(160);
      var ax0 = A.x, bx0 = B.x;
      dragFrom(0, 0, 30, 20);
      await step(200);
      log('拖动后 A.x ' + ax0 + '→' + A.x + '，B.x ' + bx0 + '→' + B.x +
          '（应只有 A 动：A ' + (A.x !== ax0) + ' / B ' + (B.x !== bx0) + '）');

      // 解锁后恢复上层命中
      B.locked = false;
      await step(160);
      log('解锁 B 后点重叠区（此时在编辑 A，点在自己包围盒里 → 不跳块）：' + clickAt(0, 0) +
          '（应 = ' + A.id + '）');
      await step(120);

      // 编辑态里点另一块并直接拖：应该既切过去、又真的拖得动
      H.exitEdit(); await step(120);
      A.x = -40; A.y = 0; B.x = 40; B.y = 0;
      A.cache = new Map(); B.cache = new Map();
      H.buildWeave(A); H.buildWeave(B);
      await step(200);
      clickAt(-120, 0);                       // 只属于 A → 进 A 的编辑
      await step(150);
      log('先点 A 进编辑：选中=' + H.selectedId() + '，正在编辑=' + H.editingId());
      var bx1 = B.x;
      // 在 A 包围盒之外、B 之内的位置按住拖（编辑态切块 + 直接拖）
      dragFrom(100, 0, 140, 0);
      await step(200);
      log('编辑态下拖另一块（点 (100,0)：A 之外、B 之内）：选中=' + H.selectedId() + '，B.x ' + bx1 + '→' + B.x +
          '（应选中 ' + B.id + ' 且 B 真的动）');
      await step(120);

      // 编辑态里点自己的包围盒（包括两块的公共重叠区）：不跳块，继续改这一块
      log('编辑态点自身重叠区 (0,0)：' + clickAt(0, 0) + '（应仍 = ' + B.id + '）');
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
tmp = os.path.join(TMP, 'qa-r49-hit.html')
io.open(tmp, 'w', encoding='utf-8', newline='').write(h)

cmd = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
       '--disable-extensions', '--window-size=1500,950', '--virtual-time-budget=12000',
       '--dump-dom', 'file:///' + tmp.replace('\\', '/')]
r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=240)
m = re.search(r'<div id="qaout"[^>]*>([\s\S]*?)</div>', r.stdout)
print((m.group(1) if m else '(not found)').strip())
