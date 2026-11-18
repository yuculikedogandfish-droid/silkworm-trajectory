# -*- coding: utf-8 -*-
"""半程截图：放一个织网单元并推进到 u=0.5，检查单格渲染 + 吐丝头。

用法：python _backup\probe_weave_mid.py docs\index.html C:\Temp\qa-mid.html 0.5
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
        var add = document.getElementById('habAddWeave');
        if (add) add.click();
        setTimeout(function () {
          var a = H.agents().filter(function (x) { return x.kind === 'weave'; }).pop();
          if (a) { a.u = __U__; a.mode = 'run'; }
        }, 120);
      } catch (e) { console.log('probe error ' + e); }
    }, 1200);
  });
})();
</script>
"""


def main():
    src = Path(sys.argv[1]).read_text(encoding="utf-8")
    dst = Path(sys.argv[2])
    u = sys.argv[3] if len(sys.argv) > 3 else "0.5"
    idx = src.rfind("</body>")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src[:idx] + TMPL.replace("__U__", u) + src[idx:], encoding="utf-8")
    print(f"{dst} {dst.stat().st_size} bytes")


if __name__ == "__main__":
    main()
