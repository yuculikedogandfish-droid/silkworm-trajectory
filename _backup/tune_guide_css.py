p = r"_backup\build_guide_r34.py"
s = open(p, encoding="utf-8").read()
s = s.replace("font:10.6pt/1.65", "font:10.1pt/1.6")
s = s.replace("max-height:112mm;object-fit:contain", "max-height:97mm;object-fit:contain")
open(p, "w", encoding="utf-8").write(s)
print("css tuned")
