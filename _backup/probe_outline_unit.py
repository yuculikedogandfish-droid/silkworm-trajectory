# -*- coding: utf-8 -*-
"""轮廓单元冒烟：点「按轮廓新建单元」→ 画 4 点 → 双击 → 检查 outline 是否写入并可见。

用法：python _backup\probe_outline_unit.py docs\index.html C:\Temp\qa-outline.html
"""

import sys
from pathlib import Path

TMPL = r"""
<style id="qa-only-habitat">
  body > *:not(#habitat):not(script):not(style) { display: none !important; }
</style>
<script>
(function () {
  window.addEventListener('load', function () {
    setTimeout(function () {
      try {
        var H = window.__studioHabitat;
        var btn = document.getElementById('habAddOutline');
        if (btn) btn.click();
        var cv = document.getElementById('habWorld');
        var v = H.view();
        var r = cv.getBoundingClientRect();
        function fire(type, wx, wy) {
          var ev = new PointerEvent(type, {
            bubbles: true, cancelable: true, clientX: r.left + v.px(wx), clientY: r.top + v.py(wx * 0 + wy), button: 0
          });
          cv.dispatchEvent(ev);
        }
        var pts = [[-90, -70], [90, -95], [115, 80], [-70, 95]];
        pts.forEach(function (p) { fire('pointerdown', p[0], p[1]); });
        cv.dispatchEvent(new MouseEvent('dblclick', { bubbles: true, clientX: r.left + v.px(0), clientY: r.top + v.py(0) }));
        setTimeout(function () {
          var list = H.agents().filter(function (a) { return a.kind === 'weave'; });
          var last = list[list.length - 1];
          var out = [];
          out.push('weave count=' + list.length);
          if (last) {
            out.push('last ' + last.id + ' outline=' + (last.outline ? last.outline.length : 0) +
              ' w=' + Math.round(last.w) + ' h=' + Math.round(last.h) + ' x=' + Math.round(last.x) + ' y=' + Math.round(last.y));
            last.u = 0.995;
            last.mode = 'idle';
          }
          var pre = document.createElement('pre');
          pre.id = 'qaOut';
          pre.textContent = out.join('\n');
          pre.style.cssText = 'position:fixed;left:260px;top:64px;z-index:99999;background:#141a17;color:#d9efe6;font:13px/1.6 Consolas,monospace;padding:8px 12px;white-space:pre-wrap';
          document.getElementById('habitat').appendChild(pre);
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
