import io
G=r"docs\使用说明.html"
s=io.open(G,encoding="utf-8").read()
s=s.replace("按住空地拖动，超过一点点距离才算框选（所以普通点击不会误选）。框到的块全部选中；按住 Shift 拉框是追加。",
"按住空地拖动，超过一点点距离才算框选（所以普通点击不会误选）。框到的块全部选中；按住 Shift 拉框是追加。<b>在选区里点右键</b>：可以一次删除选中的所有块、把它们编成一组、或取消选择；<b>点选区外的空白</b>就取消选择。")
s=s.replace("版本：<b>r43</b>","版本：<b>r45</b>")
s=s.replace("使用说明 · r43","使用说明 · r45")
io.open(G,"w",encoding="utf-8").write(s)
print("guide r45 ok")
