p = r"docs\index.html"
s = open(p, encoding="utf-8").read()
s = s.replace("""      if (window.__weaveTrace) window.__weaveTrace.push('exit ← ' + String(new Error().stack || '').split('\\n').slice(1, 4).join(' / '));
""", "")
s = s.replace('<label>蚕的大小</label>', '<label>蚕大小</label>')
s = s.replace('<label>沿丝路重复</label>', '<label>重复密度</label>')
s = s.replace('<label>丝线粗细</label>', '<label>丝线粗细</label>')
open(p, "w", encoding="utf-8").write(s)
print('trim ok')
