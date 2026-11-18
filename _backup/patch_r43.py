# -*- coding: utf-8 -*-
import io, re, base64, os

ROOT = r"H:\tool\silkworm-trajectory"
mod = io.open(ROOT + r"\_backup\r43_module.js", encoding="utf-8").read()

# 1) 接入 index.html：作为 r37 之后的新 script（保留 r37 原始逻辑作"固定网格"回退）
P = ROOT + r"\docs\index.html"
h = io.open(P, encoding="utf-8").read()
if "r43 识别升级" not in h:
    anchor = "window.__imgRec = { analyse, apply, state, readImage };"
    i = h.index(anchor)
    j = h.index("</script>", i) + len("</script>")
    h = h[:j] + "\n<script>\n" + mod.rstrip() + "\n</script>" + h[j:]
    io.open(P, "w", encoding="utf-8").write(h)
    print("index.html patched")
else:
    print("index.html already has r43")

# 2) QA harness：只跑识别算法 + 覆盖层，不加载主程序
TPL = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
body{background:#0b0f11;color:#dfe8e4;font:13px/1.6 system-ui;margin:0}
#habWorldWrap{position:relative;width:1100px;height:820px;margin:0 auto;background:#07090a}
#habWorld{position:absolute;inset:0}
#out{white-space:pre-wrap;padding:10px;font:13px ui-monospace,monospace}
</style></head><body>
<div id="out">pending</div>
<div id="habWorldWrap"><div id="habWorld"></div><canvas id="habRecOverlay"></canvas></div>
<div style="display:none">
<input id="habRecCols" value="0"><input id="habRecRows" value="0"><input id="habRecCell" value="320">
<input type="checkbox" id="habRecHoles" checked><input type="checkbox" id="habRecNotches" checked>
<div class="hab-rec-cols"></div><p id="habRecNote"></p><p id="habRecImageNote"></p>
</div>
<script>
window.__imgRec = { state:{}, analyse:function(){}, apply:function(){}, readImage:function(){} };
window.__studioHabitat = {
  view: function(){ return { w:1100, h:820, s:0.8, cx:550, cy:410, px:function(x){return 550+x*0.8;}, py:function(y){return 410+y*0.8;} }; },
  agents: function(){ return []; }, addWeave: function(){}, buildWeave: function(){}
};
</script>
<script>
__MODULE__
</script>
<script>
var IMG = "__IMG__";
window.__imgRec.readDataURL(IMG, function(){
  var t0 = performance.now();
  window.__imgRec.analyse();
  var dt = Math.round(performance.now() - t0);
  var st = window.__imgRec.state;
  var boxes = st.boxes || [];
  var present = boxes.filter(function(b){return b.present;});
  var weak = present.filter(function(b){return b.conf < 0.55;}).length;
  var polys = present.reduce(function(n,b){return n + (b.polys ? b.polys.length : 0);},0);
  var sizes = present.map(function(b){return Math.round(b.w) + "x" + Math.round(b.h);});
  document.getElementById('out').textContent =
    "ms=" + dt + " boxes=" + boxes.length + " present=" + present.length +
    " holes=" + (st.holes||[]).length + " polys=" + polys + " weak=" + weak +
    "\\nnote=" + document.getElementById('habRecNote').textContent +
    "\\nsizes=" + sizes.slice(0, 24).join(", ");
});
</script>
</body></html>"""

os.makedirs(ROOT + r"\_backup\rec43", exist_ok=True)
for tag, path in [("v", ROOT + r"\data\projects\参考图.png"),
                  ("h", r"C:\Users\54364\AppData\Local\Doubao\User Data\ClipboardTemp\e1affb7a-0807-4cee-8cef-1117c789be72.png")]:
    b64 = "data:image/png;base64," + base64.b64encode(io.open(path, "rb").read()).decode("ascii")
    html = TPL.replace("__MODULE__", mod).replace("__IMG__", b64)
    io.open(ROOT + rf"\_backup\rec43\t_{tag}.html", "w", encoding="utf-8").write(html)
    print("harness", tag, len(html))
