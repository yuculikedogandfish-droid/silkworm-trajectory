import io,re
s=io.open(r"docs\使用说明.html",encoding="utf-8").read()
js=re.findall(r"<script>([\s\S]*?)</script>",s)
io.open(r"_backup\chk42\guide-inline.js","w",encoding="utf-8").write("\n".join(js))
print("guide scripts",len(js))
