# -*- coding: utf-8 -*-
"""形状编辑交互烟测：点「开始编辑形状」→ 画布点 3 个顶点 → 双击结束 → 清空本格，检查无异常。

用法：python _backup/probe_weave_edit.py docs\\index.html C:\\Temp\\qa-edit.html
"""

import sys
from pathlib import Path

INJECT = r"""
<script>
(function () {
  var log = [];
  var errors = [];
  window.addEventListener('error', function (e) { errors.push(String(e.message)); });
  function note() {
    var el = document.getElementById('habWeaveEditNote');
    return el ? el.textContent : '(no note)';
  }
  function click(id) {
    var el = document.getElementById(id);
    if (!el) { log.push('missing ' + id); return; }
    el.click();
  }
  function tap(x, y, dbl) {
    var c = document.getElementById('habWorld');
    ['pointerdown', 'pointerup'].forEach(function (t) {
      c.dispatchEvent(new PointerEvent(t, { clientX: x, clientY: y, bubbles: true, button: 0 }));
    });
    if (dbl) c.dispatchEvent(new MouseEvent('dblclick', { clientX: x, clientY: y, bubbles: true }));
  }
  function go() {
    try {
      document.getElementById('habAddWeave').click();
      click('habWeaveEdit');
      log.push('after edit on: ' + note());
      tap(700, 420);
      tap(760, 470);
      tap(820, 430);
      log.push('after 3 taps: ' + note());
      click('habWeaveEditEnd');
      log.push('after end: ' + note());
      click('habWeaveEditClear');
      log.push('after clear: ' + note());
      click('habWeaveEdit');
      log.push('after exit: ' + note());
      var api = window.__studioHabitat;
      var a = api.agents().filter(function (x) { return x.kind === 'weave'; })[0];
      log.push('custom=' + JSON.stringify(a && a.custom) + ' sample=' + JSON.stringify(a && a.sample));
      click('habGridToggle');
      log.push('showGrid=' + (window.__studioHabitat ? 'clicked' : 'n/a'));
    } catch (e) { errors.push(String(e && e.message)); log.push('EX ' + e); }
    var out = { log: log, errors: errors };
    var pre = document.createElement('pre');
    pre.id = 'qaOut';
    pre.setAttribute('style', 'position:fixed;left:0;top:0;z-index:99999;margin:0;padding:12px;background:#fff;color:#000;font:12px/1.4 monospace;white-space:pre-wrap;width:100vw;height:100vh;overflow:auto');
    pre.textContent = JSON.stringify(out, null, 1);
    var st = document.createElement('style');
    st.textContent = 'body > *:not(#qaOut):not(script):not(style){display:none!important}';
    document.head.appendChild(st);
    document.body.appendChild(pre);
  }
  window.addEventListener('load', function () { setTimeout(go, 1800); });
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

