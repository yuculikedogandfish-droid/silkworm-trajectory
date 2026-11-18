import io, re
P=r"docs\index.html"
s=io.open(P,encoding="utf-8").read()

# 1) 删掉 r38 的旧图层模块（保留它的拖拽上传部分）
a=s.index("  /* ---------- 2) 图层面板（组 / 层 / 眼睛 / 编组） ---------- */")
b=s.index("/* ===== r39 个体与图层合并")
end=s.rindex("})();", a, b) + len("})();")
s=s[:a] + "  /* （r39 起：图层已并入右栏统一面板，旧 r38 图层模块整段移除） */\n" + s[end:]
io.open(P,"w",encoding="utf-8").write(s)
print("r38 layer block removed", len(s))
