import re, io, sys
s = io.open(r"C:\Users\54364\AppData\Local\Temp\dom43.html", encoding="utf-8", errors="replace").read()
m = re.search(r'<div id="out">(.*?)</div>', s, re.S)
print(m.group(1)[:900] if m else s[:800])
