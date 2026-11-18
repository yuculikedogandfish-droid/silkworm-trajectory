"""生成蚕室织网单元的 QA 副本：自动点「放入织网单元」+「开始」，滚动到蚕室。

用法：python _backup\\make_weave_qa.py docs\\index.html C:\\Temp\\qa-weave.html
"""

import sys
from pathlib import Path

INJECT = """
<style id="qa-only-habitat">
  body > *:not(#habitat):not(script):not(style) { display: none !important; }
</style>
<script>
(function () {
  var HOLD = __HOLD__;
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
      if (HOLD) return;
      var api = window.__studioHabitat;
      if (api && api.agents) {
        api.agents().forEach(function (a) { if (a.kind === 'weave') a.u = 1; });
      }
    }, 1400);
  }
  window.addEventListener('load', function () { setTimeout(go, 600); });
})();
</script>
"""


def main():
    src = Path(sys.argv[1]).read_text(encoding="utf-8")
    dst = Path(sys.argv[2])
    hold = len(sys.argv) > 3 and sys.argv[3] == "hold"
    inject = INJECT.replace("__HOLD__", "true" if hold else "false")
    idx = src.rfind("</body>")
    if idx < 0:
        raise SystemExit("没有 </body>")
    # 注意：文件里第一个 </body> 属于 iframe 的 srcdoc，必须插到外层文档末尾
    src = src[:idx] + inject + src[idx:]
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src, encoding="utf-8")
    print(f"{dst}  {dst.stat().st_size} bytes")


if __name__ == "__main__":
    main()
