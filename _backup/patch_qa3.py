p = r"_backup\gen_edit_qa_r30.py"
s = open(p, encoding="utf-8").read()
s = s.replace("""    say('4 加壁按下=' + (wallBtn ? wallBtn.getAttribute('aria-pressed') : 'none'));""",
"""    say('4 加壁按下=' + (wallBtn ? wallBtn.getAttribute('aria-pressed') : 'none') + ' 状态=' + JSON.stringify(H.weaveEditState()));""")
s = s.replace("""    pd(115, -80); await new Promise(r => setTimeout(r, 50));""",
"""    pd(115, -80); await new Promise(r => setTimeout(r, 50));
    say('4b 点1=' + JSON.stringify(H.weaveEditState()));""")
open(p, "w", encoding="utf-8").write(s)
print('ok')
