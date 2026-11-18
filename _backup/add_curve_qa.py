p = r"_backup\gen_r32_qa.py"
s = open(p, encoding="utf-8").read()
s = s.replace("""for name, body in (('flow', FLOW), ('menu', MENU)):""",
"""CURVE = COMMON + r\"\"\"
  try {
    const a = us[0];
    a.custom = a.custom || { walls: {}, paths: {}, shapes: {} };
    a.custom.shapes['0,0'] = { notch: null, islands: [], notchPts: [
      {x:-240,y:-90},{x:-40,y:-235},{x:180,y:-120},{x:150,y:150},{x:-90,y:205},{x:-235,y:80}] };
    if (a.cache && a.cache.clear) a.cache.clear();
    H.buildWeave(a);
    const c = H.weaveCellContent(a, 0, 0);
    let total = 0;
    (c.paths || []).forEach(p => (p.pts || []).forEach(() => total++));
    say('曲线缺口 控制点=' + a.custom.shapes['0,0'].notchPts.length + ' 丝点=' + total);
    tap(0, 0);
    await new Promise(r => setTimeout(r, 300));
    const fit = document.getElementById('habFit'); if (fit) fit.click();
    await new Promise(r => setTimeout(r, 400));
  } catch (e) { say('ERR ' + e.message); }
})();
\"\"\"

for name, body in (('flow', FLOW), ('menu', MENU), ('curve', CURVE)):""")
open(p, "w", encoding="utf-8").write(s)
print('curve page ok')
