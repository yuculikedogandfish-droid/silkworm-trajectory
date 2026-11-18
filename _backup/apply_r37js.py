import io
P = r"docs\index.html"
s = io.open(P, encoding="utf-8").read()
print("overlay:", s.count("habRecOverlay"), "panel:", s.count("habRecBox"))
print("bodies:", s.count("</body>"))
JS = io.open(r"_backup\r37_module.js", encoding="utf-8").read()
i = s.rfind("</body>")
s = s[:i] + JS + "\n" + s[i:]
io.open(P, "w", encoding="utf-8").write(s)
print("inserted at", i)
