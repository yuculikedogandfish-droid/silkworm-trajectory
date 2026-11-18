import io
p = r"_backup\apply_r37html.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('assert s.count("habRecOverlay") == 0', 'assert s.count(\'id="habRecOverlay"\') == 0')
io.open(p, "w", encoding="utf-8").write(s)
print("guard fixed")
