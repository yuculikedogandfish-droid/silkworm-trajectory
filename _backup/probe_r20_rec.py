# -*- coding: utf-8 -*-
"""r20 网页端录制探针：真实时间跑 5 秒 720p，检查 MediaRecorder 是否产出数据。
   注意：不能带 --virtual-time-budget（会冻结 performance.now，录制永远停在 0%）。"""
import io

src = r'H:\tool\silkworm-trajectory\docs\index.html'
dst = r'C:\Users\54364\AppData\Local\Temp\qa-r20-rec.html'

INJECT = r'''
<script>
window.addEventListener('load', function () {
  setTimeout(function () {
    try {
      var h = window.__studioHabitat;
      var A = h.agents();
      A.length = 0;
      h.addWeave();
      var res = document.getElementById('habVidRes');
      var sec = document.getElementById('habVidSec');
      var fps = document.getElementById('habVidFps');
      if (res) res.value = '1280x720';
      if (sec) sec.value = '5';
      if (fps) fps.value = '30';
      var t0 = Date.now();
      var iv = setInterval(function () {
        var st = document.getElementById('habVidStatus');
        console.log('QA progress ' + (st ? st.textContent : '') + ' t=' + Math.round((Date.now() - t0) / 100) / 10 + 's');
        if (st && (st.textContent.indexOf('已导出') === 0 || st.textContent.indexOf('失败') === 0)) {
          clearInterval(iv);
          console.log('QA DONE ' + st.textContent);
        }
      }, 1000);
      h.ledRecordWebVideo();
    } catch (e) { console.log('QAERR ' + e.message); }
  }, 700);
});
</script>
'''

with io.open(src, 'r', encoding='utf-8') as f:
    s = f.read()
s = s.replace('</body>', INJECT + '</body>')
with io.open(dst, 'w', encoding='utf-8', newline='') as f:
    f.write(s)
print(dst)
