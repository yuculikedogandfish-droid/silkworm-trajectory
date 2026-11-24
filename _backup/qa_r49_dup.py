# -*- coding: utf-8 -*-
"""r49c 验收：Ctrl+D / Ctrl+C→Ctrl+V 原地复制一块织网单元"""
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
  function key(k, mods) {
    var o = { key: k, bubbles: true, cancelable: true };
    if (mods && mods.indexOf('ctrl') >= 0) o.ctrlKey = true;
    if (mods && mods.indexOf('shift') >= 0) o.shiftKey = true;
    window.dispatchEvent(new KeyboardEvent('keydown', o));
  }
  function look(a) {
    return JSON.stringify({
      w: a.w, h: a.h, shape: a.shape, coverage: a.coverage, scaleK: a.scaleK,
      worms: a.worms, wallAff: a.wallAff, seed: a.seed, tone: a.tone, gap: a.gap,
      strata: a.strata, u: a.u, duration: a.duration, speedScale: a.speedScale,
      shortMode: a.shortMode, tileField: a.tileField, style: a.style,
      custom: a.custom, outline: a.outline, heading: a.heading,
    });
  }
  function byId(id) { return H.agents().filter(function (a) { return a.id === id; })[0]; }

  setTimeout(async function () {
    try {
      H.addWeave();
      await step(250);
      var U = H.agents().filter(function (a) { return a.kind === 'weave'; });
      var A = U[0];
      A.x = 0; A.y = 0; A.w = A.h = 200;
      H.buildWeave(A);
      H.exitEdit();
      await step(200);

      log('--- Ctrl+D 原地复制 ---');
      var before = H.agents().length, lookBefore = look(A), orderBefore = A.schedule.order;
      key('d', ['ctrl']);
      await step(300);
      var U2 = H.agents().filter(function (a) { return a.kind === 'weave'; });
      var D = U2[U2.length - 1];
      log('块数 ' + before + '→' + H.agents().length + '，原=' + A.id + ' 复制件=' + D.id +
          '（不同号=' + (D.id !== A.id) + '）');
      log('位置 原(' + A.x + ',' + A.y + ') 复制件(' + D.x + ',' + D.y + ')，完全重合=' + (D.x === A.x && D.y === A.y));
      log('外观参数逐项一致=' + (look(D) === lookBefore));
      log('锁=false:' + (D.locked === false) + '，出场顺序 ' + orderBefore + '→' + D.schedule.order +
          '（应+1 且在最后=' + (D.schedule.order > orderBefore) + '）');
      log('贴在原块正上方：pickAt(0,0)=' + H.pickAt(0, 0) + '（应 = ' + D.id + '）');
      log('复制后选中=' + H.selectedId() + '（应 = ' + D.id + '）');

      log('--- 复制件能直接拖走 ---');
      dragFrom(0, 0, 260, 0);
      await step(250);
      log('拖后 复制件(' + D.x + ',' + D.y + ') 原块(' + A.x + ',' + A.y + ')（应只有复制件 +260）');

      log('--- 锁定的原块也能被复制，复制件不带锁 ---');
      A.locked = true;
      await step(100);
      var selWas = H.selectedId();
      clickAt(0, 0);
      await step(150);
      log('点原块(锁定)后选中=' + H.selectedId() + '（应仍 = ' + selWas + '）');
      // 选中原块走图层列表（画布点不到它）
      var nameBtn = document.querySelector('.lay-name[data-focus="' + A.id + '"]');
      if (nameBtn) {
        nameBtn.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, button: 0, buttons: 1, pointerId: 1 }));
        nameBtn.click();
        await step(200);
      }
      log('列表选中=' + H.selectedId() + '（应 = ' + A.id + '）');
      key('d', ['ctrl']);
      await step(300);
      var U3 = H.agents().filter(function (a) { return a.kind === 'weave'; });
      var E = U3[U3.length - 1];
      log('再复制一块=' + E.id + '，锁=' + E.locked + '（应 false）');
      A.locked = false;

      log('--- Ctrl+C → Ctrl+V：贴回复制时那个位置 ---');
      var U4 = H.agents().filter(function (a) { return a.kind === 'weave'; });
      var Target = U4[0];
      Target.x = 0; Target.y = 0;
      H.buildWeave(Target);
      // 清场：把别的块挪远，保证点击能选中 Target
      U4.forEach(function (a) { if (a !== Target) { a.x = 9000; a.y = 9000; H.buildWeave(a); } });
      await step(150);
      Target.x = 0; Target.y = 0;
      clickAt(0, 0);
      await step(150);
      log('选中=' + H.selectedId() + '（应 = ' + Target.id + '）');
      key('c', ['ctrl']);
      await step(120);
      log('剪贴板里=' + H.clipUnit() + '（应 = ' + Target.id + '）');
      Target.x = 120; Target.y = 60;             // 复制之后把原块挪走
      H.buildWeave(Target);
      await step(120);
      key('v', ['ctrl']);
      await step(300);
      var U5 = H.agents().filter(function (a) { return a.kind === 'weave'; });
      var P = U5[U5.length - 1];
      log('粘贴件=' + P.id + ' 落点(' + P.x + ',' + P.y + ')（应 = 复制时的 0,0，而不是挪走后的 120,60）');

      log('--- Ctrl+Z 撤销这次粘贴 ---');
      var cntBefore = H.agents().length;
      key('z', ['ctrl']);
      await step(300);
      log('块数 ' + cntBefore + '→' + H.agents().length + '（应 -1）');

      log('--- 没选中时按 Ctrl+D 只提示、不新增 ---');
      var cnt2 = H.agents().length;
      H.agents().forEach(function (a) { if (a.kind === 'weave') { a.x = 9000; a.y = 9000; H.buildWeave(a); } });
      await step(150);
      var toastTxt = (document.getElementById('habToast') || {}).textContent || '';
      key('d', ['ctrl']);
      await step(250);
      toastTxt = (document.getElementById('habToast') || {}).textContent || '';
      log('块数不变=' + (H.agents().length === cnt2) + '，提示=' + toastTxt.slice(0, 30));

      log('--- 左栏按钮「原地复制单元」 ---');
      var btn = document.getElementById('habDupUnit');
      log('按钮存在=' + !!btn + '，文字=' + (btn ? btn.textContent : ''));
      var cntBtn = H.agents().length;
      btn.click();
      await step(250);
      log('无选中时点按钮：块数不变=' + (H.agents().length === cntBtn));
      var firstW = H.agents().filter(function (a) { return a.kind === 'weave'; })[0];
      var btnName = document.querySelector('.lay-name[data-focus="' + firstW.id + '"]');
      if (btnName) {
        btnName.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, button: 0, buttons: 1, pointerId: 1 }));
        btnName.click();
        await step(200);
      }
      btn.click();
      await step(300);
      log('选中后点按钮：块数 ' + cntBtn + '→' + H.agents().length + '（应 +1）');

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
tmp = os.path.join(TMP, 'qa-r49-dup.html')
io.open(tmp, 'w', encoding='utf-8', newline='').write(h)

cmd = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
       '--disable-extensions', '--window-size=1500,950', '--virtual-time-budget=14000',
       '--dump-dom', 'file:///' + tmp.replace('\\', '/')]
r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=240)
m = re.search(r'<div id="qaout"[^>]*>([\s\S]*?)</div>', r.stdout)
print((m.group(1) if m else '(not found)').strip())
