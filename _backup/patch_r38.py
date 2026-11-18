# -*- coding: utf-8 -*-
import io

P = r"H:\tool\silkworm-trajectory\docs\index.html"
s = io.open(P, encoding="utf-8").read()

# 1) 把左栏的识别面板整块摘掉
old_panel = """      <details id="habRecBox" class="hab-rec">
        <summary>从图片识别版式（上传一张图，自动铺块）</summary>
        <p class="hab-note">上传一张拼接好的丝片照片或设计稿：自动找出格子、几排几列、哪里缺块，以及格内的圆孔／缺口，先给你看预览，确认后再生成到场地。不影响场地里现有的东西。</p>
        <div class="row"><input type="file" id="habRecFile" accept="image/*"></div>
        <p class="hab-note" id="habRecImageNote">还没选图片。</p>
        <div class="row"><label>列数</label><input type="number" id="habRecCols" min="0" max="40" step="1" value="0" placeholder="自动" style="width:62px"><label>排数</label><input type="number" id="habRecRows" min="0" max="40" step="1" value="0" placeholder="自动" style="width:62px"><span class="hab-note" style="margin:0">0＝自动估</span></div>
        <div class="row"><label>目标格边长</label><input type="range" id="habRecCell" min="120" max="900" step="10" value="320"><span class="hab-adj-val" id="habRecCellVal">320px</span></div>
        <div class="row"><label><input type="checkbox" id="habRecHoles" checked> 识别孔洞</label><label><input type="checkbox" id="habRecNotches" checked> 识别缺口</label></div>
        <div class="row"><button type="button" id="habRecRun">识别并预览</button><button type="button" id="habRecClear">清掉预览</button></div>
        <div class="row"><button type="button" id="habRecApply">生成到场地（新增）</button><button type="button" id="habRecReplace">替换现有块群</button></div>
        <p class="hab-note" id="habRecNote">只在你点按钮时才会动场地；识别本身不改任何东西。</p>
      </details>
"""
assert s.count(old_panel) == 1
s = s.replace(old_panel, "")

# 2) 在中间画布上方插入一条可折叠的识别栏
anchor = """    <button type="button" id="habOpenRight" aria-pressed="false">收起个体</button>
  </div>
  <div class="hab-stage">"""
bar = """    <button type="button" id="habOpenRight" aria-pressed="false">收起个体</button>
  </div>
  <div class="hab-rec-bar">
    <details id="habRecBox" class="hab-rec">
      <summary><b>从图片识别版式</b><span class="hab-rec-sum">上传一张图，自动找出格子、排数、缺块与格内孔洞／缺口（先预览，再生成）</span></summary>
      <div class="hab-rec-body">
        <label class="hab-rec-drop" id="habRecDrop">
          <input type="file" id="habRecFile" accept="image/*" hidden>
          <span class="hab-rec-drop-ico">＋</span>
          <span id="habRecDropText">点击选择图片，或把图片直接拖到这里</span>
        </label>
        <div class="hab-rec-cols">
          <p class="hab-note" id="habRecImageNote">还没选图片。</p>
          <div class="row"><label>列数</label><input type="number" id="habRecCols" min="0" max="40" step="1" value="0" placeholder="自动" style="width:62px"><label>排数</label><input type="number" id="habRecRows" min="0" max="40" step="1" value="0" placeholder="自动" style="width:62px"><span class="hab-note" style="margin:0">0＝自动估</span></div>
          <div class="row"><label>格边长上限</label><input type="range" id="habRecCell" min="120" max="900" step="10" value="320" style="width:120px"><span class="hab-adj-val" id="habRecCellVal">320px</span></div>
          <div class="row"><label><input type="checkbox" id="habRecHoles" checked> 识别孔洞</label><label><input type="checkbox" id="habRecNotches" checked> 识别缺口</label></div>
        </div>
        <div class="hab-rec-act">
          <div class="row"><button type="button" id="habRecRun">识别并预览</button><button type="button" id="habRecClear">清掉预览</button></div>
          <div class="row"><button type="button" id="habRecApply">生成到场地（新增）</button><button type="button" id="habRecReplace">替换现有块群</button></div>
          <p class="hab-note" id="habRecNote">只在你点按钮时才会动场地；识别本身不改任何东西。</p>
        </div>
      </div>
    </details>
  </div>
  <div class="hab-stage">"""
assert s.count(anchor) == 1
s = s.replace(anchor, bar)

# 3) 右栏加图层面板
a2 = """      <div id="habAgents"></div>
      <h3>选中调整</h3>"""
b2 = """      <div id="habAgents"></div>
      <h3>图层</h3>
      <p class="hab-note">像 PS 的图层：每块织网单元、每只蚕各是一层。勾两层以上就能编组；「开 / 关」控制这一层显示。</p>
      <div class="row"><button type="button" id="habLayerGroup">编组所选</button><button type="button" id="habLayerUngroup">解散组</button><button type="button" id="habLayerClear">全部展开</button></div>
      <div id="habLayerTree"></div>
      <h3>选中调整</h3>"""
assert s.count(a2) == 1
s = s.replace(a2, b2)

# 4) CSS
css_anchor = "#habRecOverlay{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:7}"
css_new = css_anchor + """
.hab-rec-bar{padding:6px 14px 0}
.hab-rec{background:rgba(255,255,255,0.035);border:1px solid rgba(255,255,255,0.09);border-radius:10px;padding:0 10px}
.hab-rec>summary{cursor:pointer;list-style:none;display:flex;gap:10px;align-items:baseline;padding:8px 2px;font-size:13px}
.hab-rec>summary::-webkit-details-marker{display:none}
.hab-rec-sum{opacity:.55;font-size:12px}
.hab-rec-body{display:grid;grid-template-columns:230px 1fr 1fr;gap:14px;padding:4px 2px 10px;align-items:start}
.hab-rec-drop{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;min-height:112px;border:1.5px dashed rgba(255,255,255,0.22);border-radius:10px;cursor:pointer;text-align:center;font-size:12px;line-height:1.5;color:rgba(255,255,255,0.72);padding:10px}
.hab-rec-drop:hover,.hab-rec-drop.hi{border-color:rgba(121,203,182,0.85);background:rgba(121,203,182,0.08);color:#fff}
.hab-rec-drop-ico{font-size:20px;opacity:.75}
.hab-rec-cols,.hab-rec-act{display:flex;flex-direction:column;gap:6px;min-width:0}
#habLayerTree{display:flex;flex-direction:column;gap:2px;margin:4px 0 6px;max-height:34vh;overflow:auto}
.lay-group{display:flex;align-items:center;gap:6px;padding:3px 4px;border-radius:6px;background:rgba(255,255,255,0.05)}
.lay-group.plain{background:transparent;opacity:.7}
.lay-caret,.lay-gname{background:none;border:0;color:inherit;font:inherit;cursor:pointer;padding:0}
.lay-gname{flex:1;text-align:left;font-size:12px}
.lay-count{font-size:11px;opacity:.5}
.lay-row{display:flex;align-items:center;gap:6px;padding:2px 4px 2px 18px;border-radius:5px}
.lay-row:hover{background:rgba(255,255,255,0.06)}
.lay-row.dim{opacity:.45}
.lay-chk{display:flex}
.lay-icon{font-size:10px;width:16px;text-align:center;opacity:.6}
.lay-name{flex:1;text-align:left;background:none;border:0;color:inherit;font:inherit;font-size:12px;cursor:pointer;padding:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.lay-eye,.lay-caret{font-size:11px;background:rgba(255,255,255,0.08);border:0;color:inherit;border-radius:4px;padding:1px 5px;cursor:pointer}"""
assert s.count(css_anchor) == 1
s = s.replace(css_anchor, css_new)

# 5) 模块追加到最后
mod = io.open(r"H:\tool\silkworm-trajectory\_backup\r38_module.js", encoding="utf-8").read().rstrip()
i = s.rfind("</body>")
s = s[:i] + mod + "\n" + s[i:]

io.open(P, "w", encoding="utf-8").write(s)
print("r38 html ok", len(s))
