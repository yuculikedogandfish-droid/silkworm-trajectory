import io
G=r"docs\使用说明.html"
s=io.open(G,encoding="utf-8").read()
s=s.replace("<li>常见问题</li></ol>", "<li>常见问题</li><li>图层、分组与排版</li></ol>",1)
io.open(G,"w",encoding="utf-8").write(s)
print("toc ok" if "图层、分组与排版</li></ol>" in s else "still missing")
