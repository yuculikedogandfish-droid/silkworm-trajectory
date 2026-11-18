p = r"_backup\gen_r31_qa.py"
s = open(p, encoding="utf-8").read()
s = s.replace("""  const us = H.agents().filter(a => a.kind === 'weave');
  await H.importPointCloudDoc(window.__QA_CLOUD);""",
"""  const us = H.agents().filter(a => a.kind === 'weave');
  us.forEach(u => { u.w = 800; u.h = 800; u.x = 0; u.y = 0; u.tileField = false; });
  await H.importPointCloudDoc(window.__QA_CLOUD);
  us.forEach(u => { if (u.cache && u.cache.clear) u.cache.clear(); H.buildWeave(u); });""")
open(p, "w", encoding="utf-8").write(s)
print('sizes ok')
