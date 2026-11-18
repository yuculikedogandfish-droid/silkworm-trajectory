# -*- coding: utf-8 -*-
"""QA r30：点格即编辑 / 切格 / 右键删孔 / 画壁 / 点空白退出且壁隐藏"""
import json, os

HTML = r"H:\tool\silkworm-trajectory\docs\index.html"
TMP = os.environ.get('TEMP', r'C:\Users\54364\AppData\Local\Temp')
CLOUD = json.load(open(r"G:\raby model\trajectories.json", encoding='utf-8'))

BASE = r"""
(async () => {
  const s = document.createElement('style');
  s.textContent = 'body > *:not(#habitat):not(script):not(style){display:none}';
  document.head.appendChild(s);
  await new Promise(r => setTimeout(r, 350));
  const H = window.__studioHabitat;
  H.addWeave({ w: 300, h: 300 });
  H.addWeave({ w: 300, h: 300 });
  await H.importPointCloudDoc(window.__QA_CLOUD);
  const us = H.agents().filter(a => a.kind === 'weave');
  if (us[0]) { us[0].x = -190; us[0].y = 0; }
  if (us[1]) { us[1].x = 175; us[1].y = 0; }
  us.forEach(u => H.assignWormToUnit(u.id, 'all'));
  H.seekTo(9);

  window.__weaveTrace = [];
  const status = [];
  const out = document.createElement('div');
  out.style.cssText = 'position:fixed;left:16px;bottom:110px;z-index:99999;color:#ffd76a;font:13px monospace;background:#000d;padding:6px 8px;max-width:1100px;white-space:pre-wrap';
  (document.getElementById('habitat') || document.body).appendChild(out);
  const say = (t) => { status.push(t); out.textContent = status.join('\n'); };

  const cv = document.getElementById('habWorld');
  const pd = (wx, wy) => {
    const v = H.view(); const r = cv.getBoundingClientRect();
    cv.dispatchEvent(new PointerEvent('pointerdown', {
      clientX: r.left + v.px(wx), clientY: r.top + v.py(wy),
      button: 0, buttons: 1, bubbles: true, pointerId: 1, isPrimary: true,
    }));
  };
  const rc = (wx, wy) => {
    const v = H.view(); const r = cv.getBoundingClientRect();
    cv.dispatchEvent(new MouseEvent('contextmenu', {
      clientX: r.left + v.px(wx), clientY: r.top + v.py(wy),
      bubbles: true, cancelable: true, button: 2,
    }));
  };
  const lum = (wx, wy) => {
    const g = cv.getContext('2d'); const v = H.view();
    const cxp = Math.round(v.px(wx)), cyp = Math.round(v.py(wy));
    const d = g.getImageData(cxp - 12, cyp - 12, 24, 24).data;
    let sum = 0; for (let i = 0; i < d.length; i += 4) sum += (d[i] + d[i + 1] + d[i + 2]) / 3;
    return Math.round(sum / (d.length / 4));
  };

  try {
    pd(-190, 0);
    await new Promise(r => setTimeout(r, 150));
    say('1 点格后按钮=' + document.getElementById('habWeaveEdit').textContent.trim());

    pd(175, 0);
    await new Promise(r => setTimeout(r, 150));
    say('2 点第2块后=' + JSON.stringify(H.weaveEditState()));

    const holesA = (H.weaveCellContent(us[1], 0, 0).cell.islands || []).length;
    const isl0 = (H.weaveCellContent(us[1], 0, 0).cell.islands || [])[0];
    const hx = us[1].x + (isl0 ? isl0.cx : 0);
    const hy = us[1].y + (isl0 ? isl0.cy : 0);
    rc(hx, hy);
    await new Promise(r => setTimeout(r, 300));
    say('2b 孔数 ' + holesA + ' -> ' + ((H.weaveCellContent(us[1], 0, 0).cell.islands || []).length) +
        ' @孔心 ' + Math.round(hx) + ',' + Math.round(hy));

    const wallBtn = document.querySelector('#habWeaveTools .hab-tool[data-wtool="wall"]');
    if (wallBtn) wallBtn.click();
    await new Promise(r => setTimeout(r, 80));
    say('3 加壁按下=' + (wallBtn ? wallBtn.getAttribute('aria-pressed') : 'none') + ' ' + JSON.stringify(H.weaveEditState()));
    pd(115, -80); await new Promise(r => setTimeout(r, 50));
    pd(175, -20); await new Promise(r => setTimeout(r, 50));
    pd(235, -80); await new Promise(r => setTimeout(r, 50));
    document.getElementById('habWeaveEditEnd').click();
    await new Promise(r => setTimeout(r, 250));
    say('4 壁顶点=' + ((us[1].custom.walls['0,0'] || []).map(l => (l.pts || l).length).join('/') || '0'));

    %FINAL%
  } catch (err) {
    say('ERR ' + err.message);
  }
})();
"""

FINAL_EDIT = r"""
    await new Promise(r => setTimeout(r, 250));
"""

FINAL_EXIT = r"""
    pd(0, 430);
    await new Promise(r => setTimeout(r, 350));
    say('6 退出后按钮=' + document.getElementById('habWeaveEdit').textContent.trim());
"""

src = open(HTML, 'r', encoding='utf-8').read()
cloud = 'window.__QA_CLOUD=%s;' % json.dumps(CLOUD)
for name, final in (('wall', FINAL_EDIT), ('exit', FINAL_EXIT)):
    js = BASE.replace('%FINAL%', final)
    p = os.path.join(TMP, 'qa-r30-%s.html' % name)
    open(p, 'w', encoding='utf-8').write(
        src.replace('</body>', '<script>%s</script><script>%s</script></body>' % (cloud, js)))
    print(p)
