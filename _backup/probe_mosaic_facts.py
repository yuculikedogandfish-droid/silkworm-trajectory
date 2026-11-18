# -*- coding: utf-8 -*-
"""块群数值探针：打印 arenaSpec 与每个织网单元的位置/尺寸，排查块群为什么偏小偏挤。"""

import sys
from pathlib import Path

TMPL = r"""
<style id="qa-only-habitat">
  body > *:not(#habitat):not(script):not(style) { display: none !important; }
</style>
<style>
  #qaOut { position: fixed; inset: 0; z-index: 99999; background: #141a17; color: #d9efe6;
    font: 13px/1.65 Consolas, monospace; padding: 18px 22px; white-space: pre-wrap; overflow: auto; }
</style>
<script>
(function () {
  window.addEventListener('load', function () {
    setTimeout(function () {
      try {
        var H = window.__studioHabitat;
        var btn = document.getElementById('habAddMosaic');
        if (btn) btn.click();
        setTimeout(function () {
          var out = [];
          out.push('arena=' + JSON.stringify(H.arenaSpec ? H.arenaSpec() : 'n/a'));
          var list = H.agents().filter(function (a) { return a.kind === 'weave'; });
          out.push('weave count=' + list.length);
          list.forEach(function (a) {
            out.push(a.id + ' x=' + Math.round(a.x) + ' y=' + Math.round(a.y) +
              ' w=' + Math.round(a.w) + ' h=' + Math.round(a.h) + ' gap=' + a.gap +
              ' strata=' + a.strata + ' tone=' + a.tone.toFixed(2) + ' shape=' + a.shape);
          });
          var pre = document.createElement('pre');
          pre.id = 'qaOut';
          pre.textContent = out.join('\n');
          var host = document.getElementById('habitat') || document.body;
          host.appendChild(pre);
        }, 260);
      } catch (e) { console.log('probe error ' + e); }
    }, 1200);
  });
})();
</script>
"""


def main():
    src = Path(sys.argv[1]).read_text(encoding="utf-8")
    dst = Path(sys.argv[2])
    idx = src.rfind("</body>")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src[:idx] + TMPL + src[idx:], encoding="utf-8")
    print(f"{dst} {dst.stat().st_size} bytes")


if __name__ == "__main__":
    main()
