# -*- coding: utf-8 -*-
import io

P = r"H:\tool\silkworm-trajectory\docs\index.html"
s = io.open(P, encoding="utf-8").read()

# 1) 合并面板：个体 + 图层 合成一节
old = """      <h3>个体</h3>
      <p class="hab-note">实测蚕随描图数据自动进入；演示蚕从这里拖到场地。状态是放置、拖动、爬行、暂停。</p>
      <div id="habAgents"></div>
      <h3>图层</h3>
      <p class="hab-note">像 PS 的图层：每块织网单元、每只蚕各是一层。勾两层以上就能编组；「开 / 关」控制这一层显示。</p>
      <div class="row"><button type="button" id="habLayerGroup">编组所选</button><button type="button" id="habLayerUngroup">解散组</button><button type="button" id="habLayerClear">全部展开</button></div>
      <div id="habLayerTree"></div>"""
new = """      <h3>个体与图层</h3>
      <p class="hab-note">每块织网单元、每只蚕就是一层（像 PS）。点层名＝在场地里选中并画高亮框；勾多层可编组，组内拖动会一起走。</p>
      <div class="row"><button type="button" id="habLayerGroup">编组所选</button><button type="button" id="habLayerUngroup">解散组</button><button type="button" id="habLayerMerge">并入同组</button><button type="button" id="habLayerClear">全展开</button></div>
      <div id="habLayerTree"></div>
      <div class="lay-align">
        <span class="hab-note" style="margin:0 0 2px">对齐所选</span>
        <div class="row"><button type="button" data-align="l">左</button><button type="button" data-align="cx">横中</button><button type="button" data-align="r">右</button><button type="button" data-align="t">上</button><button type="button" data-align="cy">竖中</button><button type="button" data-align="b">下</button></div>
        <div class="row"><button type="button" data-align="dx">水平等距</button><button type="button" data-align="dy">垂直等距</button></div>
      </div>
      <div class="lay-array">
        <span class="hab-note" style="margin:0 0 2px">阵列复制（先只选一块）</span>
        <div class="row"><label>列</label><input type="number" id="habArrayN" min="1" max="20" value="3" style="width:52px"><label>排</label><input type="number" id="habArrayM" min="1" max="20" value="1" style="width:52px"><label>缝</label><input type="number" id="habArrayGap" min="0" max="200" value="12" style="width:52px"><button type="button" id="habArrayGo">复制</button></div>
      </div>
      <div id="habAgents" style="display:none"></div>"""
assert s.count(old) == 1
s = s.replace(old, new)

# 2) 覆盖层画布
a2 = """      <canvas id="habRecOverlay" aria-hidden="true"></canvas>"""
b2 = a2 + """
      <canvas id="habSnapOverlay" aria-hidden="true"></canvas>"""
assert s.count(a2) == 1
s = s.replace(a2, b2)

# 3) CSS
css = """#habRecOverlay{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:7}"""
add = css + """
#habSnapOverlay{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:8}
.lay-align,.lay-array{margin-top:8px;padding-top:6px;border-top:1px solid rgba(255,255,255,0.07)}
.lay-row.on{background:rgba(121,203,182,0.12);box-shadow:inset 2px 0 0 rgba(121,203,182,0.9)}
.lay-group.on{background:rgba(121,203,182,0.16)}
.lay-mini{font-size:11px;background:rgba(255,255,255,0.08);border:0;color:inherit;border-radius:4px;padding:1px 5px;cursor:pointer;min-width:20px}
.lay-mini.on{background:rgba(232,201,138,0.25)}"""
assert s.count(css) == 1
s = s.replace(css, add)

# 4) 工程文件带组：导出 / 导入各一行钩子
e1 = """      selected: habitat.selected,
      selectedLeaf: habitat.selectedLeaf,"""
e2 = """      selected: habitat.selected,
      selectedLeaf: habitat.selectedLeaf,
      layerGroups: (window.__layerStore && window.__layerStore.dump) ? window.__layerStore.dump() : null,"""
assert s.count(e1) == 1
s = s.replace(e1, e2)

i1 = """  function importHabitat(data) {
    if (!data) return;"""
i2 = """  function importHabitat(data) {
    if (!data) return;
    if (data.layerGroups && window.__layerStore && window.__layerStore.load) {
      setTimeout(() => window.__layerStore.load(data.layerGroups), 0);
    }"""
assert s.count(i1) == 1
s = s.replace(i1, i2)

# 5) 锁定的层不许被拖
d1 = """  function applyWeaveHandleDrag(h, p) {
    const a = weaveEditAgent();
    const e = habitat.weaveEdit;
    if (!a || !e) return;"""
d2 = """  function applyWeaveHandleDrag(h, p) {
    const a = weaveEditAgent();
    const e = habitat.weaveEdit;
    if (!a || !e) return;
    if (a.locked) return;"""
assert s.count(d1) == 1
s = s.replace(d1, d2)

# 6) 模块
mod = io.open(r"H:\tool\silkworm-trajectory\_backup\r39_module.js", encoding="utf-8").read().rstrip()
i = s.rfind("</body>")
s = s[:i] + mod + "\n" + s[i:]

io.open(P, "w", encoding="utf-8").write(s)
print("r39 ok", len(s))
