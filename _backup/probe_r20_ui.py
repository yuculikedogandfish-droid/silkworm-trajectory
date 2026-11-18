# -*- coding: utf-8 -*-
"""r20 UI 探针：放 1 块单元 →「编辑这一格」→ 孔洞工具 → 悬停手柄，
   同时量出舞台高度 / 侧栏滚动情况，并把结果写进 document.title（便于回读）。"""
import io

src = r'H:\tool\silkworm-trajectory\docs\index.html'
dst = r'C:\Users\54364\AppData\Local\Temp\qa-r20-ui.html'

INJECT = r'''
<script>
window.addEventListener('load', function () {
  setTimeout(function () {
    try {
      var h = window.__studioHabitat;
      var A = h.agents();
      A.length = 0;
      h.addWeave();
      A[0].x = 0; A[0].y = 0;
      var btn = document.getElementById('habWeaveEdit');
      if (btn) btn.click();
      var tool = document.querySelector('[data-wtool="hole"]');
      if (tool) tool.click();
      var st = document.createElement('style');
      st.textContent = 'body > *:not(#habitat){display:none!important}#habitat{display:block!important}';
      document.head.appendChild(st);
      setTimeout(function () {
        var stage = document.querySelector('.hab-stage').getBoundingClientRect();
        var sideL = document.getElementById('habLeft');
        var hud = document.getElementById('habEditHud');
        document.title = 'QA stageH=' + Math.round(stage.height) +
          ' win=' + window.innerHeight +
          ' leftScroll=' + sideL.scrollHeight + '/' + sideL.clientHeight +
          ' hudHidden=' + (hud ? hud.hidden : 'nohud') +
          ' hud="' + (hud ? hud.textContent.replace(/\s+/g, ' ').slice(0, 120) : '') + '"';
        console.log(document.title);
      }, 500);
    } catch (e) {
      document.title = 'QAERR ' + e.message;
      console.log(document.title);
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
