import io
G=r"docs\使用说明.html"
s=io.open(G,encoding="utf-8").read()
s=s.replace('<section class="card"><h2><span>11</span>','<section class="card newpage"><h2><span>11</span>',1)
s=s.replace("  .card h2{break-after:avoid;page-break-after:avoid}","  .newpage{break-before:page;page-break-before:always}\n  .card h2{break-after:avoid;page-break-after:avoid}")
io.open(G,"w",encoding="utf-8").write(s)
print("newpage ok")
