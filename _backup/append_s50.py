import io
P=r"PROGRESS_WEAVE_2026-11-16.md"
s=io.open(P,encoding="utf-8").read()
s+="""

## §50 r45 识别条避让顶栏 + 框选批量删除 / 点空白取消（2026-11-19）
- 识别条 `.hab-rec-bar` 不再写死 top:52px，改为按 `.hab-top` 实际底边 +8px 放置（resize / 定时重算），顶栏按钮换行也不会被压住。
- r39 空白单击（未形成框选）清空选择；暴露 `window.__layerSel`（ids/size/set/clear/bbox/editing）。
- r45 独立模块：多选时在选区包围盒内右键 → 删除选中的 N 块（confirm，走 __weaveHooks.deleteUnit，可撤销）/ 编为一组 / 取消选择。
- QA：菜单文本正确；3 块选 2 块右键删后 units=1、sel=0；空白单击 sel=0；recbar_clear=true gap=8 styleTop=101.875px；jserrs=[]。
- 说明书 §11 增补右键批量与点空白取消，PDF 15 页（r45）。commit a1883b9，tag r45，push ok。
"""
io.open(P,"w",encoding="utf-8").write(s)
print("progress appended")
