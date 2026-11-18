import io, re
p = r"_backup\patch_r39.py"
s = io.open(p, encoding="utf-8").read()
start = s.index("old = ")
end = s.index("new = ")
old_block = '''old = """      <h3>个体</h3>
      <p class="hab-note">实测蚕随描图数据自动进入；演示蚕从这里拖到场地。状态是放置、拖动、爬行、暂停。</p>
      <div id="habAgents"></div>
      <h3>图层</h3>
      <p class="hab-note">像 PS 的图层：每块织网单元、每只蚕各是一层。勾两层以上就能编组；「开 / 关」控制这一层显示。</p>
      <div class="row"><button type="button" id="habLayerGroup">编组所选</button><button type="button" id="habLayerUngroup">解散组</button><button type="button" id="habLayerClear">全部展开</button></div>
      <div id="habLayerTree"></div>"""
'''
s = s[:start] + old_block + s[end:]
io.open(p, "w", encoding="utf-8").write(s)
print("fixed old block")
