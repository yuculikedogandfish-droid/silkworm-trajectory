# -*- coding: utf-8 -*-
"""QA r32：缺口不再堆点 / 缺口曲线化 / 右键菜单"""
import json, os

HTML = r"H:\tool\silkworm-trajectory\docs\index.html"
TMP = os.environ.get('TEMP', r'C:\Users\54364\AppData\Local\Temp')
CLOUD = json.load(open(r"G:\raby model\trajectories.json", encoding='utf-8'))

HEAD = r"""
(async () => {
  const s = document.createElement('style');
  s.textContent = 'body > *:not(#habitat):not(#habCtxMenu):not(script):not(style){display:none}';
  document.head.appendChild(s);
  await new Promise(r => setTimeout(r, 900));
  const H = window.__studioHabitat;
  H.addWeave({});
"""

COMMON = r"""
  const us = H.agents().filter(a => a.kind === 'weave');
  us.forEach(u => { u.w = 620; u.h = 620; u.x = 0; u.y = 0; u.tileField = false; u.shape = 'plain'; u.seed = 3141; });
  await H.importPointCloudDoc(window.__QA_CLOUD);
  us.forEach(u => { if (u.cache && u.cache.clear) u.cache.clear(); H.buildWeave(u); });
  H.seekTo(8);
  const st = [];
  const out = document.createElement('div');
  out.style.cssText = 'position:fixed;left:16px;bottom:110px;z-index:99999;color:#ffd76a;font:12px monospace;background:#000d;padding:6px 8px;max-width:1200px;white-space:pre-wrap';
  (document.getElementById('habitat') || document.body).appendChild(out);
  const say = (t) => { st.push(t); out.textContent = st.join('\n'); };
  window.onerror = (m, src, ln) => { say('ERR ' + m + ' @' + ln); };
"""

pdjs = r"""
  const cv = document.getElementById('habWorld');
  const ev = (type, wx, wy, opt) => {
    const v = H.view(); const r = cv.getBoundingClientRect();
    cv.dispatchEvent(new PointerEvent(type, Object.assign({
      clientX: r.left + v.px(wx), clientY: r.top + v.py(wy),
      button: 0, bubbles: true, pointerId: 1, isPrimary: true,
    }, opt || {})));
  };
  const tap = (wx, wy) => { ev('pointerdown', wx, wy, { buttons: 1 }); ev('pointerup', wx, wy, { buttons: 0 }); };
"""

FLOW = COMMON + pdjs + r"""
  const inPoly = (P, x, y) => {
    let c = false;
    for (let i = 0, j = P.length - 1; i < P.length; j = i++) {
      const A = P[i], B = P[j];
      if (((A.y > y) !== (B.y > y)) && (x < (B.x - A.x) * (y - A.y) / (B.y - A.y) + A.x)) c = !c;
    }
    return c;
  };
  try {
    tap(80, 80);
    await new Promise(r => setTimeout(r, 200));
    document.querySelector('#habWeaveTools .hab-tool[data-wtool="notch"]').click();
    await new Promise(r => setTimeout(r, 60));
    const P = [[-250, -150], [80, -255], [255, 20], [40, 250], [-180, 150]];
    for (const q of P) { tap(q[0], q[1]); await new Promise(r => setTimeout(r, 45)); }
    document.getElementById('habWeaveEditEnd').click();
    await new Promise(r => setTimeout(r, 350));
    const sh = (us[0].custom.shapes || {})['0,0'] || {};
    say('1 画完 顶点=' + ((sh.notchPts || []).length));
    // 连点 3 下格内（应该一个锚点都不加）
    tap(-120, -40); await new Promise(r => setTimeout(r, 60));
    tap(120, -40); await new Promise(r => setTimeout(r, 60));
    tap(60, 120); await new Promise(r => setTimeout(r, 60));
    say('2 再点 3 下后 顶点=' + (((us[0].custom.shapes || {})['0,0'] || {}).notchPts || []).length);
    // 丝线有没有落进缺口
    if (us[0].cache && us[0].cache.delete) us[0].cache.delete('0,0');
    const c = H.weaveCellContent(us[0], 0, 0);
    let total = 0, inside = 0;
    (c.paths || []).forEach(p => (p.pts || []).forEach(q => { total++; if (inPoly(P, q.x, q.y)) inside++; }));
    say('3 丝点=' + total + ' 落缺口=' + inside + ' 丝数=' + (c.paths || []).length);
    document.getElementById('habFit') && document.getElementById('habFit').click();
    await new Promise(r => setTimeout(r, 300));
    document.getElementById('habWeaveEditDone') && document.getElementById('habWeaveEditDone').click();
    await new Promise(r => setTimeout(r, 300));
  } catch (e) { say('ERR ' + e.message); }
})();
"""

MENU = COMMON + pdjs + r"""
  try {
    tap(80, 80);
    await new Promise(r => setTimeout(r, 250));
    say('进编辑=' + JSON.stringify(H.weaveEditState().agentId));
    const r2 = cv.getBoundingClientRect(); const v = H.view();
    cv.dispatchEvent(new MouseEvent('contextmenu', {
      clientX: r2.left + v.px(120), clientY: r2.top + v.py(-60),
      bubbles: true, cancelable: true, button: 2,
    }));
    await new Promise(r => setTimeout(r, 500));
    const menu = document.getElementById('habCtxMenu');
    say('菜单显示=' + (menu ? menu.style.display : 'null') + ' 项数=' + (menu ? menu.children.length : 0));
    await new Promise(r => setTimeout(r, 300));
  } catch (e) { say('ERR ' + e.message); }
})();
"""

src = open(HTML, 'r', encoding='utf-8').read()
cloud = 'window.__QA_CLOUD=%s;' % json.dumps(CLOUD)
CURVE = COMMON + pdjs + r"""
  try {
    const a = us[0];
    a.custom = a.custom || { walls: {}, paths: {}, shapes: {} };
    a.custom.shapes['0,0'] = { notch: null, islands: [], notchPts: [
      {x:-240,y:-90},{x:-40,y:-235},{x:180,y:-120},{x:150,y:150},{x:-90,y:205},{x:-235,y:80}] };
    if (a.cache && a.cache.clear) a.cache.clear();
    H.buildWeave(a);
    const c = H.weaveCellContent(a, 0, 0);
    let total = 0;
    (c.paths || []).forEach(p => (p.pts || []).forEach(() => total++));
    say('曲线缺口 控制点=' + a.custom.shapes['0,0'].notchPts.length + ' 丝点=' + total);
    tap(0, 0);
    await new Promise(r => setTimeout(r, 300));
    const fit = document.getElementById('habFit'); if (fit) fit.click();
    await new Promise(r => setTimeout(r, 400));
  } catch (e) { say('ERR ' + e.message); }
})();
"""

for name, body in (('flow', FLOW), ('menu', MENU), ('curve', CURVE)):
    p = os.path.join(TMP, 'qa-r32-%s.html' % name)
    open(p, 'w', encoding='utf-8').write(
        src + '<script>%s</script><script>%s</script>' % (cloud, HEAD + body))
    print(p)
