# -*- coding: utf-8 -*-
import re, subprocess, tempfile, os, sys
p = r"H:\tool\silkworm-trajectory\docs\index.html"
s = open(p, encoding="utf-8").read()
node = r"C:\Users\54364\AppData\Local\Doubao User Data\sandbox_runtime\bases\fa694f517e5995233c80a9a8db5212c2\node\node.exe"

scripts = re.findall(r"<script>([\s\S]*?)</script>", s)
print("script blocks:", len(scripts))
fail = 0
for i, code in enumerate(scripts):
    fd, path = tempfile.mkstemp(suffix=".js", text=True)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(code)
    r = subprocess.run([node, "--check", path], capture_output=True, text=True, encoding="utf-8")
    ok = r.returncode == 0
    print("block", i, "lines", code.count("\n") + 1, "syntax_ok:", ok)
    if not ok:
        fail += 1
        print(r.stderr[:1200])
    os.unlink(path)
sys.exit(0 if fail == 0 else 1)
