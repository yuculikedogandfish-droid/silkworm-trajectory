# -*- coding: utf-8 -*-
"""巡游探针：注入一条实测样式 route 蚕，跑 60 秒模拟，检查丝迹是否铺开整个场地（而不是原地打转）。

用法：python _backup\probe_roam.py docs\index.html C:\Temp\qa-roam.html
"""

import sys
from pathlib import Path

INJECT = r"""
<script>
(function () {
  var out = { log: [], errors: [] };
  window.addEventListener('error', function (e) { out.errors.push(String(e.message)); });
  function run() {
    var H = window.__studioHabitat;
    var route = [];
    for (var i = 0; i < 60; i++) {
      var t = i / 59 * Math.PI * 2 * 2;
      route.push({ x: Math.cos(t) * 40, y: Math.sin(t * 1.6) * 70 });
    }
    var a = {
      id: 'rt-qa', kind: 'route', wormId: 1, color: '#fff', mode: 'run', bodyVisible: true,
      x: 0, y: 0, heading: 0, phase: 0, turnSign: 1, pauseUntil: 0,
      route: route, silk: [{ x: 0, y: 0, t: 0 }], offX: 0, offY: 0, rot: 0, scale: 1,
      follow: true, u: 0, travel: 0, speedScale: 1,
    };
    H.agents().push(a);
    for (var k = 0; k < 600; k++) H.step(0.1);
    var minX = 1e9, maxX = -1e9, minY = 1e9, maxY = -1e9;
    a.silk.forEach(function (p) {
      minX = Math.min(minX, p.x); maxX = Math.max(maxX, p.x);
      minY = Math.min(minY, p.y); maxY = Math.max(maxY, p.y);
    });
    out.log.push('travel=' + a.travel.toFixed(2) + ' silkPts=' + a.silk.length);
    out.log.push('smoke bbox x[' + minX.toFixed(1) + ',' + maxX.toFixed(1) + '] y[' + minY.toFixed(1) + ',' + maxY.toFixed(1) + ']');
    out.log.push('span=' + (maxX - minX).toFixed(0) + 'x' + (maxY - minY).toFixed(0));
    // 采样巡游点 5 个时刻
    var pts = [];
    [0, 10, 20, 30, 40].forEach(function (tt) {
      var g = H.roamPoint(a, tt);
      pts.push('t' + tt + '(' + g.x.toFixed(0) + ',' + g.y.toFixed(0) + ')');
    });
    out.log.push('roam ' + pts.join(' '));
  }
  window.addEventListener('load', function () {
    setTimeout(function () {
      try { run(); } catch (e) { out.errors.push(String(e)); }
      var pre = document.createElement('pre');
      pre.setAttribute('style', 'position:fixed;left:0;top:0;z-index:99999;margin:0;padding:14px;background:#fff;color:#000;font:13px/1.5 monospace;white-space:pre-wrap;width:100vw;height:100vh');
      pre.textContent = JSON.stringify(out, null, 1);
      var st = document.createElement('style');
      st.textContent = 'body > *:not(pre):not(script):not(style){display:none!important}';
      document.head.appendChild(st);
      document.body.appendChild(pre);
    }, 1800);
  });
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
