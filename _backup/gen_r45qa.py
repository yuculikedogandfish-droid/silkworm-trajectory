# -*- coding: utf-8 -*-
import io
ROOT = r"H:\tool\silkworm-trajectory"
h = io.open(ROOT + r"\docs\index.html", encoding="utf-8").read()
# 在模块之前挂错误监听
h = h.replace("<body>", "<body>\n<script>window.__errs=[];window.addEventListener('error',function(e){window.__errs.push(e.message+' @'+e.lineno);});</script>", 1)
inject = r"""
<div id="qaout" style="position:fixed;left:8px;top:8px;z-index:99999;background:#000;color:#7CFFB2;font:12px monospace;padding:6px;max-width:96vw;white-space:pre-wrap">pending</div>
<script>
window.addEventListener('load', function () {
  var out = document.getElementById('qaout');
  var log = [];
  try {
    window.confirm = function () { return true; };
    var H = window.__studioHabitat;
    [[-170, 0], [30, 10], [430, 320]].forEach(function (p, i) {
      H.addWeave({});
      var l = H.agents().filter(function (a) { return a.kind === 'weave'; });
      var u = l[l.length - 1];
      u.w = 240; u.h = 240; u.x = p[0]; u.y = p[1]; u.seed = 101 + i * 37;
    });
    var units = function () { return H.agents().filter(function (a) { return a.kind === 'weave'; }); };
    var ids = units().map(function (u) { return u.id; });
    __layerSel.set(ids.slice(0, 2));
    log.push('sel=' + __layerSel.size());
    var world = document.getElementById('habWorld');
    var r = world.getBoundingClientRect();
    var v = H.view();
    var b = __layerSel.bbox();
    var cx = r.left + v.px((b.l + b.r) / 2), cy = r.top + v.py((b.t + b.b) / 2);
    log.push('click at ' + Math.round(cx) + ',' + Math.round(cy) + ' bbox=' + JSON.stringify(b));
    world.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: cx, clientY: cy, button: 2 }));
    var menu = document.querySelector('#habitat .lay-menu');
    log.push('menu=' + (menu ? menu.textContent : 'NONE'));
    if (menu) {
      var btn = Array.prototype.find.call(menu.querySelectorAll('button'), function (x) { return x.textContent.indexOf('删除选中') === 0; });
      if (btn) btn.click();
    }
    log.push('afterDelete units=' + units().length + ' sel=' + __layerSel.size());

    __layerSel.set(units().map(function (u) { return u.id; }));
    var ex = r.left + v.px(-460), ey = r.top + v.py(-330);
    world.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, button: 0, clientX: ex, clientY: ey }));
    window.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, button: 0, clientX: ex, clientY: ey }));
    log.push('afterEmptyClick sel=' + __layerSel.size());
  } catch (e) { log.push('ERR ' + e.message); }
  setTimeout(function () {
    var bar = document.querySelector('.hab-rec-bar').getBoundingClientRect();
    var top = document.querySelector('.hab-top').getBoundingClientRect();
    log.push('recbar_clear=' + (bar.top >= top.bottom) + ' gap=' + Math.round(bar.top - top.bottom) + ' styleTop=' + document.querySelector('.hab-rec-bar').style.top);
    log.push('jserrs=' + JSON.stringify(window.__errs || []));
    out.textContent = log.join('\n');
  }, 2200);
});
</script>
"""
h = h.replace("</body>", inject + "\n</body>")
io.open(ROOT + r"\_backup\rec43\qa_r45.html", "w", encoding="utf-8").write(h)
print("qa r45 v2")
