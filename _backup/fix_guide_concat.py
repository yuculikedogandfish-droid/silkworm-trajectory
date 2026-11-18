p = r"_backup\build_guide_r34.py"
lines = open(p, encoding="utf-8").read().split("\n")
out = []
for i, ln in enumerate(lines):
    if ln.startswith("  fig(") and ln.rstrip().endswith(")"):
        if out and out[-1].rstrip().endswith("'"):
            out[-1] = out[-1].rstrip() + " +"
        out.append(ln.rstrip() + " +")
    else:
        out.append(ln)
open(p, "w", encoding="utf-8").write("\n".join(out))
print("concat fixed")
