# -*- coding: utf-8 -*-
"""QA：图片导出路径（离屏合成）像素统计 + 右侧/左栏新控件截图页"""
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
  H.seekTo(12);

  // 直接量图片合成：2048×1536 下统计非黑像素比例
  const results = [];
  for (const spec of ['2048x1536', '1280x960']) {
    const sel = document.getElementById('habVidRes');
    if (![...sel.options].some(o => o.value === spec)) { results.push(spec + ':noopt'); continue; }
    sel.value = spec;
    sel.dispatchEvent(new Event('change'));
    const W = parseInt(spec.split('x')[0], 10), HH = parseInt(spec.split('x')[1], 10);
    const cv = document.createElement('canvas'); cv.width = W; cv.height = HH;
    const g = cv.getContext('2d', { alpha: false });
    const scene = H.ledScene();
    const frames = scene.frames || 900, fps = scene.fps || 30;
    const T = Math.max(0, Math.min(1, (H.view ? 0 : 0) + 12 / (frames / fps)));
    H.ledComposeFrame(g, scene, T, false, W, HH, []);
    const data = g.getImageData(0, 0, W, HH).data;
    let lit = 0, sum = 0;
    for (let i = 0; i < data.length; i += 4) {
      const v = (data[i] + data[i + 1] + data[i + 2]) / 3;
      sum += v;
      if (v > 12) lit++;
    }
    const px = data.length / 4;
    results.push(spec + ':lit=' + (lit / px * 100).toFixed(1) + '%:avg=' + (sum / px).toFixed(1));
  }
  // 也要确认真实入口不抛错
  try { H.ledExportImage(); results.push('export:ok'); } catch (e) { results.push('export:err:' + e.message); }
  document.title = 'QA:: ' + results.join(' | ');
  document.getElementById('habLeft').scrollTop = document.getElementById('habLeft').scrollHeight;
})();
"""

src = open(HTML, 'r', encoding='utf-8').read()
p = os.path.join(TMP, 'qa-img-export.html')
open(p, 'w', encoding='utf-8').write(
    src.replace('</body>', '<script>window.__QA_CLOUD=%s;</script><script>%s</script></body>'
                % (json.dumps(CLOUD), JS)))
print(p)
