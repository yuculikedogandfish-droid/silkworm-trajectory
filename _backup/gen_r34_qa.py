# -*- coding: utf-8 -*-
"""QA r34：点线上加锚点 + 拖动锚点 + 画的时候就曲线 + 右键菜单项"""
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
  const P = [{x:-250,y:-110},{x:-60,y:-250},{x:170,y:-150},{x:190,y:110},{x:-10,y:220},{x:-225,y:110}];
  us.forEach(u => {
    u.custom = u.custom || {walls:{},paths:{},shapes:{}};
    u.custom.shapes['0,0'] = { notch: null, islands: [], notchPts: P.map(q => ({x:q.x,y:q.y})) };
    if (u.cache && u.cache.clear) u.cache.clear();
    H.buildWeave(u);
  });
  H.seekTo(7);
  const out = document.createElement('div');
  out.style.cssText = 'position:fixed;left:16px;bottom:110px;z-index:99999;color:#ffd76a;font:12px monospace;background:#000d;padding:6px 8px;max-width:1200px;white-space:pre-wrap';
  (document.getElementById('habitat') || document.body).appendChild(out);
  const log = [];
  const say = t => { log.push(t); out.textContent = log.join('\n'); };
  window.onerror = (m, s2, l) => say('ERR ' + m + ' @' + l);
  const cv = document.getElementById('habWorld');
  const pts = () => (us[0].custom.shapes['0,0'] || {}).notchPts || [];
  const ev = (type, wx, wy, buttons, extra) => {
    const v = H.view(); const r = cv.getBoundingClientRect();
    cv.dispatchEvent(new PointerEvent(type, Object.assign({
      clientX: r.left + v.px(wx), clientY: r.top + v.py(wy),
      button: 0, buttons: buttons, bubbles: true, pointerId: 1, isPrimary: true,
    }, extra || {})));
    return r;
  };
  const tap = (wx, wy) => { ev('pointerdown', wx, wy, 1); ev('pointerup', wx, wy, 0); };
  try {
    tap(0, 0);
    await new Promise(r => setTimeout(r, 220));
    document.querySelector('#habWeaveTools .hab-tool[data-wtool="notch"]').click();
    await new Promise(r => setTimeout(r, 120));
    say('1 起始 锚点=' + pts().length);
    // 点在两锚点之间的"线"上（直线中点，插值判定也是按直线段算的）
    tap(175, -85);
    await new Promise(r => setTimeout(r, 250));
    say('2 点线上后 锚点=' + pts().length + ' 新点=' + JSON.stringify((pts()[3] || {})));
    // 直接拖这个新锚点
    ev('pointerdown', 175, -85, 1);
    await new Promise(r => setTimeout(r, 60));
    ev('pointermove', 235, -45, 1);
    await new Promise(r => setTimeout(r, 60));
    ev('pointermove', 250, -30, 1);
    ev('pointerup', 250, -30, 0);
    await new Promise(r => setTimeout(r, 220));
    say('3 拖完 锚点=' + pts().length + ' 第4点=' + JSON.stringify(pts()[3] || {}));
    // 重画：清空后连点 5 点，停在"没双击收尾"的状态，看画的时候是不是曲线
    document.getElementById('habWeaveNotchRedraw').click();
    await new Promise(r => setTimeout(r, 250));
    const Q = [[-250,-110],[-60,-250],[170,-150],[190,110],[-10,220]];
    for (const q of Q) { tap(q[0], q[1]); await new Promise(r => setTimeout(r, 40)); }
    say('4 草稿点数=' + (H.weaveEditState().drafts || []).join(','));
    const fit = document.getElementById('habFit'); if (fit) fit.click();
    await new Promise(r => setTimeout(r, 500));
  } catch (e) { say('ERR ' + e.message); }
  window.__QA_DONE = 1;
})();
"""

MENU_JS = r"""
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
  const out = document.createElement('div');
  out.style.cssText = 'position:fixed;left:16px;bottom:110px;z-index:99999;color:#ffd76a;font:12px monospace;background:#000d;padding:6px 8px;max-width:1200px;white-space:pre-wrap';
  (document.getElementById('habitat') || document.body).appendChild(out);
  const log = []; const say = t => { log.push(t); out.textContent = log.join('\n'); };
  window.onerror = (m, s2, l) => say('ERR ' + m + ' @' + l);
  const cv = document.getElementById('habWorld');
  const ev2 = (type, wx, wy, buttons) => {
    const v = H.view(); const r = cv.getBoundingClientRect();
    cv.dispatchEvent(new PointerEvent(type, { clientX: r.left + v.px(wx), clientY: r.top + v.py(wy), button: 0, buttons: buttons, bubbles: true, pointerId: 1, isPrimary: true }));
  };
  try {
    ev2('pointerdown', 0, 0, 1); ev2('pointerup', 0, 0, 0);
    await new Promise(r => setTimeout(r, 250));
    const v = H.view(); const r = cv.getBoundingClientRect();
    cv.dispatchEvent(new MouseEvent('contextmenu', { clientX: r.left + v.px(80), clientY: r.top + v.py(80), bubbles: true, cancelable: true, button: 2 }));
    await new Promise(r => setTimeout(r, 350));
    const labels = Array.from(document.querySelectorAll('#habCtxMenu button')).map(b => b.textContent);
    say('菜单=' + labels.join(' | '));
  } catch (e) { say('ERR ' + e.message); }
})();
"""

src = open(HTML, 'r', encoding='utf-8').read()
cloud = 'window.__QA_CLOUD=%s;' % json.dumps(CLOUD)
for name, body in (('r34-edit', JS), ('r34-menu', MENU_JS)):
    open(os.path.join(TMP, name + '.html'), 'w', encoding='utf-8').write(
        src + '<script>%s</script><script>%s</script>' % (cloud, body))
    print(name)
