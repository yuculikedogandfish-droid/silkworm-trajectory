# -*- coding: utf-8 -*-
"""r20 布局量测：页面宽 / 舞台宽 / 两侧栏右边界 / 是否溢出视口"""
import io

src = r'H:\tool\silkworm-trajectory\docs\index.html'
dst = r'C:\Users\54364\AppData\Local\Temp\qa-r20-measure.html'

INJECT = r'''
<script>
window.addEventListener('load', function () {
  setTimeout(function () {
    try {
      var h = window.__studioHabitat;
      h.addWeave();
      var st = document.createElement('style');
      st.textContent = 'body > *:not(#habitat){display:none!important}#habitat{display:block!important}';
      document.head.appendChild(st);
      setTimeout(function () {
        var de = document.documentElement;
        var hab = document.getElementById('habitat').getBoundingClientRect();
        var stage = document.querySelector('.hab-stage').getBoundingClientRect();
        var L = document.getElementById('habLeft').getBoundingClientRect();
        var R = document.getElementById('habRight').getBoundingClientRect();
        var W = document.getElementById('habWorldWrap').getBoundingClientRect();
        var msg = 'QA vw=' + de.clientWidth + ' scrollW=' + de.scrollWidth +
          ' habW=' + Math.round(hab.width) + ' stage=' + Math.round(stage.left) + '..' + Math.round(stage.right) +
          ' L=' + Math.round(L.left) + '..' + Math.round(L.right) +
          ' W=' + Math.round(W.left) + '..' + Math.round(W.right) +
          ' R=' + Math.round(R.left) + '..' + Math.round(R.right) +
          ' Rscroll=' + document.getElementById('habRight').scrollWidth + '/' + document.getElementById('habRight').clientWidth +
          ' stageH=' + Math.round(stage.height) + ' vh=' + window.innerHeight;
        document.title = msg;
        console.log(msg);
      }, 600);
    } catch (e) { document.title = 'QAERR ' + e.message; console.log(document.title); }
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
