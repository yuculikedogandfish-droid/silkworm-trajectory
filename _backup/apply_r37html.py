import io
P = r"docs\index.html"
s = io.open(P, encoding="utf-8").read()
assert s.count('id="habRecOverlay"') == 0

a = """      <canvas id="habDepth" class="depth" aria-hidden="true"></canvas>"""
b = a + """
      <canvas id="habRecOverlay" aria-hidden="true"></canvas>"""
assert s.count(a) == 1
s = s.replace(a, b)

c = "#habCtxMenu{position:fixed;"
d = """#habRecOverlay{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:7}
#habCtxMenu{position:fixed;"""
assert s.count(c) == 1
s = s.replace(c, d)

e = """      <p class="hab-note" id="habImgStatus">还没导出。</p>
    </aside>"""
f = """      <p class="hab-note" id="habImgStatus">还没导出。</p>
      <details id="habRecBox" class="hab-rec">
        <summary>从图片识别版式（上传一张图，自动铺块）</summary>
        <p class="hab-note">上传一张拼接好的丝片照片或设计稿：自动找出格子、几排几列、哪里缺块，以及格内的圆孔／缺口，先给你看预览，确认后再生成到场地。不影响场地里现有的东西。</p>
        <div class="row"><input type="file" id="habRecFile" accept="image/*"></div>
        <p class="hab-note" id="habRecImageNote">还没选图片。</p>
        <div class="row"><label>目标格边长</label><input type="range" id="habRecCell" min="120" max="900" step="10" value="320"><span class="hab-adj-val" id="habRecCellVal">320px</span></div>
        <div class="row"><label><input type="checkbox" id="habRecHoles" checked> 识别孔洞</label><label><input type="checkbox" id="habRecNotches" checked> 识别缺口</label></div>
        <div class="row"><button type="button" id="habRecRun">识别并预览</button><button type="button" id="habRecClear">清掉预览</button></div>
        <div class="row"><button type="button" id="habRecApply">生成到场地（新增）</button><button type="button" id="habRecReplace">替换现有块群</button></div>
        <p class="hab-note" id="habRecNote">只在你点按钮时才会动场地；识别本身不改任何东西。</p>
      </details>
    </aside>"""
assert s.count(e) == 1
s = s.replace(e, f)
io.open(P, "w", encoding="utf-8").write(s)
print("html ok", s.count("habRecOverlay"))
