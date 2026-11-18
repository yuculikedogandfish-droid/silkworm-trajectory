"""逐个形状重建织网单元，统计墙体/丝线数量，写进 body[data-qa]。

用法：python _backup\\probe_weave_shapes.py docs\\index.html C:\\Temp\\qa-weave-shapes.html
"""

import sys
from pathlib import Path

INJECT = """
<script>
(function () {
  function run() {
    var api = window.__studioHabitat;
    if (!api || !api.agents) { document.body.setAttribute('data-qa', 'no-api'); return; }
    document.getElementById('habAddWeave').click();
    var sel = document.getElementById('habWeaveShape');
    var out = [];
    var shapes = ['plain', 'notch', 'island', 'notchIsland'];
    var i = 0;
    function next() {
      if (i >= shapes.length) {
        document.body.setAttribute('data-qa', JSON.stringify(out));
        return;
      }
      var shape = shapes[i++];
      sel.value = shape;
      sel.dispatchEvent(new Event('change'));
      document.getElementById('habWeaveRebuild').click();
      var a = api.agents().filter(function (x) { return x.kind === 'weave'; })[0];
      if (a) {
        out.push({
          shape: shape, w: a.w, h: a.h, walls: a.walls.length,
          wallPts: a.walls.reduce(function (s, l) { return s + l.length; }, 0),
          paths: a.paths.length,
          points: a.paths.reduce(function (s, p) { return s + p.pts.length; }, 0)
        });
      }
      setTimeout(next, 350);
    }
    setTimeout(next, 400);
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
