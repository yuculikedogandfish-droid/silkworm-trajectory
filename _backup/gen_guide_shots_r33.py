# -*- coding: utf-8 -*-
"""r33 说明书配图：干净界面截图（无调试条）"""
import json, os

HTML = r"H:\tool\silkworm-trajectory\docs\index.html"
TMP = os.environ.get('TEMP', r'C:\Users\54364\AppData\Local\Temp')
CLOUD = json.load(open(r"G:\raby model\trajectories.json", encoding='utf-8'))

HEAD = r"""
(async () => {
  const st = document.createElement('style');
  st.textContent = 'body > *:not(#habitat):not(#habCtxMenu):not(script):not(style){display:none}';
  document.head.appendChild(st);
  await new Promise(r => setTimeout(r, 900));
  const H = window.__studioHabitat;
  H.addWeave({});
  await H.importPointCloudDoc(window.__QA_CLOUD);
  const us = H.agents().filter(a => a.kind === 'weave');
  const cv = document.getElementById('habWorld');
  const v0 = () => H.view();
  const tap = (wx, wy) => {
    const v = v0(); const r = cv.getBoundingClientRect();
    cv.dispatchEvent(new PointerEvent('pointerdown', { clientX: r.left + v.px(wx), clientY: r.top + v.py(wy), button: 0, buttons: 1, bubbles: true, pointerId: 1, isPrimary: true }));
    cv.dispatchEvent(new PointerEvent('pointerup', { clientX: r.left + v.px(wx), clientY: r.top + v.py(wy), button: 0, buttons: 0, bubbles: true, pointerId: 1, isPrimary: true }));
  };
"""

HOME = HEAD + r"""
  us.forEach((u, i) => {
    u.w = i ? 460 : 620; u.h = i ? 460 : 620;
    u.x = i ? 420 : -260; u.y = i ? 90 : -40;
    u.tileField = false; u.shape = 'island'; u.seed = 101 + i * 202;
    if (u.cache && u.cache.clear) u.cache.clear();
    H.buildWeave(u);
    H.assignWormToUnit(u.id, 'all');
  });
  H.seekTo(7);
  document.getElementById('habFit') && document.getElementById('habFit').click();
  await new Promise(r => setTimeout(r, 500));
})();
"""

EDIT = HEAD + r"""
  const a = us[0];
  a.w = 620; a.h = 620; a.x = 0; a.y = 0; a.tileField = false; a.shape = 'plain'; a.seed = 3141;
  a.custom = a.custom || { walls: {}, paths: {}, shapes: {} };
  a.custom.shapes['0,0'] = { notch: null, islands: [{ cx: 20, cy: 30, r: 105 }], notchPts: [
    {x:-250,y:-110},{x:-60,y:-250},{x:170,y:-150},{x:190,y:110},{x:-10,y:220},{x:-225,y:110}] };
  if (a.cache && a.cache.clear) a.cache.clear();
  H.buildWeave(a);
  H.assignWormToUnit(a.id, 'all');
  H.seekTo(7);
  tap(0, 0);
  await new Promise(r => setTimeout(r, 200));
  document.querySelector('#habWeaveTools .hab-tool[data-wtool="notch"]').click();
  await new Promise(r => setTimeout(r, 300));
  document.getElementById('habFit') && document.getElementById('habFit').click();
  await new Promise(r => setTimeout(r, 500));
})();
"""

MENU = HEAD + r"""
  const a = us[0];
  a.w = 620; a.h = 620; a.x = 0; a.y = 0; a.tileField = false; a.shape = 'plain'; a.seed = 3141;
  a.custom = a.custom || { walls: {}, paths: {}, shapes: {} };
  a.custom.shapes['0,0'] = { notch: null, islands: [], notchPts: [
    {x:-250,y:-110},{x:-60,y:-250},{x:170,y:-150},{x:190,y:110},{x:-10,y:220},{x:-225,y:110}] };
  if (a.cache && a.cache.clear) a.cache.clear();
  H.buildWeave(a);
  H.assignWormToUnit(a.id, 'all');
  H.seekTo(7);
  tap(0, 0);
  await new Promise(r => setTimeout(r, 200));
  document.querySelector('#habWeaveTools .hab-tool[data-wtool="notch"]').click();
  await new Promise(r => setTimeout(r, 250));
  document.getElementById('habFit') && document.getElementById('habFit').click();
  await new Promise(r => setTimeout(r, 400));
  const v = H.view(); const r = cv.getBoundingClientRect();
  cv.dispatchEvent(new MouseEvent('contextmenu', {
    clientX: r.left + v.px(170), clientY: r.top + v.py(-150),
    bubbles: true, cancelable: true, button: 2,
  }));
  await new Promise(r => setTimeout(r, 400));
})();
"""

src = open(HTML, 'r', encoding='utf-8').read()
cloud = 'window.__QA_CLOUD=%s;' % json.dumps(CLOUD)
for name, body in (('guide33-home', HOME), ('guide33-edit', EDIT), ('guide33-menu', MENU)):
    open(os.path.join(TMP, name + '.html'), 'w', encoding='utf-8').write(
        src + '<script>%s</script><script>%s</script>' % (cloud, body))
    print(name)
