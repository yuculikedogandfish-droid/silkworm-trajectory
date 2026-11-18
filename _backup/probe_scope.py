# -*- coding: utf-8 -*-
"""活动范围探针：cell 模式下蚕是否只在单格内活动，field 模式是否跨格。

用法：python _backup\probe_scope.py docs\index.html C:\Temp\qa-scope.html
"""

import sys
from pathlib import Path

TMPL = r"""
<style id="qa-only-habitat">
  body > *:not(#habitat):not(script):not(style) { display: none !important; }
</style>
<style>
  #qaOut { position: fixed; left: 24px; top: 24px; z-index: 99999; background: #141a17;
    color: #d9efe6; font: 13px/1.6 Consolas, monospace; padding: 10px 14px; white-space: pre-wrap; }
</style>
<script>
(function () {
  window.addEventListener('load', function () {
    setTimeout(function () {
      try {
        var H = window.__studioHabitat;
        var out = [];
        out.push('scope select=' + (document.getElementById('habAdjScope') ? 'yes' : 'missing'));
        document.getElementById('habAddMosaic').click();
        document.getElementById('habAddRandom').click();
        setTimeout(function () {
          var unit = H.agents().filter(function (a) { return a.kind === 'weave'; })[0];
          out.push('weave units=' + H.agents().filter(function (a) { return a.kind === 'weave'; }).length);
          if (!unit) { finish(); return; }
          var fake = { wormId: 1, x: unit.x, y: unit.y, scope: 'cell', homeUnitId: unit.id };
          var maxCell = 0;
          for (var i = 0; i < 240; i++) {
            var p = H.roamPoint(fake, i * 0.05);
            var d = Math.max(Math.abs(p.x - unit.x) / (unit.w / 2), Math.abs(p.y - unit.y) / (unit.h / 2));
            if (d > maxCell) maxCell = d;
          }
          out.push('cell mode: max |dx|/halfW = ' + maxCell.toFixed(2) + ' (<=1 表示在格内)');
          fake.scope = 'field'; fake.homeUnitId = null;
          var maxDX = 0, maxDY = 0;
          for (var j = 0; j < 240; j++) {
            var q = H.roamPoint(fake, j * 0.05);
            maxDX = Math.max(maxDX, Math.abs(q.x));
            maxDY = Math.max(maxDY, Math.abs(q.y));
          }
          out.push('field mode: max |x| = ' + Math.round(maxDX) + ', max |y| = ' + Math.round(maxDY));
          finish();
          function finish() {
            var pre = document.createElement('pre');
            pre.id = 'qaOut';
            pre.textContent = out.join('\n');
            document.getElementById('habitat').appendChild(pre);
          }
        }, 300);
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
