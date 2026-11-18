import io
p=r"_backup\r39_module.js"
s=io.open(p,encoding="utf-8").read()
s=s.replace("""  let guides = [];""", """  let guides = [];
  let marquee = null;""",1)
s=s.replace("""  let marquee = null;   // {x0,y0,x1,y1,add}
""","",1)
io.open(p,"w",encoding="utf-8").write(s)
P=r"docs\index.html"
h=io.open(P,encoding="utf-8").read()
i=h.find("/* ===== r39 个体与图层合并"); st=h.rfind("<script>",0,i); en=h.find("</script>",i)
h=h[:st]+s.rstrip()+h[en+len("</script>"):]
io.open(P,"w",encoding="utf-8").write(h)
print("marquee hoisted")
