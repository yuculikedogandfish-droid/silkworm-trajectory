p = r"_backup\gen_edit_qa_r30.py"
s = open(p, encoding="utf-8").read()
s = s.replace("""    say('3 再点第2块按钮=' + document.getElementById('habWeaveEdit').textContent.trim());""",
"""    say('3 再点第2块按钮=' + document.getElementById('habWeaveEdit').textContent.trim() + ' 状态=' + JSON.stringify(H.weaveEditState()));""")
s = s.replace("""    const origEnter = window.__weaveHooks.enter;
    window.__weaveHooks.enter = (id) => { say('ENTER id=' + id + ' @ ' + String(new Error().stack || '').split('\\n').slice(1, 4).join(' / ')); return origEnter(id); };
""", "")
open(p, "w", encoding="utf-8").write(s)
print('ok')
