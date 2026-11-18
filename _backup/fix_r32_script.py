p = r"_backup\patch_r32.py"
s = open(p, encoding="utf-8").read()
s = s.replace("""rep(\"\"\"</body>\"\"\",
\"\"\"<div id=\"habCtxMenu\" role=\"menu\"></div>
</body>\"\"\")""",
"""rep_last(\"\"\"</body>\"\"\",
\"\"\"<div id=\"habCtxMenu\" role=\"menu\"></div>
</body>\"\"\")""")
s = s.replace("""rep(\"\"\"</style>\"\"\",
\"\"\"#habCtxMenu{""",
"""rep(\"\"\".hab-tools[aria-disabled=\"true\"] { opacity: .45; pointer-events: none; }\"\"\",
\"\"\".hab-tools[aria-disabled=\"true\"] { opacity: .45; pointer-events: none; }
#habCtxMenu{""")
open(p, "w", encoding="utf-8").write(s)
print("patched script")
