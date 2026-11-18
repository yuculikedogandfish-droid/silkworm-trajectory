"""蚕室 QA 变体：放入织网 → 开始 → 强制 u=1 → 点 N 次放大。"""

import sys
from pathlib import Path

INJECT = """
<style id="qa-only-habitat">
  body > *:not(#habitat):not(script):not(style) { display: none !important; }
</style>
<script>
(function () {
  function go() {
    var hab = document.getElementById('habitat');
    if (!hab) return;
    var add = document.getElementById('habAddWeave');
    if (add) add.click();
    setTimeout(function () {
      var start = document.getElementById('habStart');
      if (start) start.click();
    }, 80);
    setTimeout(function () {
      var api = window.__studioHabitat;
      if (api && api.agents) {
        api.agents().forEach(function (a) { if (a.kind === 'weave') a.u = 1; });
      }
      var zin = document.getElementById('habZoomIn');
      for (var k = 0; k < __ZOOM__; k++) { if (zin) zin.click(); }
    }, 1400);
  }
  window.addEventListener('load', function () { setTimeout(go, 600); });
})();
</script>
"""


def main():
    src = Path(sys.argv[1]).read_text(encoding="utf-8")
    dst = Path(sys.argv[2])
    zoom = sys.argv[3] if len(sys.argv) > 3 else "3"
    inject = INJECT.replace("__ZOOM__", zoom)
    idx = src.rfind("</body>")
    src = src[:idx] + inject + src[idx:]
    dst.write_text(src, encoding="utf-8")
    print(f"{dst}  {dst.stat().st_size} bytes")


if __name__ == "__main__":
    main()
