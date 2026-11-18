import io
p=r"_backup\r38_module.js"
s=io.open(p,encoding="utf-8").read()
old="  setInterval(() => refresh(false), 800);\n  refresh(true);"
new="""  const agentsBox = document.getElementById('habAgents');
  if (agentsBox && window.MutationObserver) {
    new MutationObserver(() => refresh(false)).observe(agentsBox, { childList: true, subtrees: true, subtree: true });
  }
  setInterval(() => refresh(false), 600);
  refresh(true);"""
assert s.count(old)==1
s=s.replace(old,new).replace("subtrees: true, ", "")
io.open(p,"w",encoding="utf-8").write(s)

P=r"docs\index.html"
h=io.open(P,encoding="utf-8").read()
m="/* ===== r38 拖拽上传"
i=h.find(m); start=h.rfind("<script>",0,i); end=h.find("</script>",i)
h=h[:start]+s.rstrip()+h[end+len("</script>"):]
io.open(P,"w",encoding="utf-8").write(h)
print("observer added")
