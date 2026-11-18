# -*- coding: utf-8 -*-
"""QA r33：右键压在缺口锚点上 -> 菜单里给"删除这个锚点 / 删除整个缺口"，点第一项才真删"""
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
  us.forEach(u => { u.w = 620; u.h = 620; u.x = 0; u.y = 0; u.tileField = false; u.shape = 'plain'; u.seed = 3141; });
  await H.importPointCloudDoc(window.__QA_CLOUD);
  const P = [{x:-240,y:-90},{x:-40,y:-235},{x:180,y:-120},{x:150,y:150},{x:-90,y:205},{x:-235,y:80}];
  us.forEach(u => { u.custom = u.custom || {walls:{},paths:{},shapes:{}}; u.custom.shapes['0,0'] = { notch: null, islands: [], notchPts: P.slice() }; u.cache && u.cache.clear && u.cache.clear(); H.buildWeave(u); });
  H.seekTo(8);
  const out = document.createElement('div');
  out.style.cssText = 'position:fixed;left:16px;bottom:110px;z-index:99999;color:#ffd76a;font:12px monospace;background:#000d;padding:6px 8px;max-width:1200px;white-space:pre-wrap';
  (document.getElementById('habitat') || document.body).appendChild(out);
  const log = [];
  const say = t => { log.push(t); out.textContent = log.join('\n'); };
  window.onerror = (m, s, l) => say('ERR ' + m + ' @' + l);
  const cv = document.getElementById('habWorld');
  const v = H.view(); const r = cv.getBoundingClientRect();
  const down = (wx, wy) => {
    cv.dispatchEvent(new PointerEvent('pointerdown', { clientX: r.left + v.px(wx), clientY: r.top + v.py(wy), button: 0, buttons: 1, bubbles: true, pointerId: 1, isPrimary: true }));
    cv.dispatchEvent(new PointerEvent('pointerup', { clientX: r.left + v.px(wx), clientY: r.top + v.py(wy), button: 0, buttons: 0, bubbles: true, pointerId: 1, isPrimary: true }));
  };
  try {
    down(0, 0);
    await new Promise(r2 => setTimeout(r2, 250));
    say('编辑=' + H.weaveEditState().agentId + ' 顶点=' + ((us[0].custom.shapes['0,0'].notchPts || []).length));
    // 右键正压在一个锚点上
    cv.dispatchEvent(new MouseEvent('contextmenu', { clientX: r.left + v.px(-240), clientY: r.top + v.py(-90), bubbles: true, cancelable: true, button: 2 }));
    await new Promise(r2 => setTimeout(r2, 400));
    const m = document.getElementById('habCtxMenu');
    const labels = Array.from(m.querySelectorAll('button')).map(b => b.textContent);
    say('菜单项=' + labels.length + ' 前两项=' + labels.slice(0, 2).join(' / '));
    say('删完前 顶点=' + (us[0].custom.shapes['0,0'].notchPts || []).length);
    m.querySelectorAll('button')[0].click();     // 点"删除这个锚点"
    await new Promise(r2 => setTimeout(r2, 350));
    say('点第一项后 顶点=' + ((us[0].custom.shapes['0,0'].notchPts || []).length) + ' 菜单=' + m.style.display);
    await new Promise(r2 => setTimeout(r2, 300));
  } catch (e) { say('ERR ' + e.message); }
})();
"""

src = open(HTML, 'r', encoding='utf-8').read()
cloud = 'window.__QA_CLOUD=%s;' % json.dumps(CLOUD)
p = os.path.join(TMP, 'qa-r33-vertex.html')
open(p, 'w', encoding='utf-8').write(src + '<script>%s</script><script>%s</script>' % (cloud, JS))
print(p)
