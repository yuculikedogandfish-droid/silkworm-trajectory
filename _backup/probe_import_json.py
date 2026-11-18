# -*- coding: utf-8 -*-
"""导入回归：把「JSON 导出」结构（curves3d / silkworms，mm 为 null 时退化到 px）灌进描图器，校验不再报缺列。

用法：python _backup\probe_import_json.py docs\index.html C:\Temp\qa-import.html
"""

import sys
from pathlib import Path

INJECT = r"""
<script>
(function () {
  var log = [], alerts = [], errors = [];
  var realAlert = window.alert;
  window.alert = function (m) { alerts.push(String(m)); banner('ALERT: ' + m); };
  function banner(text) {
    var b = document.createElement('div');
    b.style.cssText = 'position:fixed;left:0;top:0;z-index:99999;background:#c00;color:#fff;font:16px/1.5 monospace;padding:8px 12px;width:100vw';
    b.textContent = text;
    (document.body || document.documentElement).appendChild(b);
  }
  window.addEventListener('error', function (e) { errors.push(String(e.message)); });
  function payloadCurves() {
    return {
      fps: 30,
      curves3d: [{
        id: '1_0', wormId: 1, strokeIndex: 0, name: 'worm_1_stroke_0', color: '#f7f5f2',
        style: { headWidth_mm: 0.2, midWidth_mm: 0.3, tailWidth_mm: 0.1, opacity: 1, material: 'silk' },
        points: [
          { index: 0, x_mm: null, y_mm: null, z_mm: 0, x_px: 100, y_px: 80, width_mm: 0.2 },
          { index: 1, x_mm: null, y_mm: null, z_mm: 0, x_px: 160, y_px: 40, width_mm: 0.3 },
          { index: 2, x_mm: null, y_mm: null, z_mm: 0, x_px: 220, y_px: 90, width_mm: 0.2 },
        ],
      }],
      silkworms: [{ id: 1, color: '#f7f5f2', style: {}, points: [
        { index: 0, x_mm: null, y_mm: null, x_px: 100, y_px: 80 },
        { index: 1, x_mm: null, y_mm: null, x_px: 160, y_px: 40 },
      ] }],
    };
  }
  function feed(obj) {
    var input = document.getElementById('fileJson');
    var dt = new DataTransfer();
    dt.items.add(new File([JSON.stringify(obj)], 'trajectories.json', { type: 'application/json' }));
    input.files = dt.files;
    input.dispatchEvent(new Event('change', { bubbles: true }));
  }
  function stat() {
    var el = document.getElementById('trajStat');
    return el ? el.textContent.replace(/\s+/g, ' ').trim() : '(no stat)';
  }
  function go() {
    try {
      feed(payloadCurves());
      setTimeout(function () {
        try {
          log.push('alerts=' + JSON.stringify(alerts));
          log.push('stat=' + stat());
          log.push('errors=' + JSON.stringify(errors));
        } catch (e2) { log.push('inner error ' + e2); }
        var pre = document.createElement('pre');
        pre.setAttribute('style', 'position:fixed;left:0;top:0;z-index:99999;margin:0;padding:12px;background:#fff;color:#000;font:12px/1.4 monospace;white-space:pre-wrap;width:100vw;height:100vh');
        pre.textContent = JSON.stringify({ log: log }, null, 1);
        var st = document.createElement('style');
        st.textContent = 'body > *:not(pre):not(script):not(style){display:none!important}';
        document.head.appendChild(st);
        document.body.appendChild(pre);
      }, 600);
    } catch (e) { errors.push(String(e)); }
  }
  window.addEventListener('load', function () { setTimeout(go, 1200); });
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
