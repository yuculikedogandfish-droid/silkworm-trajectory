"""覆盖率滑杆效果验证：0.30 / 0.55 / 0.80 三档重建，统计点数写进 body[data-qa]。

用法：python _backup\\probe_weave_cov.py docs\\index.html C:\\Temp\\qa-weave-cov.html
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
    var slider = document.getElementById('habWeaveCov');
    var out = [];
    var covs = [0.30, 0.55, 0.80];
    var i = 0;
    function next() {
      if (i >= covs.length) { document.body.setAttribute('data-qa', JSON.stringify(out)); return; }
      var cov = covs[i++];
      slider.value = String(cov);
      slider.dispatchEvent(new Event('input'));
      var a = api.agents().filter(function (x) { return x.kind === 'weave'; })[0];
      if (a) {
        out.push({
          cov: cov, applied: a.coverage,
          paths: a.paths.length,
          points: a.paths.reduce(function (s, p) { return s + p.pts.length; }, 0),
          avg: Math.round(a.paths.reduce(function (s, p) { return s + p.pts.length; }, 0) / Math.max(1, a.paths.length))
        });
      }
      setTimeout(next, 400);
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
