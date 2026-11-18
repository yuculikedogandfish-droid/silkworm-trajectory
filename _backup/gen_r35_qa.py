# -*- coding: utf-8 -*-
"""QA r35：右键添加缺口立刻出现 / 坏锚点不再形成自交小三角 / 孔洞可拉到几乎占满整格"""
import json, os

HTML = r"H:\tool\silkworm-trajectory\docs\index.html"
TMP = os.environ.get('TEMP', r'C:\Users\54364\AppData\Local\Temp')
CLOUD = json.load(open(r"G:\raby model\trajectories.json", encoding='utf-8'))

JS = r"""
(async () => {
  const st = document.createElement('style');
  st.textContent = 'body > *:not(#habitat):not(#habCtxMenu):not(script):not(style){display:none}';
  document.head.appendChild(st);
  await new Promise(r => setTimeout(r, 900));
  const H = window.__studioHabitat;
  H.addWeave({});
  const us = H.agents().filter(a => a.kind === 'weave');
  us.forEach(u => { u.w = 620; u.h = 620; u.x = 0; u.y = 0; u.tileField = false; u.shape = 'plain'; u.seed = 3141; });
  await H.importPointCloudDoc(window.__QA_CLOUD);
  us.forEach(u => { u.custom = u.custom || {walls:{},paths:{},shapes:{}}; if (u.cache && u.cache.clear) u.cache.clear(); H.buildWeave(u); });
  H.seekTo(7);

  const out = document.createElement('div');
  out.style.cssText = 'position:fixed;left:16px;bottom:110px;z-index:99999;color:#ffd76a;font:12px monospace;background:#000d;padding:6px 8px;max-width:1200px;white-space:pre-wrap';
  (document.getElementById('habitat') || document.body).appendChild(out);
  const log = []; const say = t => { log.push(t); out.textContent = log.join(String.fromCharCode(10)); };
  window.onerror = (m, s2, l) => say('ERR ' + m + ' @' + l);
  const cv = document.getElementById('habWorld');
  const vw = () => H.view();
  const toS = (wx, wy) => { const v = vw(); const r = cv.getBoundingClientRect(); return { x: r.left + v.px(wx), y: r.top + v.py(wy) }; };
  const ptr = (type, wx, wy, buttons) => {
    const q = toS(wx, wy);
    cv.dispatchEvent(new PointerEvent(type, { clientX: q.x, clientY: q.y, button: 0, buttons: buttons, bubbles: true, pointerId: 1, isPrimary: true }));
  };
  const tap = (wx, wy) => { ptr('pointerdown', wx, wy, 1); ptr('pointerup', wx, wy, 0); };
  const shape = () => (us[0].custom.shapes['0,0'] || {});

  // 与页面内相同的向心 CR（对照：均匀 CR）
  const uniCurve = (pts) => {
    const n = pts.length, get = i => pts[((i % n) + n) % n], out2 = [];
    for (let i = 0; i < n; i++) {
      const p0 = get(i - 1), p1 = get(i), p2 = get(i + 1), p3 = get(i + 2);
      for (let s2 = 0; s2 < 10; s2++) {
        const t = s2 / 10, t2 = t * t, t3 = t2 * t;
        out2.push({
          x: 0.5 * (2 * p1.x + (-p0.x + p2.x) * t + (2 * p0.x - 5 * p1.x + 4 * p2.x - p3.x) * t2 + (-p0.x + 3 * p1.x - 3 * p2.x + p3.x) * t3),
          y: 0.5 * (2 * p1.y + (-p0.y + p2.y) * t + (2 * p0.y - 5 * p1.y + 4 * p2.y - p3.y) * t2 + (-p0.y + 3 * p1.y - 3 * p2.y + p3.y) * t3),
        });
      }
    }
    return out2;
  };
  const cenCurve = (pts) => {
    const n = pts.length, get = i => pts[((i % n) + n) % n], out2 = [], al = 0.5;
    const lp = (a, b, t) => ({ x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t });
    for (let i = 0; i < n; i++) {
      const p0 = get(i - 1), p1 = get(i), p2 = get(i + 1), p3 = get(i + 2);
      const d01 = Math.pow(Math.hypot(p1.x - p0.x, p1.y - p0.y), al) || 1e-4;
      const d12 = Math.pow(Math.hypot(p2.x - p1.x, p2.y - p1.y), al) || 1e-4;
      const d23 = Math.pow(Math.hypot(p3.x - p2.x, p3.y - p2.y), al) || 1e-4;
      const t0 = 0, t1 = t0 + d01, t2 = t1 + d12, t3 = t2 + d23;
      for (let s2 = 0; s2 < 10; s2++) {
        const tt = t1 + (t2 - t1) * (s2 / 10);
        const A1 = lp(p0, p1, (tt - t0) / (t1 - t0)), A2 = lp(p1, p2, (tt - t1) / (t2 - t1)), A3 = lp(p2, p3, (tt - t2) / (t3 - t2));
        const B1 = lp(A1, A2, (tt - t0) / (t2 - t0)), B2 = lp(A2, A3, (tt - t1) / (t3 - t1));
        out2.push(lp(B1, B2, (tt - t1) / (t2 - t1)));
      }
    }
    return out2;
  };
  const cross = (o, a, b) => (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
  const segX = (a, b, cc, d) => {
    const d1 = cross(a, b, cc), d2 = cross(a, b, d), d3 = cross(cc, d, a), d4 = cross(cc, d, b);
    return ((d1 > 0) !== (d2 > 0)) && ((d3 > 0) !== (d4 > 0));
  };
  const selfX = (pts) => {
    let cnt2 = 0;
    for (let i = 0; i < pts.length; i++) {
      const a = pts[i], b = pts[(i + 1) % pts.length];
      for (let j = i + 2; j < pts.length; j++) {
        if (Math.abs(i - j) < 2 || (i === 0 && j === pts.length - 1)) continue;
        const cc = pts[j], d = pts[(j + 1) % pts.length];
        if (segX(a, b, cc, d)) cnt2++;
      }
    }
    return cnt2;
  };

  try {
    tap(0, 0);
    await new Promise(r => setTimeout(r, 220));
    // A. 一串正常点，然后故意把两个锚点拖到几乎重合（复现用户的"小三角"）
    const P0 = [{x:-250,y:-110},{x:-60,y:-250},{x:170,y:-150},{x:190,y:110},{x:-10,y:220},{x:-225,y:110}];
    shape().notchPts = P0.map(q => ({ x: q.x, y: q.y }));
    us[0].cache && us[0].cache.delete && us[0].cache.delete('0,0');
    H.weaveCellContent(us[0], 0, 0);
    let bad = P0.map(q => ({ x: q.x, y: q.y }));
    bad.splice(5, 1);
    bad.splice(5, 0, { x: -225 + 6, y: 110 - 4 });   // 两个点只差 ~7px
    say('A 挤在一起的 6 点：均匀曲线自交=' + selfX(uniCurve(bad)) + ' · 向心曲线自交=' + selfX(cenCurve(bad)));
    // B. 右键 → 添加缺口，应当立刻出现一个可见缺口
    shape().notchPts = undefined; delete shape().notchPts;
    us[0].cache && us[0].cache.delete && us[0].cache.delete('0,0');
    H.weaveCellContent(us[0], 0, 0);
    const q = toS(120, 60);
    cv.dispatchEvent(new MouseEvent('contextmenu', { clientX: q.x, clientY: q.y, bubbles: true, cancelable: true, button: 2 }));
    await new Promise(r => setTimeout(r, 300));
    const btns = Array.from(document.querySelectorAll('#habCtxMenu button'));
    const lab = btns.map(b => b.textContent);
    say('B 菜单=' + lab.join(' | '));
    const addBtn = btns.find(b => b.textContent.indexOf('添加缺口') >= 0);
    if (addBtn) addBtn.click();
    await new Promise(r => setTimeout(r, 350));
    say('C 点「添加缺口」后 notchPts=' + ((shape().notchPts || []).length) + ' 首点=' + JSON.stringify((shape().notchPts || [])[0] || null));
    // D. 孔洞拉到超过 45% 上限
    shape().islands = [{ cx: 0, cy: 0, r: 60 }];
    us[0].cache && us[0].cache.delete && us[0].cache.delete('0,0');
    H.weaveCellContent(us[0], 0, 0);
    await new Promise(r => setTimeout(r, 80));
    ptr('pointerdown', 0 + 60, 0, 1);
    await new Promise(r => setTimeout(r, 60));
    ptr('pointermove', 0 + 400, 0, 1);
    await new Promise(r => setTimeout(r, 60));
    ptr('pointerup', 400, 0, 0);
    await new Promise(r => setTimeout(r, 200));
    const isl = (shape().islands || [])[0] || {};
    say('D 拖完 孔半径=' + Math.round(isl.r || 0) + '（620 格的 45% = 279）');
    document.getElementById('habFit') && document.getElementById('habFit').click();
    await new Promise(r => setTimeout(r, 500));
  } catch (e) { say('ERR ' + e.message); }
})();
"""

src = open(HTML, 'r', encoding='utf-8').read()
cloud = 'window.__QA_CLOUD=%s;' % json.dumps(CLOUD)
open(os.path.join(TMP, 'r35.html'), 'w', encoding='utf-8').write(src + '<script>%s</script><script>%s</script>' % (cloud, JS))
print('r35.html')
