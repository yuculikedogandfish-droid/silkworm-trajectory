# -*- coding: utf-8 -*-
import io, base64
ROOT = r"H:\tool\silkworm-trajectory"
h = io.open(ROOT + r"\docs\index.html", encoding="utf-8").read()
img = "data:image/png;base64," + base64.b64encode(io.open(ROOT + r"\data\projects\参考图.png", "rb").read()).decode("ascii")
inject = """
<div id="qaout" style="position:fixed;left:8px;top:8px;z-index:99999;background:#000;color:#7CFFB2;font:12px monospace;padding:6px;max-width:96vw">pending</div>
<script>
window.addEventListener('load', function () {
  var out = document.getElementById('qaout');
  try {
    __imgRec.readDataURL("__IMG__", function () {
      try {
        __imgRec.analyse();
        var st = __imgRec.state;
        var found = st.boxes.filter(function(b){return b.present;}).length;
        st.boxes = st.boxes.filter(function(b){return b.present;}).slice(0, 4);
        __imgRec.apply(true);
        var us = __studioHabitat.agents().filter(function(a){return a.kind === 'weave';});
        out.textContent = 'found=' + found + ' units=' + us.length + ' ' + JSON.stringify(us.map(function(u){
          var sh = (u.custom && u.custom.shapes && u.custom.shapes['0,0']) || {};
          return { w: u.w, h: u.h, x: u.x, y: u.y, holes: (sh.islands || []).length, notch: (sh.notchPts || []).length };
        }));
      } catch (e) { out.textContent = 'ERR apply ' + e.message; }
    });
  } catch (e) { out.textContent = 'ERR ' + e.message; }
});
</script>
"""
h = h.replace("</body>", inject.replace("__IMG__", img) + "\n</body>")
io.open(ROOT + r"\_backup\rec43\qa_apply.html", "w", encoding="utf-8").write(h)
print("qa apply page", len(h))
