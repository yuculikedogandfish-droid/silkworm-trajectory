"""织网格网：导出→导入→重建 一致性验证，结果写 body[data-qa]。"""

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
      var before = { w: a.w, h: a.h, cov: a.coverage, shape: a.shape, worms: a.worms,
                     seed: a.seed, sample: a.sample, cells: a.cache ? a.cache.size : 0 };
      var ex = api.export();
      api.import(ex);
      var b = api.agents().filter(function (x) { return x.kind === 'weave'; })[0];
      var after = { w: b.w, h: b.h, cov: b.coverage, shape: b.shape, worms: b.worms,
                    seed: b.seed, sample: b.sample, cells: b.cache ? b.cache.size : 0 };
      document.body.setAttribute('data-qa', JSON.stringify({ before: before, after: after,
        saved: ex.agents.filter(function (x) { return x.kind === 'weave'; })[0].weave }));
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
    dst.write_text(src, encoding="utf-8")
    print(dst)


if __name__ == "__main__":
    main()
