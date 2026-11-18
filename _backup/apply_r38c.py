import io
p=r"_backup\r38_module.js"
s=io.open(p,encoding="utf-8").read()
s=s.replace("""title="' + (off ? '显示这一层' : '隐藏这一层') + '">' + (off ? '关' : '开') + '</button>'""", """title="' + (off ? '显示这一层' : '隐藏这一层') + '">' + (off ? '隐' : '显') + '</button>'""")
s=s.replace("""' + (allOff ? '关' : '开') + '</button>'""", """' + (allOff ? '隐' : '显') + '</button>'""")
io.open(p,"w",encoding="utf-8").write(s)
P=r"docs\index.html"
h=io.open(P,encoding="utf-8").read()
m="/* ===== r38 拖拽上传"; i=h.find(m); start=h.rfind("<script>",0,i); end=h.find("</script>",i)
h=h[:start]+s.rstrip()+h[end+len("</script>"):]
io.open(P,"w",encoding="utf-8").write(h)
print("labels ok")
