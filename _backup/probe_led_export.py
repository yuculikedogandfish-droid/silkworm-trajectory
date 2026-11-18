# -*- coding: utf-8 -*-
"""母版导出探针：检查面板按钮 + ledScene / ledCurves / ledSvg / ledDxf 结构。

用法：python _backup\probe_led_export.py docs\index.html C:\Temp\qa-led-export.html
"""

import sys
from pathlib import Path

TMPL = r"""
<style>
  body > *:not(#habitat):not(script):not(style) { display: none !important; }
  #qaOut { position: fixed; left: 14px; top: 14px; z-index: 99999; background: #0d120f;
    color: #d9efe6; font: 12px/1.55 Consolas, monospace; padding: 12px; white-space: pre-wrap;
    max-width: 96vw; max-height: 96vh; overflow: auto; }
</style>
<script>
(function () {
  window.addEventListener('load', function () {
    const out = [];
    try { main(); } catch (e) { out.push('probe error: ' + (e && e.message ? e.message : e)); }
    const pre = document.createElement('pre');
    pre.id = 'qaOut'; pre.textContent = out.join('\n');
    document.getElementById('habitat').appendChild(pre);
    function main() {
      const H = window.__studioHabitat;
      ['habLedRes', 'habLedFrames', 'habLedFps', 'habLedScene', 'habLedCurves', 'habLedGeom', 'habLedDxf', 'habLedCmd']
        .forEach(id => out.push('#' + id + ' = ' + (document.getElementById(id) ? 'ok' : 'MISSING')));
      document.getElementById('habAddMosaic').click();
      setTimeout(function () {
        try { dump(); } catch (e) { out.push('dump error: ' + (e && e.message ? e.message : e)); }
        document.getElementById('qaOut').textContent = out.join('\n');
      }, 120);
    }
    function dump() {
      const H = window.__studioHabitat;
      const sc = H.ledScene();
      const b = sc.units.length ? 'units=' + sc.units.length : 'units=0';
      out.push('scene schema=' + sc.schema + ' px=' + sc.px.w + 'x' + sc.px.h + ' frames=' + sc.frames +
        ' fps=' + sc.fps + ' ' + b + ' scale=' + sc.scale + ' center=' + JSON.stringify(sc.center));
      const u0 = sc.units[0];
      out.push('unit0 keys=' + Object.keys(u0).join(','));
      out.push('unit0 x=' + u0.x + ' y=' + u0.y + ' w=' + u0.w + ' h=' + u0.h + ' seed=' + u0.seed +
        ' cov=' + u0.coverage + ' strata=' + u0.strata + ' tone=' + u0.tone + ' shape=' + u0.shape);
      const cur = H.ledCurves();
      const c0 = cur.units[0];
      out.push('curves schema=' + cur.schema + ' units=' + cur.units.length +
        ' unit0 curves=' + c0.curves.length + ' pts=' + c0.curves.reduce((s, c) => s + c.pts.length, 0) +
        ' totalLength=' + c0.totalLength);
      const svg = H.ledSvg();
      const dxf = H.ledDxf();
      out.push('svg ' + svg.length + ' B, paths=' + (svg.match(/<path/g) || []).length);
      out.push('dxf ' + dxf.length + ' B, polylines=' + (dxf.match(/LWPOLYLINE/g) || []).length);
      out.push('cmd ' + H.ledRenderCommand());
    }
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
    print(f"{dst} {dst.stat().st_size}")


if __name__ == "__main__":
    main()
