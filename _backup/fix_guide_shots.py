p = r"_backup\gen_guide_shots_r33.py"
s = open(p, encoding="utf-8").read()
s = s.replace("""  await new Promise(r => setTimeout(r, 900));
  const H = window.__studioHabitat;
  const us0 = H.agents().filter(a => a.kind === 'weave');""",
"""  const st = document.createElement('style');
  st.textContent = 'body > *:not(#habitat):not(#habCtxMenu):not(script):not(style){display:none}';
  document.head.appendChild(st);
  await new Promise(r => setTimeout(r, 900));
  const H = window.__studioHabitat;
  H.addWeave({});""")
open(p, "w", encoding="utf-8").write(s)
print('shots fixed')
