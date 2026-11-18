# -*- coding: utf-8 -*-
"""调试探针：单格 buildWeave 统计 + 全量绘制，用于排查路径为空/运行时异常。

用法：python _backup\probe_route_debug.py docs\index.html C:\Temp\qa-dbg.html
"""
import sys
from pathlib import Path

TMPL = r"""
<style>
  body > *:not(#habitat):not(script):not(style) { display: none !important; }
  #qaOut { position: fixed; left: 12px; top: 12px; z-index: 99999; background: #0d120f;
    color: #d9efe6; font: 12px/1.5 Consolas, monospace; padding: 10px 13px; white-space: pre-wrap; max-width: 96vw; }
</style>
<script>
(function () {
  function run() {
    const H = window.__studioHabitat;
    const out = [];
    try {
      const unit = {
        id: 'dbg', kind: 'weave', mode: 'idle', bodyVisible: true,
        x: 0, y: 0, w: 200, h: 200, coverage: 0.55, shape: 'island', worms: 6,
        wallAff: 0.6, seed: 4242, tone: 0.9, gap: 8, strata: 2, outline: null,
        u: 1, duration: 30, speedScale: 1, tileField: false, silk: [], heading: 0,
        walls: [], paths: [], custom: { walls: {}, paths: {}, shapes: {} }, cache: null, sample: null
      };
      H.buildWeave(unit);
      out.push('threads=' + (unit.sample ? unit.sample.threads : -1) +
        ' points=' + (unit.sample ? unit.sample.points : -1));
      const c = H.weaveCellContent(unit, 0, 0);
      out.push('paths=' + c.paths.length);
      c.paths.slice(0, 6).forEach((p, i) => {
        const b = { x0: 1e9, y0: 1e9, x1: -1e9, y1: -1e9 };
        p.pts.forEach(q => {
          b.x0 = Math.min(b.x0, q.x); b.x1 = Math.max(b.x1, q.x);
          b.y0 = Math.min(b.y0, q.y); b.y1 = Math.max(b.y1, q.y);
        });
        out.push('  p' + i + ' n=' + p.pts.length + ' bbox=' +
          (b.x1 - b.x0).toFixed(1) + 'x' + (b.y1 - b.y0).toFixed(1) +
          ' a=' + (p.a != null ? p.a.toFixed(3) : '-') + ' b=' + p.b);
      });
      // 画一遍，确认能出丝
      const cv = document.createElement('canvas');
      cv.width = 600; cv.height = 600;
      cv.style.cssText = 'position:fixed;right:20px;top:20px;background:#000;border:1px solid #333';
      document.getElementById('habitat').appendChild(cv);
      const g = cv.getContext('2d');
      g.fillStyle = '#000'; g.fillRect(0, 0, 600, 600);
      const v = { w: 600, h: 600, s: 1.6, cx: 300, cy: 300, px: x => 300 + x * 1.6, py: y => 300 + y * 1.6 };
      H.drawWeave(g, v, unit);
      out.push('drawWeave ok');
    } catch (e) {
      out.push('ERROR ' + (e && e.stack ? e.stack : e));
    }
    const pre = document.createElement('pre');
    pre.id = 'qaOut';
    pre.textContent = out.join('\n');
    document.getElementById('habitat').appendChild(pre);
  }
  if (document.readyState === 'complete') run();
  else window.addEventListener('load', run);
})();
</script>
"""


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    html = src.read_text(encoding="utf-8")
    html = html.replace("</head>", TMPL + "</head>", 1)
    dst.write_text(html, encoding="utf-8")
    print(dst, dst.stat().st_size)


main()
