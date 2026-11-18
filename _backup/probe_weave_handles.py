# -*- coding: utf-8 -*-
"""手柄拖拽冒烟：拖圆孔中心 / 顶点，校验 custom.shapes 与 custom.walls 是否按预期变化。

用法：python _backup\probe_weave_handles.py docs\index.html C:\Temp\qa-handles-drag.html
"""

import sys
from pathlib import Path

INJECT = r"""
<script>
(function () {
  var log = [], errors = [];
  window.addEventListener('error', function (e) { errors.push(String(e.message)); });
  function ev(type, x, y) {
    var c = document.getElementById('habWorld');
    var r = c.getBoundingClientRect();
    var cx = r.left + (x / c.width) * r.width;
    var cy = r.top + (y / c.height) * r.height;
    ['pointerdown', 'pointermove', 'pointerup'].indexOf(type) < 0 && 0;
    var e = new PointerEvent(type, { clientX: cx, clientY: cy, bubbles: true, button: 0, buttons: type === 'pointerup' ? 0 : 1 });
    c.dispatchEvent(e);
  }
  function go() {
    try {
      document.getElementById('habAddWeave').click();
      document.getElementById('habWeaveEdit').click();
      var api = window.__studioHabitat;
      var a = api.agents().filter(function (x) { return x.kind === 'weave'; })[0];
      a.u = 1;
      var v = api.view();
      var cell = api.weaveCellContent(a, 0, 0).cell;
      var isl = cell.islands[0];
      var ixw = a.x + isl.cx, iyw = a.y + isl.cy;
      var sx = v.px(ixw), sy = v.py(iyw);
      log.push('island before=' + JSON.stringify(isl));
      ev('pointerdown', sx, sy);
      ev('pointermove', sx + 40, sy + 30);
      ev('pointerup', sx + 40, sy + 30);
      var sh = a.custom.shapes && a.custom.shapes['0,0'];
      log.push('override=' + JSON.stringify(sh));
      // 画一条壁：三个顶点 + 双击结束
      var bx = v.px(a.x - 60), by = v.py(a.y + 80);
      ev('pointerdown', bx, by); ev('pointerup', bx, by);
      ev('pointerdown', bx + 30, by - 20); ev('pointerup', bx + 30, by - 20);
      ev('pointerdown', bx + 60, by + 10); ev('pointerup', bx + 60, by + 10);
      var c = document.getElementById('habWorld');
      c.dispatchEvent(new MouseEvent('dblclick', { bubbles: true }));
      log.push('walls=' + JSON.stringify(a.custom.walls));
      var handlesCount = (function () { return Object.keys(a.custom.walls || {}).length + Object.keys(a.custom.shapes || {}).length; })();
      log.push('customKeys=' + handlesCount + ' sample=' + JSON.stringify(a.sample));
    } catch (e) { errors.push(String(e && e.message)); log.push('EX ' + e); }
    var pre = document.createElement('pre');
    pre.setAttribute('style', 'position:fixed;left:0;top:0;z-index:99999;margin:0;padding:12px;background:#fff;color:#000;font:12px/1.4 monospace;white-space:pre-wrap;width:100vw;height:100vh');
    pre.textContent = JSON.stringify({ log: log, errors: errors }, null, 1);
    var st = document.createElement('style');
    st.textContent = 'body > *:not(pre):not(script):not(style){display:none!important}';
    document.head.appendChild(st);
    document.body.appendChild(pre);
  }
  window.addEventListener('load', function () { setTimeout(go, 1600); });
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
