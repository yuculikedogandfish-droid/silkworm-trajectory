import io
import re
import sys

s = io.open(sys.argv[1], encoding="utf-8", errors="replace").read()
m = re.search(r'data-qa="(.*?)"', s, re.S)
print(m.group(1)[:1600] if m else "NO DATA-QA")
