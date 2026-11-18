p = r"_backup\gen_edit_qa_r30.py"
s = open(p, encoding="utf-8").read()
s = s.replace("""    pd(115, -80); await new Promise(r => setTimeout(r, 50));""",
"""    const origEnter = window.__weaveHooks.enter;
    window.__weaveHooks.enter = (id) => { say('ENTER called id=' + id); return origEnter(id); };
    pd(115, -80); await new Promise(r => setTimeout(r, 50));""")
open(p, "w", encoding="utf-8").write(s)
print('ok')
