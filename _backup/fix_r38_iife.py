import io
P=r"docs\index.html"
h=io.open(P,encoding="utf-8").read()
old="""  /* （r39 起：图层已并入右栏统一面板，旧 r38 图层模块整段移除） */

</script>"""
new="""  /* （r39 起：图层已并入右栏统一面板，旧 r38 图层模块整段移除） */
})();

</script>"""
assert old in h
h=h.replace(old,new,1)
io.open(P,"w",encoding="utf-8").write(h)
print("r38 iife closed")
