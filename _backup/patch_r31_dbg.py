p = r"_backup\gen_r31_qa.py"
s = open(p, encoding="utf-8").read()
s = s.replace("""    for (const q of pts) { pd(q[0], q[1]); await new Promise(r => setTimeout(r, 45)); }""",
"""    let ti = 0;
    for (const q of pts) {
      pd(q[0], q[1]);
      await new Promise(r => setTimeout(r, 60));
      ti++;
      say('tap' + ti + ' → ' + JSON.stringify(H.weaveEditState().drafts) + ' 改=' + JSON.stringify(Object.keys(((us[0].custom || {}).shapes) || {})));
    }""")
open(p, "w", encoding="utf-8").write(s)
print('dbg ok')
