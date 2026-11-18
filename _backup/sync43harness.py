# -*- coding: utf-8 -*-
import io
mod = io.open(r"H:\tool\silkworm-trajectory\_backup\r43_module.js", encoding="utf-8").read()
for tag in ("v", "h"):
    p = rf"H:\tool\silkworm-trajectory\_backup\rec43\t_{tag}.html"
    s = io.open(p, encoding="utf-8").read()
    i = s.find("/* ===== r47")
    if i < 0: i = s.find("/* ===== r43")
    j = s.find("</script>", i)
    s = s[:i] + mod.rstrip() + s[j:]
    io.open(p, "w", encoding="utf-8").write(s)
print("harness synced")
