# -*- coding: utf-8 -*-
import subprocess, json, os, tempfile
HTML = r"H:\tool\silkworm-trajectory\docs\index.html"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
TMP = tempfile.gettempdir()


def shot(name, js, cloud=True, wait_budget=6000):
    with open(HTML, 'r', encoding='utf-8') as f:
        s = f.read()
    pre = ''
    if cloud:
        cc = json.load(open(r"G:\raby model\trajectories.json", encoding='utf-8'))
        pre = 'window.__QA_CLOUD=%s;' % json.dumps(cc)
    body = '<script>%s%s</script>' % (pre, js)
    s = s.replace('</body>', body + '</body>')
    p = os.path.join(TMP, 'qa-guide-%s.html' % name)
    open(p, 'w', encoding='utf-8').write(s)
    out = os.path.join(TMP, 'guide-%s.png' % name)
    subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--window-size=1600,1000',
                    '--hide-scrollbars', '--virtual-time-budget=%d' % wait_budget,
                    '--screenshot=' + out, 'file:///' + p.replace('\\', '/')], timeout=90)
    print('shot', out, os.path.getsize(out))


BADGE = r"""
function badge(el, txt, dx, dy) {
  const r = el.getBoundingClientRect();
  const b = document.createElement('div');
  b.textContent = txt;
  b.style.cssText = 'position:fixed;z-index:99;left:' + (r.left + (dx||6)) + 'px;top:' + (r.top + (dy||6)) +
    'px;width:26px;height:26px;border-radius:50%;background:#f0b45a;color:#141010;font:700 14px/26px sans-serif;text-align:center;box-shadow:0 0 0 2px rgba(0,0,0,.55)';
  document.body.appendChild(b);
  return r;
}
"""

# 1) 主界面：三块区域标注
JS1 = BADGE + r"""
(async () => {
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

# 2) 编辑态
JS2 = BADGE + r"""
(async () => {
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

# 3) 视频导出区：把左侧栏滚到底，框出四个下拉 + 按钮
JS3 = r"""
(async () => {
  const H = window.__studioHabitat;
  await new Promise(r => setTimeout(r, 260));
  H.addWeave({ w: 240, h: 240 });
  H.seekTo(6);
  await new Promise(r => setTimeout(r, 200));
  const left = document.getElementById('habLeft');
  left.scrollTop = left.scrollHeight;
  await new Promise(r => setTimeout(r, 200));
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

shot('home', JS1)
shot('edit', JS2)
shot('video', JS3, cloud=False)
