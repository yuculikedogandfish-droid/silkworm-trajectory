import io
for tag in ("v","h"):
    p=rf"_backup\rec43\t_{tag}.html"
    s=io.open(p,encoding="utf-8").read()
    s=s.replace('"\\nsizes=" + sizes.slice(0, 24).join(", ");','"\\nsizes=" + sizes.slice(0, 24).join(", ") + "\\ndbg=" + JSON.stringify(window.__segDebug || {});')
    io.open(p,"w",encoding="utf-8").write(s)
print("dbg added")
