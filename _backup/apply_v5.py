import io
p = r"_backup\r37_module.js"
s = io.open(p, encoding="utf-8").read()
s = s.replace("const gap = Math.max(2, Math.round(T * 0.02));", "const gap = Math.max(2, Math.round(bW * 0.02));")
assert "Math.round(T *" not in s
io.open(p, "w", encoding="utf-8").write(s)
P = r"docs\index.html"
h = io.open(P, encoding="utf-8").read()
i = h.find("/* ===== r37 图片识别"); start = h.rfind("<script>", 0, i); end = h.find("</script>", i)
h = h[:start] + s.rstrip() + h[end+len("</script>"):]
io.open(P, "w", encoding="utf-8").write(h)
print("gap fixed")
