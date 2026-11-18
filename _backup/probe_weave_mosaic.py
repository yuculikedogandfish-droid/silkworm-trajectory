# -*- coding: utf-8 -*-
"""块群截图：点「铺块群」，把每个单元推到 u=0.85，检查有限块群/分层/块缝。

用法：python _backup\probe_weave_mosaic.py docs\index.html C:\Temp\qa-mosaic.html 0.85
"""

import sys
from pathlib import Path

TMPL = r"""
<style id="qa-only-habitat">
  body > *:not(#habitat):not(script):not(style) { display: none !important; }
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
          H.agents().forEach(function (a) {
            if (a.kind === 'weave') { a.u = __U__; a.mode = 'idle'; }
          });
          // canvas 很高，把页面滚到场地中心，截图才看得到整片块群
          var cv = document.getElementById('habWorld');
          var r = cv.getBoundingClientRect();
          window.scrollTo(0, window.scrollY + r.top + r.height / 2 - window.innerHeight / 2);
        }, 200);
      } catch (e) { console.log('probe error ' + e); }
    }, 1200);
  });
})();
</script>
"""


def main():
    src = Path(sys.argv[1]).read_text(encoding="utf-8")
    dst = Path(sys.argv[2])
    u = sys.argv[3] if len(sys.argv) > 3 else "0.85"
    idx = src.rfind("</body>")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src[:idx] + TMPL.replace("__U__", u) + src[idx:], encoding="utf-8")
    print(f"{dst} {dst.stat().st_size} bytes")


if __name__ == "__main__":
    main()
