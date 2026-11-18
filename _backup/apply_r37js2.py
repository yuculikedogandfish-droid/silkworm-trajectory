import io
P = r"docs\index.html"
s = io.open(P, encoding="utf-8").read()
m = "/* ===== r37 图片识别"
i = s.find(m)
assert i > 0
start = s.rfind("<script>", 0, i)
end = s.find("</script>", i)
assert end > 0
new = io.open(r"_backup\r37_module.js", encoding="utf-8").read().rstrip()
s = s[:start] + new + s[end + len("</script>"):]
io.open(P, "w", encoding="utf-8").write(s)
print("module replaced", len(new))
