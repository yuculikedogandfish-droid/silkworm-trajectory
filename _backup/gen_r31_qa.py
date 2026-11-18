# -*- coding: utf-8 -*-
"""QA r31：大格子 + 手画多边形缺口 + 壁旁逐帧抖动测量"""
import json, os

HTML = r"H:\tool\silkworm-trajectory\docs\index.html"
TMP = os.environ.get('TEMP', r'C:\Users\54364\AppData\Local\Temp')
CLOUD = json.load(open(r"G:\raby model\trajectories.json", encoding='utf-8'))

HEAD = r"""
(async () => {
  const s = document.createElement('style');
  s.textContent = 'body > *:not(#habitat):not(script):not(style){display:none}';
  document.head.appendChild(s);
  await new Promise(r => setTimeout(r, 900));
  const H = window.__studioHabitat;
  H.addWeave({ w: 800, h: 800 });
"""

COMMON = r"""
  const us = H.agents().filter(a => a.kind === 'weave');
  us.forEach(u => { u.w = 800; u.h = 800; u.x = 0; u.y = 0; u.tileField = false; u.shape = 'plain'; u.seed = 2026; });
  await H.importPointCloudDoc(window.__QA_CLOUD);
  us.forEach(u => { if (u.cache && u.cache.clear) u.cache.clear(); H.buildWeave(u); });
  H.seekTo(9);
  const status = [];
  const out = document.createElement('div');
  out.style.cssText = 'position:fixed;left:16px;bottom:110px;z-index:99999;color:#ffd76a;font:12px monospace;background:#000d;padding:6px 8px;max-width:1200px;white-space:pre-wrap';
  (document.getElementById('habitat') || document.body).appendChild(out);
  const say = (t) => { status.push(t); out.textContent = status.join('\n'); };
  window.onerror = (m, src, ln) => { say('ERR ' + m + ' @' + ln); };
"""

NOTCH = COMMON + r"""
  const cv = document.getElementById('habWorld');
  const pd = (wx, wy) => {
    const v = H.view(); const r = cv.getBoundingClientRect();
    cv.dispatchEvent(new PointerEvent('pointerdown', {
      clientX: r.left + v.px(wx), clientY: r.top + v.py(wy),
      button: 0, buttons: 1, bubbles: true, pointerId: 1, isPrimary: true,
    }));
    cv.dispatchEvent(new PointerEvent('pointerup', {
      clientX: r.left + v.px(wx), clientY: r.top + v.py(wy),
      button: 0, buttons: 0, bubbles: true, pointerId: 1, isPrimary: true,
    }));
  };
  const inPoly = (pts, x, y) => {
    let c = false;
    for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
      const a = pts[i], b = pts[j];
      if (((a.y > y) !== (b.y > y)) && (x < (b.x - a.x) * (y - a.y) / (b.y - a.y) + a.x)) c = !c;
    }
    return c;
  };
  try {
    pd(60, 60);   // 点格内（偏一点，避开正中"移动"手柄）
    await new Promise(r => setTimeout(r, 200));
    say('1 进编辑=' + JSON.stringify(H.weaveEditState()));
    document.querySelector('#habWeaveTools .hab-tool[data-wtool="notch"]').click();
    await new Promise(r => setTimeout(r, 80));
    const pts = [[-300, -140], [30, -340], [330, -60], [160, 270], [-230, 210]];
    for (const q of pts) { pd(q[0], q[1]); await new Promise(r => setTimeout(r, 55)); }
    document.getElementById('habWeaveEditEnd').click();
    await new Promise(r => setTimeout(r, 500));
    const sh = (us[0].custom.shapes || {})['0,0'] || {};
    const cell = H.weaveCellContent(us[0], 0, 0).cell;
    const np = (sh.notchPts || []);
    say('2 缺口顶点=' + np.length + ' 格内 spec 缺口点=' + ((cell.notchPts || []).length));
    say('2c 顶点=' + JSON.stringify((np || []).map(q => [Math.round(q.x), Math.round(q.y)])));
    const th = H.weaveCellContent(us[0], 0, 0).threads || [];
    let inHole = 0, total = 0;
    th.forEach(t => (t.pts || t).forEach(q => { total++; if (np.length >= 3 && inPoly(np, q.x, q.y)) inHole++; }));
    say('3 丝点总数=' + total + ' 落进缺口=' + inHole);
    say('4 格尺寸=' + Math.round(us[0].w) + '×' + Math.round(us[0].h) + ' 每格丝=' + th.length);
    const fit = document.getElementById('habFit');
    if (fit) fit.click();
    await new Promise(r => setTimeout(r, 400));
  } catch (e) { say('ERR ' + e.message); }
})();
"""

POLY = COMMON + r"""
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
"""

JITTER = COMMON + r"""
  try {
    const a = us[0];
    a.custom = a.custom || { walls: {}, paths: {}, shapes: {} };
    a.custom.walls['0,0'] = [{ pts: [{ x: -400, y: -150 }, { x: -100, y: -60 }, { x: 200, y: -160 }, { x: 400, y: -80 }], closed: false }];
    if (a.cache && a.cache.clear) a.cache.clear();
    H.buildWeave(a);
    const worm = H.agents().find(z => z.kind === 'route' && z.scope === 'cell');
    if (!worm) { say('没有格内蚕'); return; }
    worm.mode = 'run'; worm.follow = true; worm.speedScale = 1;
    const wall = a.custom.walls['0,0'][0].pts.map(q => ({ x: a.x + q.x, y: a.y + q.y }));
    const distToWall = (x, y) => {
      let best = Infinity;
      for (let i = 1; i < wall.length; i++) {
        const A = wall[i - 1], B = wall[i];
        const ex = B.x - A.x, ey = B.y - A.y, L2 = ex * ex + ey * ey || 1;
        let t = ((x - A.x) * ex + (y - A.y) * ey) / L2; t = Math.max(0, Math.min(1, t));
        best = Math.min(best, Math.hypot(x - (A.x + ex * t), y - (A.y + ey * t)));
      }
      return best;
    };
    const dt = 1 / 60;
    const trail = [];
    for (let i = 0; i < 900; i++) {
      H.step(dt);
      trail.push({ x: worm.x, y: worm.y, d: distToWall(worm.x, worm.y) });
    }
    let near = 0, pen = 0, rev = 0, maxStep = 0, sumStep = 0, nearSteps = 0, nearMax = 0;
    for (let i = 2; i < trail.length; i++) {
      const p0 = trail[i - 2], p1 = trail[i - 1], p2 = trail[i];
      const v1 = { x: p1.x - p0.x, y: p1.y - p0.y };
      const v2 = { x: p2.x - p1.x, y: p2.y - p1.y };
      const l1 = Math.hypot(v1.x, v1.y), l2 = Math.hypot(v2.x, v2.y);
      sumStep += l2;
      if (l2 > maxStep) maxStep = l2;
      if (p2.d < 8) {
        near++;
        nearSteps += l2;
        if (l2 > nearMax) nearMax = l2;
        if (l1 > 1e-6 && l2 > 1e-6) {
          const cos = (v1.x * v2.x + v1.y * v2.y) / (l1 * l2);
          if (cos < -0.35) rev++;
        }
      }
      if (p2.d < 1.2) pen++;
    }
    say('帧数=' + trail.length + ' 贴壁帧=' + near + ' 掉头帧=' + rev + '(占贴壁 ' +
        (near ? (rev / near * 100).toFixed(1) : '0') + '%)');
    say('穿壁帧=' + pen + ' 最大单帧位移=' + maxStep.toFixed(2) + ' 平均=' + (sumStep / trail.length).toFixed(2));
    say('贴壁时最大单帧位移=' + nearMax.toFixed(2) + ' 贴壁平均单帧=' + (near ? (nearSteps / near).toFixed(2) : '0'));
  } catch (e) { say('ERR ' + e.message); }
})();
"""

src = open(HTML, 'r', encoding='utf-8').read()
cloud = 'window.__QA_CLOUD=%s;' % json.dumps(CLOUD)
for name, body in (('notch', NOTCH), ('jitter', JITTER), ('poly', POLY)):
    p = os.path.join(TMP, 'qa-r31-%s.html' % name)
    open(p, 'w', encoding='utf-8').write(
        src.replace('</body>', '<script>%s</script><script>%s</script></body>' % (cloud, HEAD + body)))
    print(p)
