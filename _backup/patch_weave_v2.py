import sys
from pathlib import Path

target = Path(sys.argv[1])
spec_txt = Path(sys.argv[2]).read_text(encoding="utf-8")
engine_txt = Path(sys.argv[3]).read_text(encoding="utf-8")

data = target.read_bytes()
crlf = b"\r\n" in data[:5000]
if crlf:
    spec_txt = spec_txt.replace("\n", "\r\n")
    engine_txt = engine_txt.replace("\n", "\r\n")

A_START = b"  function weaveCellSpec(agent) {"
A_END = b"  function weaveSDF(cell, x, y) {"
B_START = b"  function weaveGrowOne(cell, agent, wIdx, profile) {"
B_END = b"  let toastTimer = 0;"

a0 = data.index(A_START)
a1 = data.index(A_END)
b0 = data.index(B_START)
b1 = data.index(B_END)
assert a1 > a0 and b0 > a1
data = data[:a0] + spec_txt.encode("utf-8") + data[a1:b0] + engine_txt.encode("utf-8") + data[b1:]
target.write_bytes(data)
print(f"patched {target}  crlf={crlf}  {len(data)} bytes")
