# -*- coding: utf-8 -*-
"""r49b 验收：锁定层在画布上完全点不到，从而可以拖与它重合的那一块"""
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
  function dragFrom(x, y, tx, ty) { ev('pointerdown', x, y, 1); ev('pointermove', tx, ty, 1); ev('pointerup', tx, ty, 0); }

  setTimeout(async function () {
    try {
      H.addWeave(); H.addWeave();
      var U = H.agents().filter(function (a) { return a.kind === 'weave'; });
      var A = U[0], B = U[1];
      // 几乎完全重合：中心只差 20px，块 200×200
      A.x = -10; A.y = 0; A.w = A.h = 200; A.seed = 777;
      B.x = 10; B.y = 0; B.w = B.h = 200; B.seed = 777;
      H.buildWeave(A); H.buildWeave(B);
      H.exitEdit();
      await step(250);

      log('--- 锁定上层 B ---');
      B.locked = true;
      await step(150);

      var ax0 = A.x, bx0 = B.x, ay0 = A.y, by0 = B.y;
      dragFrom(0, 0, 60, 30);                 // 在重叠区按住拖
      await step(200);
      log('拖重叠区后：选中=' + H.selectedId() +
          '，A(' + ax0 + ',' + ay0 + ')→(' + A.x + ',' + A.y + ')' +
          '，B(' + bx0 + ',' + by0 + ')→(' + B.x + ',' + B.y + ')');
      log('结论：A 动=' + (Math.abs(A.x - ax0 - 60) < 0.5) + '，B 不动=' + (B.x === bx0 && B.y === by0));

      log('--- 只属于锁定层 B 的地方点一下 ---');
      // 复位：A 占 [-110,90]，B 占 [-90,110]，(100,0) 只落在锁定的 B 上
      A.x = -10; A.y = 0; B.x = 10; B.y = 0;
      H.buildWeave(A); H.buildWeave(B);
      await step(200);
      var selBefore = H.selectedId();
      clickAt(100, 0);
      await step(250);
      var toastTxt = (document.getElementById('habToast') || {}).textContent || '';
      log('pickAt(100,0)=' + H.pickAt(100, 0) + '，B.locked=' + B.locked);
      log('选中是否被锁定层改掉=' + (H.selectedId() === selBefore) +
          '，出现「已锁定」提示=' + (toastTxt.indexOf('已锁定') >= 0) + '（toast: ' + toastTxt.slice(0, 24) + '…）');

      log('--- 锁定层仍然能从右侧图层列表选到 ---');
      var nameBtn = document.querySelector('.lay-name[data-focus="' + B.id + '"]');
      log('列表里有这一行=' + !!nameBtn);
      if (nameBtn) {
        // 真实点击是 pointerdown → click；合成事件要补 pointerdown 才会走到 selectAgent
        nameBtn.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, button: 0, buttons: 1, pointerId: 1 }));
        nameBtn.click();
        await step(250);
      }
      log('点列表行后选中=' + H.selectedId() + '（应 = ' + B.id + '）');

      log('--- 解锁后恢复上层命中 ---');
      B.locked = false;
      A.x = -10; A.y = 0; B.x = 10; B.y = 0;
      H.buildWeave(A); H.buildWeave(B);
      await step(200);
      log('解锁后点重叠区 (0,0)：' + clickAt(0, 0) + '（应 = ' + B.id + '）');
      log('孔洞中心在同一点时仍按上层=' + clickAt(0, 0));
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
tmp = os.path.join(TMP, 'qa-r49-lock.html')
io.open(tmp, 'w', encoding='utf-8', newline='').write(h)

cmd = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
       '--disable-extensions', '--window-size=1500,950', '--virtual-time-budget=12000',
       '--dump-dom', 'file:///' + tmp.replace('\\', '/')]
r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=240)
m = re.search(r'<div id="qaout"[^>]*>([\s\S]*?)</div>', r.stdout)
print((m.group(1) if m else '(not found)').strip())
