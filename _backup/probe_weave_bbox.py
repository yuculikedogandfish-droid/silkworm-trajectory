"""织格探针：读取每格路径 bbox 与视口参数，定位外圈丝线缺失问题。"""

import sys
from pathlib import Path

INJECT = """
<script>
(function () {
  function bboxOf(pts) {
    var xs = [], ys = [];
    pts.forEach(function (p) { if (isFinite(p.x) && isFinite(p.y)) { xs.push(p.x); ys.push(p.y); } });
    if (!xs.length) return null;
    return [Math.min.apply(null, xs).toFixed(1), Math.max.apply(null, xs).toFixed(1),
            Math.min.apply(null, ys).toFixed(1), Math.max.apply(null, ys).toFixed(1)];
  }
  function run() {
    var api = window.__studioHabitat;
    if (!api || !api.agents) { document.body.setAttribute('data-qa', 'no-api'); return; }
    document.getElementById('habAddWeave').click();
    setTimeout(function () {
      var a = api.agents().filter(function (x) { return x.kind === 'weave'; })[0];
      var v = api.view();
      var out = { agent: { x: a.x, y: a.y, w: a.w, h: a.h, u: a.u, mode: a.mode,
                          sample: a.sample, cache: a.cache ? a.cache.size : 0 },
                  view: v, cells: {} };
      [[0,0],[1,0],[2,0],[3,0],[-1,0],[5,0],[0,1],[0,3],[8,0],[8,3]].forEach(function (c) {
        var content = api.weaveCellContent(a, c[0], c[1]);
        out.cells[c.join(',')] = (content.paths || []).map(function (p) { return bboxOf(p.pts); });
      });
      var c00 = api.weaveCellContent(a, 0, 0);
      out.firstPathPts = c00.paths[0] ? c00.paths[0].pts.slice(0, 6).map(function (p) {
        return [p.x.toFixed(1), p.y.toFixed(1)];
      }) : null;
      out.nanCells = (function () {
        var n = 0;
        for (var i = -2; i <= 8; i++) for (var j = -2; j <= 8; j++) {
          var cc = api.weaveCellContent(a, i, j);
          (cc.paths || []).forEach(function (p) { p.pts.forEach(function (q) { if (!isFinite(q.x) || !isFinite(q.y)) n++; }); });
        }
        return n;
      })();
      document.body.setAttribute('data-qa', JSON.stringify(out));
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
    dst.write_text(src[:idx] + INJECT + src[idx:], encoding="utf-8")
    print(dst)


if __name__ == "__main__":
    main()
