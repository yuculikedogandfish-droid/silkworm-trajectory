# -*- coding: utf-8 -*-
"""QA r36：右键删除整块 / 右栏「删除这一块」"""
import json, os

HTML = r"H:\tool\silkworm-trajectory\docs\index.html"
TMP = os.environ.get('TEMP', r'C:\Users\54364\AppData\Local\Temp')
CLOUD = json.load(open(r"G:\raby model\trajectories.json", encoding='utf-8'))

JS = r"""
(async () => {
  const st = document.createElement('style');
  st.textContent = 'body > *:not(#habitat):not(#habCtxMenu):not(script):not(style){display:none}';
  document.head.appendChild(st);
  await new Promise(r => setTimeout(r, 900));
  const H = window.__studioHabitat;
  H.addWeave({});
  const us = H.agents().filter(a => a.kind === 'weave');
  us.forEach((u, i) => { u.w = 520; u.h = 520; u.x = i ? 330 : -330; u.y = 0; u.tileField = false; u.shape = 'island'; u.seed = 101 + i * 202; });
  await H.importPointCloudDoc(window.__QA_CLOUD);
  us.forEach(u => { H.buildWeave(u); H.assignWormToUnit(u.id, 'all'); });
  H.seekTo(7);
  const out = document.createElement('div');
  out.style.cssText = 'position:fixed;left:16px;bottom:110px;z-index:99999;color:#ffd76a;font:12px monospace;background:#000d;padding:6px 8px;max-width:1200px;white-space:pre-wrap';
  (document.getElementById('habitat') || document.body).appendChild(out);
  const log = []; const say = t => { log.push(t); out.textContent = log.join(String.fromCharCode(10)); };
  window.onerror = (m, s2, l) => say('ERR ' + m + ' @' + l);
  const cv = document.getElementById('habWorld');
  const toS = (wx, wy) => { const v = H.view(); const r = cv.getBoundingClientRect(); return { x: r.left + v.px(wx), y: r.top + v.py(wy) }; };
  const units = () => H.agents().filter(a => a.kind === 'weave');
  try {
    say('0 起始 块数=' + units().length + '（id=' + units().map(u => u.id).join(',') + '）');
    // 右键第二块
    const q = toS(330, 0);
    cv.dispatchEvent(new MouseEvent('contextmenu', { clientX: q.x, clientY: q.y, bubbles: true, cancelable: true, button: 2 }));
    await new Promise(r => setTimeout(r, 320));
    const btns = Array.from(document.querySelectorAll('#habCtxMenu button'));
    say('1 菜单项=' + btns.map(b => b.textContent).join(' | '));
    const delBtn = btns.find(b => b.textContent.indexOf('删除这一块织网单元') >= 0);
    if (!delBtn) { say('XX 菜单里没有删除项'); }
    else { delBtn.click(); await new Promise(r => setTimeout(r, 300)); }
    say('2 右键删完 块数=' + units().length + '（剩 ' + units().map(u => u.id).join(',') + '）');
    // 选中剩下那块，点右栏按钮
    const rest = units()[0];
    if (rest) {
      const p = toS(rest.x, rest.y);
      cv.dispatchEvent(new PointerEvent('pointerdown', { clientX: p.x, clientY: p.y, button: 0, buttons: 1, bubbles: true, pointerId: 1, isPrimary: true }));
      cv.dispatchEvent(new PointerEvent('pointerup', { clientX: p.x, clientY: p.y, button: 0, buttons: 0, bubbles: true, pointerId: 1, isPrimary: true }));
      await new Promise(r => setTimeout(r, 260));
      const btn = document.getElementById('habDeleteUnit');
      say('3 右栏按钮存在=' + !!btn + ' 文案=' + (btn ? btn.textContent : '-'));
      if (btn) btn.click();
      await new Promise(r => setTimeout(r, 300));
      say('4 按钮删完 块数=' + units().length);
    }
    // 撤销验证
    H.undoStep && H.undoStep();
    await new Promise(r => setTimeout(r, 200));
    say('5 撤销后 块数=' + units().length);
  } catch (e) { say('ERR ' + e.message); }
})();
"""

src = open(HTML, 'r', encoding='utf-8').read()
cloud = 'window.__QA_CLOUD=%s;' % json.dumps(CLOUD)
open(os.path.join(TMP, 'r36.html'), 'w', encoding='utf-8').write(src + '<script>%s</script><script>%s</script>' % (cloud, JS))
print('r36.html')
