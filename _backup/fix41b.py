import io
p=r"_backup\r39_module.js"
s=io.open(p,encoding="utf-8").read()
old="""    window.addEventListener('pointerup', () => {
      if (marquee && marquee.armed) marqueeSelect(); else marquee = null;"""
new="""    window.addEventListener('pointerup', (e) => {
      if (marquee) {
        try { const p = toWorld(e); marquee.x1 = p.x; marquee.y1 = p.y; } catch (err) {}
      }
      if (marquee && marquee.armed) marqueeSelect(); else marquee = null;"""
assert s.count(old)==1
s=s.replace(old,new)
io.open(p,"w",encoding="utf-8").write(s)
P=r"docs\index.html"
h=io.open(P,encoding="utf-8").read()
i=h.find("/* ===== r39 个体与图层合并"); st=h.rfind("<script>",0,i); en=h.find("</script>",i)
h=h[:st]+s.rstrip()+h[en+len("</script>"):]
io.open(P,"w",encoding="utf-8").write(h)
print("up coords fixed")
