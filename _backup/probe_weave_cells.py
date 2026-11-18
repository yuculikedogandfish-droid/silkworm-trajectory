"""读取织网格网的 cell 几何与丝线，验证尺寸/数量。"""

import sys
from pathlib import Path

INJECT = """
<script>
(function () {
  function run() {
    var api = window.__studioHabitat;
    if (!api || !api.agents) { document.body.setAttribute('data-qa', 'no-api'); return; }
    document.getElementById('habAddWeave').click();
    setTimeout(function () {
      var a = api.agents().filter(function (x) { return x.kind === 'weave'; })[0];
      var out = { w: a.w, h: a.h, sample: a.sample, cells: [] };
      [[0, 0], [1, 0], [0, 1], [-1, -1]].forEach(function (p) {
        var c = a.cache && a.cache.get(p[0] + ',' + p[1]);
        if (!c) { out.cells.push({ ix: p[0], iy: p[1], missing: true }); return; }
        var minx = 1e9, maxx = -1e9, miny = 1e9, maxy = -1e9;
        c.walls.forEach(function (line) {
          line.forEach(function (q) {
            minx = Math.min(minx, q.x); maxx = Math.max(maxx, q.x);
            miny = Math.min(miny, q.y); maxy = Math.max(maxy, q.y);
          });
        });
        out.cells.push({
          ix: p[0], iy: p[1], walls: c.walls.length,
          bbox: [Math.round(minx), Math.round(maxx), Math.round(miny), Math.round(maxy)],
          paths: c.paths.length,
          points: c.paths.reduce(function (s, q) { return s + q.pts.length; }, 0)
        });
      });
      document.body.setAttribute('data-qa', JSON.stringify(out));
    }, 800);
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
    dst.write_text(src, encoding="utf-8")
    print(dst)


if __name__ == "__main__":
    main()
