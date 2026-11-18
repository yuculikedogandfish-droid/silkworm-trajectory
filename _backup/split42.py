import io,re,subprocess,os
h=io.open(r"docs\index.html",encoding="utf-8").read()
parts=re.findall(r"<script>(.*?)</script>", h, re.S)
os.makedirs(r"_backup\chk42",exist_ok=True)
for i,p in enumerate(parts):
    io.open(rf"_backup\chk42\s{i}.js","w",encoding="utf-8").write(p)
print("scripts",len(parts))
