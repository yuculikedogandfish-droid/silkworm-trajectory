import io
P=r"docs\index.html"
h=io.open(P,encoding="utf-8").read()
anchor=""".lay-name{flex:1 1 auto;"""
add="""#habLayerTree{width:100%}
.lay-row{width:100%;box-sizing:border-box;display:flex;align-items:center}
.lay-name{flex:1 1 auto;"""
h=h.replace(anchor, add,1)
h=h.replace(""".lay-mini{font-size:11px;background:rgba(255,255,255,0.08);border:0;color:inherit;border-radius:4px;padding:1px 5px;cursor:pointer;min-width:20px}""",
""".lay-mini{font-size:10px;background:rgba(255,255,255,0.08);border:0;color:inherit;border-radius:4px;padding:1px 3px;cursor:pointer;min-width:17px;line-height:15px}""")
io.open(P,"w",encoding="utf-8").write(h)

p=r"_backup\r39_module.js"
s=io.open(p,encoding="utf-8").read()
s=s.replace("""    ? ('单元 ' + String(a.id).replace(/^wv-/, '') + (a.w ? ' · ' + Math.round(a.w) + '×' + Math.round(a.h) : ''))""",
"""    ? ('单元 ' + String(a.id).replace(/^wv-/, ''))""")
io.open(p,"w",encoding="utf-8").write(s)
b=h.find("/* ===== r39 个体与图层合并"); st=h.rfind("<script>",0,b); en=h.find("</script>",b)
h=h[:st]+s.rstrip()+h[en+len("</script>"):]
io.open(P,"w",encoding="utf-8").write(h)
print("width ok")
