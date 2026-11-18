import re
from pathlib import Path

src = Path(r"H:\tool\silkworm-trajectory\docs\index.html")
dst = Path(r"C:\Users\54364\AppData\Local\Temp\qa-hab.html")

text = src.read_text(encoding="utf-8")

# 把 srcdoc 属性整段抠出来，只在“外层文档”上做注入，避免误改预览内部页面
m = re.search(r'srcdoc="(.*?)"></iframe>', text, re.S)
outer = text[:m.start(1)] + 'about:blank' + text[m.end(1):] if m else text

qa_css = """<script>
(function () {
  var t = 0;
  window.requestAnimationFrame = function (cb) {
    return setTimeout(function () { t += 16; cb(t); }, 16);
  };
})();
</script><style>.screen1{display:none !important}</style></head>"""
outer = outer.replace("</head>", qa_css, 1)

probe = """
<script>
window.addEventListener('error', function (e) {
  document.title = 'ERR ' + e.message + ' @' + e.lineno;
});
window.addEventListener('load', function () {
  setTimeout(function () {
    try {
      var pts = [];
      for (var i = 0; i < 80; i++) {
        pts.push({ x: i * 8, y: Math.sin(i / 7) * 26 + Math.cos(i / 13) * 12 });
      }
      window.__previewTrajs = [
        { wormId: 1, points: pts },
        { wormId: 2, points: pts.map(function (p) { return { x: p.x, y: -p.y }; }) }
      ];
      var hab = window.__studioHabitat;
      var n = hab.syncMeasured();
      // 选中第 1 只，用滑杆把速度倍率调到 2.00×
      window.__qaHab.selected = 'rt-1';
      var sp = document.getElementById('habAdjSpeed');
      sp.value = '2';
      sp.dispatchEvent(new Event('input', { bubbles: true }));
      var spLabel = document.getElementById('habAdjSpeedVal');
      document.getElementById('habStart').click();
      // 用真实 step() 推进 3.2 秒模拟时间（不依赖 rAF 时间戳）
      for (var k = 0; k < 200; k++) window.__qaStep(0.016);
      setTimeout(function () {
        var d = hab.export();
        // 缩放 / 平移 / 分隔线联动检查
      var label0 = document.getElementById('habZoomLabel').textContent;
      var wEl = document.getElementById('habWorld');
      var r = wEl.getBoundingClientRect();
      wEl.dispatchEvent(new WheelEvent('wheel', {
        bubbles: true, cancelable: true, deltaY: -240,
        clientX: r.left + r.width * 0.7, clientY: r.top + r.height * 0.4
      }));
      var label1 = document.getElementById('habZoomLabel').textContent;
      document.getElementById('habFitView').click();
      var label2 = document.getElementById('habZoomLabel').textContent;
      document.getElementById('habPanToggle').click();
      var panOn = document.getElementById('habPanToggle').className + '/' + wEl.className;
      var varBefore = getComputedStyle(document.documentElement).getPropertyValue('--preview-width').trim();
      try {
        var sp2 = document.getElementById('previewSplitter');
        sp2.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: 900, pointerId: 1 }));
        sp2.dispatchEvent(new PointerEvent('pointermove', { bubbles: true, clientX: 640, pointerId: 1 }));
        sp2.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: 640, pointerId: 1 }));
      } catch (e) { varBefore += ' ERR:' + e.message; }
      var varAfter = getComputedStyle(document.documentElement).getPropertyValue('--preview-width').trim();
      // 像素级检查：蚕体是否真的画出来
      var ag = window.__qaHab.agents[0];
      window.__qaPaint();
      var vv = window.__qaView();
      var cv = document.getElementById('habWorld');
      var cx2 = vv.px(ag.x), cy2 = vv.py(ag.y);
      var img = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height).data;
      var bright = 0;
      for (var q = 0; q < img.length; q += 4) {
        if (img[q] > 200 && img[q + 1] > 200 && img[q + 2] > 200) bright++;
      }
      var pxInfo = 'px=' + cx2.toFixed(0) + ',' + cy2.toFixed(0) + ' bright=' + bright + ' cv=' + cv.width + 'x' + cv.height;
      var a = d.agents[0] || {};
        var b = d.agents[1] || {};
        var hEl = document.getElementById('habCanvasHeightVal');
        var r = 'QA sync=' + n + ' n=' + d.agents.length +
          ' | a.mode=' + a.mode + ' u=' + (a.u || 0).toFixed(3) +
          ' x=' + (a.x || 0).toFixed(2) + ' follow=' + a.follow +
          ' speed=' + a.speedScale + ' | b.u=' + (b.u || 0).toFixed(3) +
          ' b.speed=' + b.speedScale +
          ' | heightLabel=[' + (hEl ? hEl.textContent : 'na') + ']' +
          ' inputVal=' + document.getElementById('habCanvasHeight').value +
          ' | zoom ' + label0 + '->' + label1 + '->' + label2 +
          ' pan=' + panOn +
          ' | splitterVar ' + varBefore + ' -> ' + varAfter +
          ' spLabel=' + (spLabel ? spLabel.textContent : 'na') +
          ' silk=' + ((window.__qaHab.agents[0] || {}).silk || []).length +
          ' body=' + ((window.__qaHab.agents[0] || {}).bodyVisible) +
          ' | ' + pxInfo;
        document.title = r;
        var box = document.createElement('div');
        box.style.cssText = 'position:fixed;left:8px;bottom:8px;z-index:99999;background:#000;color:#7fffd4;font:12px monospace;padding:6px;white-space:pre';
        box.textContent = r;
        document.body.appendChild(box);
      }, 2600);
    } catch (err) {
      document.title = 'QA ERROR ' + err.message;
    }
  }, 600);
});
</script></body>"""

outer = outer.replace("</body>", probe, 1)
outer = outer.replace(
    "window.__studioHabitat = { export: exportHabitat",
    "window.__qaStep = step; window.__qaView = view; window.__qaPaint = paintWorld; window.__qaWorm = drawHabitatWorm; window.__qaHab = habitat; window.__studioHabitat = { export: exportHabitat",
    1,
)
dst.write_text(outer, encoding="utf-8")
print(dst, dst.stat().st_size)
