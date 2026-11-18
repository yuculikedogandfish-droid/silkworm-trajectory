# -*- coding: utf-8 -*-
"""视图/坐标探针：打印 view 变换、canvas 尺寸与每个单元的屏幕坐标。"""

import sys
from pathlib import Path

TMPL = r"""
<style id="qa-only-habitat">
  body > *:not(#habitat):not(script):not(style) { display: none !important; }
</style>
<style>
  #qaOut { position: fixed; inset: 0; z-index: 99999; background: #141a17; color: #d9efe6;
    font: 13px/1.6 Consolas, monospace; padding: 16px 20px; white-space: pre-wrap; overflow: auto; }
</style>
<script>
(function () {
  window.addEventListener('load', function () {
    setTimeout(function () {
      try {
        var H = window.__studioHabitat;
        var btn = document.getElementById('habAddMosaic');
        if (btn) btn.click();
        setTimeout(function () {
          var v = H.view();
          var cv = document.getElementById('habWorld');
          var r = cv.getBoundingClientRect();
          var out = [];
          out.push('view zoom=' + Math.round(v.s * 1000) / 1000 + ' cx=' + Math.round(v.cx) + ' cy=' + Math.round(v.cy) + ' w=' + v.w + ' h=' + v.h);
          out.push('canvas rect left=' + Math.round(r.left) + ' top=' + Math.round(r.top) + ' w=' + Math.round(r.width) + ' h=' + Math.round(r.height));
          out.push('scrollY=' + window.scrollY + ' innerH=' + window.innerHeight + ' docH=' + document.documentElement.scrollHeight);
          H.agents().filter(function (a) { return a.kind === 'weave'; }).forEach(function (a) {
            out.push(a.id + ' world(' + Math.round(a.x) + ',' + Math.round(a.y) + ') screen(' + Math.round(v.px(a.x)) + ',' + Math.round(v.py(a.y)) + ')');
          });
          var pre = document.createElement('pre');
          pre.id = 'qaOut';
          pre.textContent = out.join('\n');
          document.getElementById('habitat').appendChild(pre);
        }, 300);
      } catch (e) { console.log('probe error ' + e); }
    }, 1200);
  });
})();
</script>
"""


def main():
    src = Path(sys.argv[1]).read_text(encoding="utf-8")
    dst = Path(sys.argv[2])
    idx = src.rfind("</body>")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src[:idx] + TMPL + src[idx:], encoding="utf-8")
    print(f"{dst} {dst.stat().st_size} bytes")


if __name__ == "__main__":
    main()
