import io
P=r"docs\index.html"
h=io.open(P,encoding="utf-8").read()
mod=io.open(r"_backup\r43_module.js",encoding="utf-8").read()
i=h.find("/* ===== r47")
if i < 0: i=h.find("/* ===== r43 识别升级")
j=h.find("</script>",i)
h=h[:i]+mod.rstrip()+h[j:]
io.open(P,"w",encoding="utf-8").write(h)
print("index r43 updated", len(h))
