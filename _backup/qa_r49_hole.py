# -*- coding: utf-8 -*-
"""复查：编辑这一格、选「孔洞」工具、在格内点一下，孔洞加得进去吗（含重叠块/铺满块的场景）"""
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
  function clickAt(x, y) { ev('pointerdown', x, y, 1); ev('pointermove', x, y, 1); ev('pointerup', x, y, 0); }
  function byId(id) { return H.agents().filter(function (a) { return a.id === id; })[0]; }
  function islandsOf(a) {
    var sh = a && a.custom && a.custom.shapes && a.custom.shapes['0,0'];
    return (sh && sh.islands) ? sh.islands.length : 0;
  }
  function notchOf(a) {
    var sh = a && a.custom && a.custom.shapes && a.custom.shapes['0,0'];
    return (sh && (sh.notchPts || sh.notch)) ? 1 : 0;
  }
  function toastTxt() { return (document.getElementById('habToast') || {}).textContent || ''; }

  setTimeout(async function () {
    try {
      var W = window.__weaveHooks;
      /* ---------- 场景 1：两块几乎重合（= 刚用 Ctrl+D 复制过） ---------- */
      log('=== 场景1：编辑下面那块，点上层的重合区 ===');
      H.addWeave(); H.addWeave();
      var U = H.agents().filter(function (a) { return a.kind === 'weave'; });
      var A = U[0], B = U[1];
      A.x = -10; A.y = 0; A.w = A.h = 200;
      B.x = 10; B.y = 0; B.w = B.h = 200;
      H.buildWeave(A); H.buildWeave(B);
      H.exitEdit();
      await step(200);
      log('A=' + A.id + ' B=' + B.id + '，B 在上层（pickAt(0,0)=' + H.pickAt(0, 0) + '）');

      W.enter(A.id);
      await step(150);
      document.querySelector('.hab-tool[data-wtool="hole"]').click();
      await step(120);
      log('进编辑=' + H.editingId() + '，工具=' + JSON.stringify(H.weaveEditState().tool));
      var c0 = H.cachedCell(A.id, 0, 0);
      var k0 = H.cacheKeys(A.id).filter(function (k) { return k.indexOf('0,0') === 0; });
      clickAt(-90, -80);
      await step(200);
      var k1 = H.cacheKeys(A.id).filter(function (k) { return k.indexOf('0,0') === 0; });
      log('格 0,0 的缓存 key：点前=' + JSON.stringify(k0) + ' 点后=' + JSON.stringify(k1));
      log('缓存里的孔数：点前=' + JSON.stringify(c0) +
          ' 点后=' + JSON.stringify(H.cachedCell(A.id, 0, 0)) + '（点后应立刻变成 2 个孔）');
      log('点完：选中=' + H.selectedId() + '，编辑=' + H.editingId() +
          '，A 的孔=' + islandsOf(A) + '，B 的孔=' + islandsOf(B) + '，toast=' + toastTxt().slice(0, 28));

      /* ---------- 场景 2：5×5 铺块群，点在格子靠边处 ****/
      log('=== 场景2：铺满 5×5，编辑其中一块，点在它靠边的位置 ===');
      H.exitEdit();
      H.agents().filter(function (a) { return a.kind === 'weave'; }).forEach(function (a) {
        H.agents().splice(H.agents().indexOf(a), 1);
      });
      document.getElementById('habAddMosaic').click();
      await step(700);
      var M = H.agents().filter(function (a) { return a.kind === 'weave'; });
      log('铺了 ' + M.length + ' 块');
      var mid = M[Math.floor(M.length / 2)];
      W.enter(mid.id);
      await step(150);
      document.querySelector('.hab-tool[data-wtool="hole"]').click();
      await step(120);
      var holesBefore = islandsOf(mid);
      var px = mid.x + mid.w * 0.36, py = mid.y + mid.h * 0.36;
      log('编辑 ' + mid.id + '（中心 ' + Math.round(mid.x) + ',' + Math.round(mid.y) + '，' + mid.w + '×' + mid.h +
          '），点 (' + Math.round(px) + ',' + Math.round(py) + ')，pickAt=' + H.pickAt(px, py));
      clickAt(px, py);
      await step(220);
      log('点完：选中=' + H.selectedId() + '，编辑=' + H.editingId() +
          '，该块孔数 ' + holesBefore + '→' + islandsOf(mid) + '，toast=' + toastTxt().slice(0, 28));

      log('--- 缺口工具：点一下也要立刻生效 ---');
      document.querySelector('.hab-tool[data-wtool="notch"]').click();
      await step(120);
      var midNotchBefore = notchOf(mid);
      clickAt(mid.x + 4, mid.y + 4);
      await step(220);
      log('缺口 0/1：' + midNotchBefore + '→' + notchOf(mid) + '（缺口按“点几下围一圈”的老规矩，单点只落一个顶点）');
      log('--- 边界已取消 / 桑叶已清干净 ---');
      log('blocked(260,260)=' + H.blockedAt(260, 260) + '（应 false，旧逻辑在正方 180 外是 true）');
      log('blocked(9000,9000)=' + H.blockedAt(9000, 9000) + '（应 false）');
      var fs = (document.getElementById('habFieldStatus') || {}).textContent || '';
      log('场地状态文案=' + fs);
      log('状态里还有"障碍"=' + (fs.indexOf('障碍') >= 0));

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
tmp = os.path.join(TMP, 'qa-r49-hole.html')
io.open(tmp, 'w', encoding='utf-8', newline='').write(h)

cmd = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
       '--disable-extensions', '--window-size=1500,950', '--virtual-time-budget=14000',
       '--dump-dom', 'file:///' + tmp.replace('\\', '/')]
r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=240)
m = re.search(r'<div id="qaout"[^>]*>([\s\S]*?)</div>', r.stdout)
print((m.group(1) if m else '(not found)').strip())
