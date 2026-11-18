# -*- coding: utf-8 -*-
"""手柄可视化 QA：放入织网单元 → 开始 → 进入形状编辑（显示手柄）→ u=1。

用法：python _backup\make_weave_handles_qa.py docs\index.html C:\Temp\qa-handles.html
"""

import sys
from pathlib import Path

INJECT = r"""
<style>body > *:not(#habitat):not(script):not(style){display:none!important}</style>
<script>
(function () {
  function go() {
    var add = document.getElementById('habAddWeave');
    if (add) add.click();
    setTimeout(function () {
      var start = document.getElementById('habStart');
      if (start) start.click();
      var edit = document.getElementById('habWeaveEdit');
      if (edit) edit.click();
      var api = window.__studioHabitat;
      if (api && api.agents) api.agents().forEach(function (a) { if (a.kind === 'weave') a.u = 1; });
    }, 900);
  }
  window.addEventListener('load', function () { setTimeout(go, 700); });
})();
</script>
"""


def main():
    src = Path(sys.argv[1]).read_text(encoding="utf-8")
    dst = Path(sys.argv[2])
    idx = src.rfind("</body>")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src[:idx] + INJECT + src[idx:], encoding="utf-8")
    print(f"{dst} {dst.stat().st_size} bytes")


if __name__ == "__main__":
    main()
