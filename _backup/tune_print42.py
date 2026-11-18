import io
G=r"docs\使用说明.html"
s=io.open(G,encoding="utf-8").read()
s=s.replace(".card{break-inside:avoid;page-break-inside:avoid;margin-bottom:10px}",
            ".card{break-inside:auto;page-break-inside:auto;margin:0 0 8px;padding:10px 0 2px}")
s=s.replace("figure.shot{break-inside:avoid}","figure.shot{break-inside:avoid;page-break-inside:avoid;margin:8px 0}")
s=s.replace(".shot img{border:1px solid #d5dcd8;max-width:100%}",
            ".shot img{border:1px solid #d5dcd8;max-width:100%;max-height:92mm;width:auto}")
io.open(G,"w",encoding="utf-8").write(s)
print("print css tuned")
