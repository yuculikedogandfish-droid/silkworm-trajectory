# -*- coding: utf-8 -*-
"""第二张截图：自定义尺寸展开态"""
import os, tempfile

HTML = r"H:\tool\silkworm-trajectory\docs\index.html"
TMP = tempfile.gettempdir()

JS = r"""
(async () => {
  const s = document.createElement('style');
  s.textContent = 'body > *:not(#habitat):not(script):not(style){display:none}';
  document.head.appendChild(s);
  await new Promise(r => setTimeout(r, 400));
  const sel = document.getElementById('habVidRes');
  sel.value = 'custom';
  sel.dispatchEvent(new Event('change'));
  const wi = document.getElementById('habVidW'), hi = document.getElementById('habVidH');
  wi.value = '2048'; hi.value = '1536';
  wi.dispatchEvent(new Event('input'));
  hi.dispatchEvent(new Event('input'));
  document.getElementById('habLeft').scrollTop = document.getElementById('habLeft').scrollHeight;
})();
"""

src = open(HTML, 'r', encoding='utf-8').read()
p = os.path.join(TMP, 'qa-guide-video2.html')
open(p, 'w', encoding='utf-8').write(src.replace('</body>', '<script>%s</script></body>' % JS))
print(p)
