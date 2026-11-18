import io
p=r"_backup\r39_module.js"
s=io.open(p,encoding="utf-8").read()
s=s.replace("""  const nameOf = (a) => a.kind === 'weave' ? ('织网单元 ' + a.id) : (a.kind === 'route' ? ('蚕 ' + a.wormId) : String(a.id));""",
"""  const nameOf = (a) => a.kind === 'weave'
    ? ('单元 ' + String(a.id).replace(/^wv-/, '') + (a.w ? ' · ' + Math.round(a.w) + '×' + Math.round(a.h) : ''))
    : (a.kind === 'route' ? ('蚕 ' + (a.wormId != null ? a.wormId : a.id)) : String(a.id));""")
s=s.replace("""'<button type="button" class="lay-name" data-focus="' + a.id + '">'""",
"""'<button type="button" class="lay-name" title="选中这一层" data-focus="' + a.id + '">'""")
io.open(p,"w",encoding="utf-8").write(s)

P=r"docs\index.html"
h=io.open(P,encoding="utf-8").read()
i=h.find("/* ===== r39 个体与图层合并"); st=h.rfind("<script>",0,i); en=h.find("</script>",i)
h=h[:st]+s.rstrip()+h[en+len("</script>"):]
h=h.replace(""".lay-mini{font-size:11px""", """.lay-name{flex:1 1 auto;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-align:left}
.lay-row{gap:3px}
.lay-mini{font-size:11px""",1)
io.open(P,"w",encoding="utf-8").write(h)
print("labels ok")
