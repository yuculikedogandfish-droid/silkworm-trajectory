import io,re
s=io.open(r"docs\使用说明.html",encoding="utf-8").read()
s=re.sub(r'data:image/[^;]+;base64,[A-Za-z0-9+/=]+','[图片]',s)
io.open(r"_backup\guide_r45_text.html","w",encoding="utf-8").write(s)
print(len(s))
