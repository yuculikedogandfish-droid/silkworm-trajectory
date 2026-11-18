import io
p=r"_backup\r43_module.js"
s=io.open(p,encoding="utf-8").read()
s=s.replace("      dark[i] = sb[i] < lineThr ? 1 : 0;","      dark[i] = gray[i] < lineThr ? 1 : 0;")
s=s.replace("    const lineThr = Math.max(14, glob * 0.42);","    const lineThr = Math.max(18, glob * 0.55);")
s=s.replace("      let bv = null, bh = null;","      let bv = null, bh = null;\n      if (depth === 0) { window.__segDebug = { v: 0, h: 0, W, H: H2, lineThr }; }")
s=s.replace("        if (sc < 0.55) continue;\n        if (bv && sc <= bv.sc) continue;",
            "        if (depth === 0 && sc > window.__segDebug.v) window.__segDebug.v = Math.round(sc * 100) / 100;\n        if (sc < 0.55) continue;\n        if (bv && sc <= bv.sc) continue;")
s=s.replace("        if (sc < 0.55) continue;\n        if (bh && sc <= bh.sc) continue;",
            "        if (depth === 0 && sc > window.__segDebug.h) window.__segDebug.h = Math.round(sc * 100) / 100;\n        if (sc < 0.55) continue;\n        if (bh && sc <= bh.sc) continue;")
io.open(p,"w",encoding="utf-8").write(s)
print("dark raw ok")
