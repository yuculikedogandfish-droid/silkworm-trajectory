# -*- coding: utf-8 -*-
"""QA r29：隐藏蚕/丝 三态截图 + 图片导出（离屏合成）像素统计"""
import json, os, tempfile

HTML = r"H:\tool\silkworm-trajectory\docs\index.html"
TMP = os.environ.get('TEMP', r'C:\Users\54364\AppData\Local\Temp')
CLOUD = json.load(open(r"G:\raby model\trajectories.json", encoding='utf-8'))

SETUP = r"""
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
  window.__QA_H = H;
})();
"""

MODES = {
    'normal': "",
    'nobody': "window.__QA_H.setHide({ bodies: true });",
    'nosilk': "window.__QA_H.setHide({ silk: true });",
}

# 给页面加一个 setHide 便携入口（仅截图脚本注入，不改主程序）
BRIDGE = r"""
window.__qaSetHide = (o) => {
  const H = window.__studioHabitat;
  const cb = document.getElementById('habHideAllBody');
  const cs = document.getElementById('habHideAllSilk');
  if ('bodies' in o && cb) { cb.checked = !!o.bodies; cb.dispatchEvent(new Event('change')); }
  if ('silk' in o && cs) { cs.checked = !!o.silk; cs.dispatchEvent(new Event('change')); }
};
"""

src = open(HTML, 'r', encoding='utf-8').read()
cloud = 'window.__QA_CLOUD=%s;' % json.dumps(CLOUD)
for name, extra in MODES.items():
    js = cloud + SETUP + BRIDGE + r"""
(async () => {
  await new Promise(r => setTimeout(r, 400));
  %s
  await new Promise(r => setTimeout(r, 350));
})();
""" % extra.replace('window.__QA_H.setHide', 'window.__qaSetHide')
    p = os.path.join(TMP, 'qa-hide-%s.html' % name)
    open(p, 'w', encoding='utf-8').write(src.replace('</body>', '<script>%s</script></body>' % js))
    print(p)
