import io
p=r"_backup\r43_module.js"
s=io.open(p,encoding="utf-8").read()
s=s.replace("    const closed = morph(morph(mask, w, h, 2, true), w, h, 2, false);",
            "    const CR = (window.__rec43close != null ? window.__rec43close : 1);\n    const closed = CR > 0 ? morph(morph(mask, w, h, CR, true), w, h, CR, false) : mask;")
io.open(p,"w",encoding="utf-8").write(s)
print("close param ok")
