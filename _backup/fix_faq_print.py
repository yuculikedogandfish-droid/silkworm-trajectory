import io
G=r"docs\使用说明.html"
s=io.open(G,encoding="utf-8").read()
s=s.replace("  a{color:#24443c!important}",
"""  a{color:#24443c!important}
  .faq dt,.faq dd,.faq dt b{color:#16201d!important}
  .faq dt{font-weight:600}
  .card h2{break-after:avoid;page-break-after:avoid}
  .card h3{break-after:avoid;page-break-after:avoid}""")
io.open(G,"w",encoding="utf-8").write(s)
print("faq print color ok")
