p = r"_backup\gen_edit_qa_r30.py"
s = open(p, encoding="utf-8").read()
s = s.replace("""  const status = [];""", """  window.__weaveTrace = [];
  const status = [];""")
s = s.replace("""    say('5 壁顶点='""", """    say('5a trace=' + JSON.stringify((window.__weaveTrace || []).slice(-3)));
    say('5 壁顶点='""")
open(p, "w", encoding="utf-8").write(s)
print('ok')
