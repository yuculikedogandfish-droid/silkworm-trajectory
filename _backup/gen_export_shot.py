# -*- coding: utf-8 -*-
"""截图页：左栏导出区（视频+图片）与右栏隐藏开关"""
import json, os, tempfile

HTML = r"H:\tool\silkworm-trajectory\docs\index.html"
TMP = os.environ.get('TEMP', r'C:\Users\54364\AppData\Local\Temp')
CLOUD = json.load(open(r"G:\raby model\trajectories.json", encoding='utf-8'))

JS = r"""
(async () => {
  const s = document.createElement('style');
  s.textContent = 'body > *:not(#habitat):not(script):not(style){display:none}';
  document.head.appendChild(s);
  await new Promise(r => setTimeout(r, 400));
  const H = window.__studioHabitat;
  H.addWeave({ w: 300, h: 300 });
  H.addWeave({ w: 300, h: 300 });
  await H.importPointCloudDoc(window.__QA_CLOUD);
  const us = H.agents().filter(a => a.kind === 'weave');
  if (us[0]) { us[0].x = -190; us[0].y = 0; }
  if (us[1]) { us[1].x = 175; us[1].y = 0; }
  us.forEach(u => H.assignWormToUnit(u.id, 'all'));
  H.seekTo(10);
  await new Promise(r => setTimeout(r, 300));
  document.getElementById('habLeft').scrollTop = document.getElementById('habLeft').scrollHeight;
})();
"""

src = open(HTML, 'r', encoding='utf-8').read()
p = os.path.join(TMP, 'qa-guide-export.html')
open(p, 'w', encoding='utf-8').write(
    src.replace('</body>', '<script>window.__QA_CLOUD=%s;</script><script>%s</script></body>'
                % (json.dumps(CLOUD), JS)))
print(p)
