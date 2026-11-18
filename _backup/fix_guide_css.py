p = r"_backup\build_guide_r34.py"
s = open(p, encoding="utf-8").read()
s = s.replace("table{width:100%;border-collapse:collapse;table-layout:fixed;margin:6pt 0;font-size:8.8pt}",
              "table{width:100%;border-collapse:collapse;table-layout:fixed;margin:6pt 0;font-size:8.8pt;break-inside:avoid}\ntr{break-inside:avoid}")
open(p, "w", encoding="utf-8").write(s)
print("css ok")
