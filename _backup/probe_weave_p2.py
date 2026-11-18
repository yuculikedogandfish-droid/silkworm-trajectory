# -*- coding: utf-8 -*-
"""织网 P2 探针：注入后在页面里统计每格丝迹 bbox / 点数 / 自定义，并捕获运行时错误。

用法：python _backup\\probe_weave_p2.py docs\\index.html C:\\Temp\\qa-probe-p2.html
随后 chrome --headless --dump-dom 该 html，再用 _backup\\extract_attr.py 解析 body[data-qa]。
"""

import sys
from pathlib import Path

INJECT = r"""
<script>
(function () {
  var errors = [];
  window.addEventListener('error', function (e) { errors.push(String(e.message)); });
  function bbox(pts) {
    var x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    pts.forEach(function (p) {
      if (!isFinite(p.x) || !isFinite(p.y)) return;
      x0 = Math.min(x0, p.x); y0 = Math.min(y0, p.y);
      x1 = Math.max(x1, p.x); y1 = Math.max(y1, p.y);
    });
    return [Math.round(x0), Math.round(y0), Math.round(x1), Math.round(y1)];
  }
  function go() {
    var out = { errors: errors };
    try {
      document.getElementById('habAddWeave').click();
      var api = window.__studioHabitat;
      var a = api.agents().filter(function (x) { return x.kind === 'weave'; })[0];
      if (!a) { out.fail = 'no weave agent'; }
      else {
        a.u = 1;
        out.agent = { id: a.id, w: a.w, h: a.h, worms: a.worms, shape: a.shape, sample: a.sample };
        out.cells = [];
        var cw = a.w, ch = a.h;
        for (var j = -1; j <= 1; j++) {
          for (var i = -1; i <= 1; i++) {
            var c = api.weaveCellContent(a, i, j);
            out.cells.push({
              key: i + ',' + j,
              blank: !!c.blank,
              paths: c.paths.length,
              pts: c.paths.reduce(function (s, p) { return s + p.pts.length; }, 0),
              walls: c.walls.length,
              islands: (c.cell.islands || []).length,
              notch: c.cell.notch ? (c.cell.notch.corner === -1 ? 'edge' : 'corner') : 'none',
              bbox: c.paths.length ? bbox(c.paths[0].pts) : null,
              cellW: cw, cellH: ch,
            });
          }
        }
      }
    } catch (err) {
      out.fail = String(err && err.message || err);
      out.stack = String(err && err.stack || '');
    }
    out.errors = errors;
    document.body.setAttribute('data-qa', JSON.stringify(out));
    document.body.setAttribute('data-qa-done', '1');
    var pre = document.createElement('pre');
    pre.id = 'qaOut';
    pre.setAttribute('style', 'position:fixed;left:0;top:0;z-index:99999;margin:0;padding:12px;background:#fff;color:#000;font:12px/1.35 monospace;white-space:pre-wrap;width:100vw;height:100vh;overflow:auto');
    pre.textContent = JSON.stringify(out, null, 1);
    var st = document.createElement('style');
    st.textContent = 'body > *:not(#qaOut):not(script):not(style){display:none!important}';
    document.head.appendChild(st);
    document.body.appendChild(pre);
  }
  window.addEventListener('load', function () { setTimeout(go, 2200); });
})();
</script>
"""


def main():
    src = Path(sys.argv[1]).read_text(encoding="utf-8")
    dst = Path(sys.argv[2])
    idx = src.rfind("</body>")
    if idx < 0:
        raise SystemExit("no </body>")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src[:idx] + INJECT + src[idx:], encoding="utf-8")
    print(f"{dst} {dst.stat().st_size} bytes")


if __name__ == "__main__":
    main()

