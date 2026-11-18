# -*- coding: utf-8 -*-
"""r20 侧栏宽度来源诊断：computed width / min-width / 最宽子元素"""
import io

src = r'H:\tool\silkworm-trajectory\docs\index.html'
dst = r'C:\Users\54364\AppData\Local\Temp\qa-r20-diag.html'

INJECT = r'''
<script>
window.addEventListener('load', function () {
  setTimeout(function () {
    try {
      var st = document.createElement('style');
      st.textContent = 'body > *:not(#habitat){display:none!important}#habitat{display:block!important}';
      document.head.appendChild(st);
      setTimeout(function () {
        var out = [];
        ['habLeft', 'habRight'].forEach(function (id) {
          var el = document.getElementById(id);
          var cs = getComputedStyle(el);
          var w = 0, who = '';
          Array.prototype.forEach.call(el.querySelectorAll('*'), function (c) {
            var r = c.getBoundingClientRect().width;
            if (r > w) { w = r; who = c.tagName + '.' + (c.className || '') + '#' + (c.id || ''); }
          });
          out.push(id + ' width=' + cs.width + ' minW=' + cs.minWidth + ' maxW=' + cs.maxWidth +
            ' box=' + Math.round(el.getBoundingClientRect().width) +
            ' widest=' + Math.round(w) + ' (' + who + ')');
        });
        var g = getComputedStyle(document.querySelector('.hab-stage'));
        out.push('grid=' + g.gridTemplateColumns);
        console.log('QA ' + out.join(' | '));
      }, 600);
    } catch (e) { console.log('QAERR ' + e.message); }
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
