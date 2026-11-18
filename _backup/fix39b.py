import io
p = r"_backup\r39_module.js"
s = io.open(p, encoding="utf-8").read()
anchor = """    if (at('data-eye')) {"""
add = """    if (at('data-geye')) {
      const gid = at('data-geye');
      const mem = agents().filter(a => store.member[a.id] === gid);
      const anyOn = mem.some(a => !hiddenOf(a));
      mem.forEach(a => setHidden(a, anyOn));
      sig = ''; render(); return;
    }
""" + anchor
assert s.count(anchor) == 1
s = s.replace(anchor, add)
io.open(p, "w", encoding="utf-8").write(s)

P = r"docs\index.html"
h = io.open(P, encoding="utf-8").read()
i = h.find("/* ===== r39 个体与图层合并"); st = h.rfind("<script>", 0, i); en = h.find("</script>", i)
h = h[:st] + s.rstrip() + h[en+len("</script>"):]
io.open(P, "w", encoding="utf-8").write(h)
print("geye fixed")
