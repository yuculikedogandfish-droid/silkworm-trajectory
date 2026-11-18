p = r"_backup\gen_r31_qa.py"
s = open(p, encoding="utf-8").read()
s = s.replace("""  const say = (t) => { status.push(t); out.textContent = status.join('\\n'); };""",
"""  const say = (t) => { status.push(t); out.textContent = status.join('\\n'); };
  window.onerror = (m, src, ln) => { say('ERR ' + m + ' @' + ln); };""")
s = s.replace("""    say('2 缺口顶点=' + ((sh.notchPts || []).length) + ' 色块=' + JSON.stringify(H.weaveEditState()));""",
"""    say('2 缺口顶点=' + ((sh.notchPts || []).length) + ' 色块=' + JSON.stringify(H.weaveEditState()));
    say('2b custom=' + JSON.stringify(us[0].custom).slice(0, 400));""")
open(p, "w", encoding="utf-8").write(s)
print('dbg2 ok')
