# -*- coding: utf-8 -*-
import io
ROOT = r"H:\tool\silkworm-trajectory"
h = io.open(ROOT + r"\docs\index.html", encoding="utf-8").read()
h = h.replace("<body>", "<body>\n<script>window.__errs=[];window.addEventListener('error',function(e){window.__errs.push(e.message+' @'+e.lineno);});</script>", 1)
inject = r"""
<div id="qaout" style="position:fixed;left:8px;top:8px;z-index:99999;background:#000;color:#7CFFB2;font:12px monospace;padding:7px;max-width:1200px;white-space:pre-wrap">pending</div>
<script>
window.addEventListener('load', function () {
  var L = [];
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
    var world = document.getElementById('habWorld');
    var r = world.getBoundingClientRect(), v = H.view();
    function at(u) { return [r.left + v.px(u.x), r.top + v.py(u.y)]; }
    function dbl(u, shift) {
      var p = at(u);
      world.dispatchEvent(new MouseEvent('dblclick', { bubbles: true, cancelable: true, clientX: p[0], clientY: p[1], button: 0, shiftKey: !!shift }));
    }
    __layerSel.clear();
    dbl(units()[0]); L.push('dbl_select=' + (__layerSel.ids().join(',') === ids[0]));
    dbl(units()[0]); L.push('dbl_deselect=' + (__layerSel.size() === 0));
    dbl(units()[0]); dbl(units()[1], true); L.push('dbl_shift_add=' + (__layerSel.size() === 2));
    __weaveHooks.enter(ids[0]);
    dbl(units()[0]);
    L.push('dbl_multi_removes_hit=' + (__layerSel.ids().join(',') === ids[1]) + ' edit_exited=' + (!H.weaveEditState()));
    __layerSel.set([ids[0]]);
    dbl(units()[0]); L.push('dbl_sole_clears=' + (__layerSel.size() === 0));

    // 右键批量删除 + 一次撤销恢复整批
    __layerSel.set(ids.slice(0, 2));
    var b = __layerSel.bbox();
    var cx = r.left + v.px((b.l + b.r) / 2), cy = r.top + v.py((b.t + b.b) / 2);
    world.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: cx, clientY: cy, button: 2 }));
    var menu = document.querySelector('#habitat .lay-menu');
    var btn = menu && Array.prototype.find.call(menu.querySelectorAll('button'), function (x) { return x.textContent.indexOf('删除选中') === 0; });
    if (btn) btn.click();
    L.push('batch_delete=' + (units().length === 1) + ' sel=' + __layerSel.size());
    H.undoStep();
    L.push('one_undo_restores_all=' + (units().length === 3));

    // 空白单击取消选择
    __layerSel.set(units().map(function (u) { return u.id; }));
    var ex = r.left + v.px(-460), ey = r.top + v.py(-330);
    world.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, button: 0, clientX: ex, clientY: ey }));
    window.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, button: 0, clientX: ex, clientY: ey }));
    L.push('empty_clears=' + (__layerSel.size() === 0));

    // 结构 / 入口 / 布局
    var allIds = Array.prototype.map.call(document.querySelectorAll('[id]'), function (x) { return x.id; });
    var dup = allIds.filter(function (x, i) { return x && allIds.indexOf(x) !== i; });
    L.push('duplicate_ids=' + JSON.stringify(Array.from(new Set(dup))));
    L.push('guide_links=' + document.querySelectorAll('a[href="使用说明.html"]').length);
    var doc = H.export();
    L.push('project_export=' + (doc && doc.agents.filter(function (a) { return a.kind === 'weave'; }).length === 3));
    H.import(doc);
    L.push('project_import_roundtrip=' + (units().length === 3));
    L.push('feature_apis=' + ['analyse', 'apply'].every(function (k) { return window.__imgRec && typeof window.__imgRec[k] === 'function'; }) + ',' + (typeof H.ledExportImage === 'function') + ',' + (typeof H.ledRecordWebVideo === 'function'));
  } catch (e) { L.push('ERR ' + e.message + ' ' + e.stack); }
  setTimeout(function () {
    var bar = document.querySelector('.hab-rec-bar').getBoundingClientRect();
    var top = document.querySelector('.hab-top').getBoundingClientRect();
    L.push('recbar_clear=' + (bar.top >= top.bottom) + ' gap=' + Math.round(bar.top - top.bottom));
    L.push('jserrs=' + JSON.stringify(window.__errs || []));
    document.getElementById('qaout').textContent = L.join('\n');
  }, 1000);
});
</script>
"""
j = h.rfind("</body>")
h = h[:j] + inject + "\n" + h[j:]
io.open(ROOT + r"\_backup\rec43\qa_r46.html", "w", encoding="utf-8").write(h)
print("qa r46 page")
