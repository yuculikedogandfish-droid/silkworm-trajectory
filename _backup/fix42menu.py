import io
p=r"_backup\r39_module.js"
s=io.open(p,encoding="utf-8").read()
s=s.replace("    document.body.appendChild(menuEl);", "    (document.getElementById('habitat') || document.body).appendChild(menuEl);",1)
io.open(p,"w",encoding="utf-8").write(s)
P=r"docs\index.html"
h=io.open(P,encoding="utf-8").read()
i=h.find("/* ===== r39 个体与图层合并"); st=h.rfind("<script>",0,i); en=h.find("</script>",i)
h=h[:st]+s.rstrip()+h[en+len("</script>"):]
io.open(P,"w",encoding="utf-8").write(h)
print("menu container ok")
