import io
p=r"_backup\r43_module.js"
s=io.open(p,encoding="utf-8").read()
s=s.replace("      u.w = Math.max(80, Math.round(b.w));\n      u.h = Math.max(80, Math.round(b.h));",
            "      // 不强行拉宽：参考图里本来就有窄条，硬拉到 80 会把版式改样\n      u.w = Math.max(40, Math.round(b.w));\n      u.h = Math.max(40, Math.round(b.h));")
io.open(p,"w",encoding="utf-8").write(s)
print("clamp ok")
