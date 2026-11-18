# -*- coding: utf-8 -*-
"""生成 3 个带标注的截图页（只生成 html，截图交给 PowerShell 调用 chrome）"""
import json, os, tempfile
HTML = r"H:\tool\silkworm-trajectory\docs\index.html"
TMP = tempfile.gettempdir()
BADGE = r"""
function badge(el, txt, dx, dy) {
  if (!el) return;
  const r = el.getBoundingClientRect();
  const b = document.createElement('div');
  b.textContent = txt;
  b.style.cssText = 'position:fixed;z-index:99;left:' + (r.left + (dx||6)) + 'px;top:' + (r.top + (dy||6)) +
    'px;width:26px;height:26px;border-radius:50%;background:#f0b45a;color:#141010;font:700 14px/26px sans-serif;text-align:center;box-shadow:0 0 0 2px rgba(0,0,0,.55)';
  document.body.appendChild(b);
}
"""
JS1 = BADGE + r"""
(async () => {
  const s = document.createElement('style');
  s.textContent = 'body > *:not(#habitat):not(script):not(style){display:none}';
  document.head.appendChild(s);
  const H = window.__studioHabitat;
  await new Promise(r => setTimeout(r, 260));
  H.addWeave({ w: 260, h: 260 });
  H.addWeave({ w: 260, h: 260 });
  await H.importPointCloudDoc(window.__QA_CLOUD);
  const us = H.agents().filter(a => a.kind === 'weave');
  if (us[0]) { us[0].x = -190; us[0].y = 0; }
  if (us[1]) { us[1].x = 175; us[1].y = 0; }
  us.forEach(u => H.assignWormToUnit(u.id, 'all'));
  H.seekTo(9);
  await new Promise(r => setTimeout(r, 300));
  badge(document.getElementById('habLeft'), '1', 8, 10);
  badge(document.querySelector('.hab-world'), '2', 10, 10);
  badge(document.getElementById('habRight'), '3', 8, 10);
})();
"""
JS2 = BADGE + r"""
(async () => {
  const s = document.createElement('style');
  s.textContent = 'body > *:not(#habitat):not(script):not(style){display:none}';
  document.head.appendChild(s);
  const H = window.__studioHabitat;
  await new Promise(r => setTimeout(r, 260));
  H.addWeave({ w: 280, h: 280 });
  await H.importPointCloudDoc(window.__QA_CLOUD);
  const u = H.agents().filter(a => a.kind === 'weave')[0];
  if (u) { u.x = 0; u.y = 0; }
  H.assignWormToUnit(u.id, 'all');
  H.seekTo(9);
  await new Promise(r => setTimeout(r, 220));
  const cv = document.getElementById('habWorld');
  const rc = cv.getBoundingClientRect();
  const v = H.view();
  const sx = rc.left + v.px(0) * (rc.width / cv.width), sy = rc.top + v.py(0) * (rc.height / cv.height);
  cv.dispatchEvent(new PointerEvent('pointerdown', { clientX: sx, clientY: sy, bubbles: true, pointerId: 1, button: 0 }));
  cv.dispatchEvent(new PointerEvent('pointerup', { clientX: sx, clientY: sy, bubbles: true, pointerId: 1, button: 0 }));
  await new Promise(r => setTimeout(r, 150));
  document.getElementById('habWeaveEdit').click();
  await new Promise(r => setTimeout(r, 260));
  badge(document.getElementById('habWeaveEdit'), '4', 6, -30);
  badge(document.getElementById('habWeaveEditNote'), '5', 6, -30);
})();
"""
JS3 = r"""
(async () => {
  const s = document.createElement('style');
  s.textContent = 'body > *:not(#habitat):not(script):not(style){display:none}';
  document.head.appendChild(s);
  const H = window.__studioHabitat;
  await new Promise(r => setTimeout(r, 260));
  H.addWeave({ w: 240, h: 240 });
  H.seekTo(6);
  await new Promise(r => setTimeout(r, 200));
  const left = document.getElementById('habLeft');
  left.scrollTop = left.scrollHeight;
  await new Promise(r => setTimeout(r, 260));
  ['habVidRes','habVidSec','habVidFps','habVidBit','habVidRecord','habVidStatus'].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    const r = el.getBoundingClientRect();
    const box = document.createElement('div');
    box.style.cssText = 'position:fixed;z-index:999;pointer-events:none;left:' + (r.left - 6) + 'px;top:' + (r.top - 6) +
      'px;width:' + (r.width + 12) + 'px;height:' + (r.height + 12) + 'px;border:2px solid #f0b45a;border-radius:6px';
    document.body.appendChild(box);
  });
})();
"""

src = open(HTML, 'r', encoding='utf-8').read()
cloud_data = json.load(open(r"G:\raby model\trajectories.json", encoding='utf-8'))
cloud = 'window.__QA_CLOUD=%s;' % json.dumps(cloud_data)

for name, js, use_cloud in (('home', JS1, True), ('edit', JS2, True), ('video', JS3, False)):
    pre = cloud if use_cloud else ''
    s = src.replace('</body>', '<script>%s%s</script></body>' % (pre, js))
    p = os.path.join(TMP, 'qa-guide-%s.html' % name)
    open(p, 'w', encoding='utf-8').write(s)
    print(p)
