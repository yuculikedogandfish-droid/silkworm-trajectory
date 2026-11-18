# -*- coding: utf-8 -*-
"""QA：视频分辨率下拉 + 自定义尺寸比例提示；结果写进 document.title 便于 dump-dom 读取"""
import os, tempfile, sys

HTML = r"H:\tool\silkworm-trajectory\docs\index.html"
TMP = tempfile.gettempdir()

JS = r"""
(async () => {
  const s = document.createElement('style');
  s.textContent = 'body > *:not(#habitat):not(script):not(style){display:none}';
  document.head.appendChild(s);
  await new Promise(r => setTimeout(r, 400));
  const out = [];
  const sel = document.getElementById('habVidRes');
  const wi = document.getElementById('habVidW');
  const hi = document.getElementById('habVidH');
  function probe(v, w, h) {
    sel.value = v;
    sel.dispatchEvent(new Event('change'));
    if (w) wi.value = w;
    if (h) hi.value = h;
    if (w) wi.dispatchEvent(new Event('input'));
    if (h) hi.dispatchEvent(new Event('input'));
    out.push(v + '->' + document.getElementById('habVidRatio').textContent.replace(/\s+/g, '') +
      '/row=' + document.getElementById('habVidCustomRow').style.display +
      '/w=' + wi.value + 'h=' + hi.value);
  }
  probe('2048x1536');
  probe('2093x1573');
  probe('1920x1080');
  probe('custom', 1600, 1200);
  probe('custom', 2049, 1537);
  probe('2048x1536');
  document.title = 'QA:: ' + out.join(' | ');
  document.getElementById('habLeft').scrollTop = document.getElementById('habLeft').scrollHeight;
})();
"""

src = open(HTML, 'r', encoding='utf-8').read()
p = os.path.join(TMP, 'qa-guide-video.html')
open(p, 'w', encoding='utf-8').write(src.replace('</body>', '<script>%s</script></body>' % JS))
print(p)
