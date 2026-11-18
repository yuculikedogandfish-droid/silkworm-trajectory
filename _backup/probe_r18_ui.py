# -*- coding: utf-8 -*-
"""r18 UI 快照：放 1 块单元 + 进入编辑（孔洞工具）+ 造一个悬停标签"""
import io

src = r'H:\tool\silkworm-trajectory\docs\index.html'
dst = r'C:\Users\54364\AppData\Local\Temp\qa-r18-ui.html'

INJECT = r'''
<script>
window.addEventListener('load', function () {
  setTimeout(function () {
    try {
      var h = window.__studioHabitat;
      var A = h.agents();
      A.length = 0;
      h.addWeave();
      var a = A[0];
      var btn = document.getElementById('habWeaveEdit');
      if (btn) btn.click();
      var tool = document.querySelector('[data-wtool="hole"]');
      if (tool) tool.click();
      // 模拟鼠标停在孔洞手柄上，展示悬停标签
      setTimeout(function () {
        var cv = document.getElementById('habCanvas');
        var hs = (window.__studioHabitat && window.__studioHabitat.handles) ? window.__studioHabitat.handles() : null;
        if (cv && hs && hs.length) {
          var r = cv.getBoundingClientRect();
          var ev = new PointerEvent('pointermove', {
            clientX: r.left + hs[0].sx, clientY: r.top + hs[0].sy, bubbles: true,
          });
          cv.dispatchEvent(ev);
        }
      }, 400);
      var st = document.createElement('style');
      st.textContent = 'body > *:not(#habitat){display:none!important}#habitat{display:block!important}';
      document.head.appendChild(st);
    } catch (e) {
      document.title = 'QAERR ' + e.message;
    }
  }, 900);
});
</script>
'''

with io.open(src, 'r', encoding='utf-8') as f:
    s = f.read()
s = s.replace('</body>', INJECT + '</body>')
with io.open(dst, 'w', encoding='utf-8', newline='') as f:
    f.write(s)
print(dst)
