import io
P=r"docs\index.html"
h=io.open(P,encoding="utf-8").read()
i=h.find("/* ===== r45 识别条避让")
st=h.rfind("<script>",0,i)
en=h.find("</script>",i)+len("</script>")
blk=h[st:en]
h=h[:st]+h[en:]
j=h.rfind("</body>")
h=h[:j]+blk+"\n"+h[j:]
io.open(P,"w",encoding="utf-8").write(h)
print("r45 moved to end", h.rfind("r45 识别条避让") > h.rfind("__layerSel ="))
