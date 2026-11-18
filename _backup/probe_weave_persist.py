"""验证织网单元的保存/恢复闭环：导出 → 导入 → 重建，把结果写进 body 属性供 --dump-dom 读取。

用法：python _backup\\probe_weave_persist.py docs\\index.html C:\\Temp\\qa-weave-persist.html
"""

import sys
from pathlib import Path

INJECT = """
<script>
(function () {
  function run() {
    var api = window.__studioHabitat;
    if (!api || !api.agents) { document.body.setAttribute('data-qa', 'no-api'); return; }
    var add = document.getElementById('habAddWeave');
    if (add) add.click();
    setTimeout(function () {
      var before = api.agents().find(function (a) { return a.kind === 'weave'; });
      if (!before) { document.body.setAttribute('data-qa', 'no-agent'); return; }
      var beforeInfo = {
        w: before.w, h: before.h, coverage: before.coverage, shape: before.shape,
        worms: before.worms, seed: before.seed, u: before.u,
        paths: before.paths.length, points: before.paths.reduce(function (s, p) { return s + p.pts.length; }, 0),
        walls: before.walls.length
      };
      var ex = api.export();
      var saved = ex.agents.filter(function (a) { return a.kind === 'weave'; })[0];
      api.import(ex);
      var after = api.agents().find(function (a) { return a.kind === 'weave'; });
      var afterInfo = {
        w: after.w, h: after.h, coverage: after.coverage, shape: after.shape,
        worms: after.worms, seed: after.seed, u: after.u,
        paths: after.paths.length, points: after.paths.reduce(function (s, p) { return s + p.pts.length; }, 0),
        walls: after.walls.length
      };
      document.body.setAttribute('data-qa', JSON.stringify({
        savedWeave: saved && saved.weave, before: beforeInfo, after: afterInfo
      }));
    }, 900);
  }
  window.addEventListener('load', function () { setTimeout(run, 500); });
})();
</script>
"""


def main():
    src = Path(sys.argv[1]).read_text(encoding="utf-8")
    dst = Path(sys.argv[2])
    idx = src.rfind("</body>")
    src = src[:idx] + INJECT + src[idx:]
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src, encoding="utf-8")
    print(f"{dst}  {dst.stat().st_size} bytes")


if __name__ == "__main__":
    main()
