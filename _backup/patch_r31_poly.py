p = r"_backup\gen_r31_qa.py"
s = open(p, encoding="utf-8").read()
# 1) 在 notch 页面结束时打印更完整的缺口数组
s = s.replace("""    say('2 缺口顶点=' + np.length + ' 格内 spec 缺口点=' + ((cell.notchPts || []).length));""",
"""    say('2 缺口顶点=' + np.length + ' 格内 spec 缺口点=' + ((cell.notchPts || []).length));
    say('2c 顶点=' + JSON.stringify((np || []).map(q => [Math.round(q.x), Math.round(q.y)])));""")
# 2) 追加 poly 页面：直接写缺口形状，验证"避开缺口"渲染
s = s.replace("""JITTER = COMMON + r\"\"\"""", """POLY = COMMON + r\"\"\"
  try {
    const a = us[0];
    a.custom = a.custom || { walls: {}, paths: {}, shapes: {} };
    const pts = [{x:-300,y:-140},{x:30,y:-340},{x:330,y:-60},{x:160,y:270},{x:-230,y:210},{x:-360,y:40}];
    a.custom.shapes['0,0'] = { notch: null, islands: [], notchPts: pts };
    if (a.cache && a.cache.clear) a.cache.clear();
    H.buildWeave(a);
    const cell = H.weaveCellContent(a, 0, 0).cell;
    const th = H.weaveCellContent(a, 0, 0).threads || [];
    const inPoly = (P, x, y) => { let c = false; for (let i = 0, j = P.length - 1; i < P.length; j = i++) { const A = P[i], B = P[j]; if (((A.y > y) !== (B.y > y)) && (x < (B.x - A.x) * (y - A.y) / (B.y - A.y) + A.x)) c = !c; } return c; };
    let inside = 0, total = 0;
    th.forEach(t => (t.pts || t).forEach(q => { total++; if (inPoly(pts, q.x, q.y)) inside++; }));
    say('poly 缺口点=' + ((cell.notchPts || []).length) + ' 丝点=' + total + ' 落缺口=' + inside + ' 丝数=' + th.length);
    const fit = document.getElementById('habFit'); if (fit) fit.click();
    await new Promise(r => setTimeout(r, 500));
  } catch (e) { say('ERR ' + e.message); }
})();
\"\"\"

JITTER = COMMON + r\"\"\"""")
s = s.replace("""for name, body in (('notch', NOTCH), ('jitter', JITTER)):""",
"""for name, body in (('notch', NOTCH), ('jitter', JITTER), ('poly', POLY)):""")
open(p, "w", encoding="utf-8").write(s)
print('poly ok')
