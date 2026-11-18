
(function () {
  if (document.body.classList.contains('embed')) return;

  const MODEL = 'habitat-demo-0.1';
  const habitat = {
    shape: 'square',
    tempC: 25,
    humidity: 65,
    seed: 1,
    simTime: 0,
    runningClock: false,
    tool: 'worm',
    selected: null,
    selectedLeaf: null,
    agents: [],
    orphans: [],
    obstacles: [],
    reference: null,
    undo: [],
    redo: [],
    drag: null,
    mistPhase: 0,
    showGrid: true,
    weaveEdit: null,
  };

  const habViewport = {
    zoom: 1,
    panX: 0,
    panY: 0,
    panMode: false,
  };

  /* 本脚本块独立作用域：单位向量工具需在本块内定义 */
  function safeUnit(x, y) {
    const len = Math.hypot(x, y);
    if (!Number.isFinite(len) || len < 1e-6) return { x: 0, y: -1 };
    return { x: x / len, y: y / len };
  }

  function mulberry32(a) {
    return function () {
      a |= 0; a = a + 0x6D2B79F5 | 0;
      let t = Math.imul(a ^ a >>> 15, 1 | a);
      t ^= t + Math.imul(t ^ t >>> 7, 61 | t);
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }

  function arenaSpec() {
    if (habitat.shape === 'rect') return { kind: 'rect', hw: 220, hh: 140 };
    if (habitat.shape === 'circle') return { kind: 'circle', r: 180 };
    return { kind: 'square', hw: 180, hh: 180 };
  }

  function insideArena(x, y, pad) {
    const a = arenaSpec();
    const p = pad || 0;
    if (a.kind === 'circle') return x * x + y * y <= (a.r - p) * (a.r - p);
    return Math.abs(x) <= a.hw - p && Math.abs(y) <= a.hh - p;
  }

  function inLeaf(x, y, leaf, pad) {
    const extra = pad || 0;
    const dx = x - leaf.x, dy = y - leaf.y;
    const c = Math.cos(-leaf.rot), s = Math.sin(-leaf.rot);
    const lx = dx * c - dy * s;
    const ly = dx * s + dy * c;
    const rx = leaf.rx + extra, ry = leaf.ry + extra;
    return (lx * lx) / (rx * rx) + (ly * ly) / (ry * ry) < 1;
  }

  function blocked(x, y) {
    return !insideArena(x, y, 10);
  }

  /* ================= 织网单元（P1 单格引擎，移植自 prototype/weave-lab.html） ================= */
  const WEAVE_DEMO_PROFILE = {
    id: 'demo-weave',
    label: '演示指纹（非实测）',
    source: { kind: 'assumption', note: '蚕室单格联调用；论文与展陈必须换 measured 指纹' },
    stepMean: 1.8, curveAmp: 0.26, maxTurn: 0.72, noise: 0.045, phaseStep: 0.020,
    turnSignPersistence: 3, loopsHint: 2.4,
  };

  // 八字纵横比来自实测蚕样本：G:\raby model\trajectories.json
  // (curves3d/v2, worm 1, 2 笔丝迹 29.5mm / 40.9mm，纵横比 1.78 / 1.45，标定 61.06 px/mm)
  // 环圈形状为理想化平滑八字（x=sin t, y=sin 2t，纵向 > 横向），真实折线回放由指纹 pathTemplate 提供（暂未接入逐点回放）。

  function weaveProfile() { return habitat.weaveProfile || WEAVE_DEMO_PROFILE; }
  function weaveProfileOf(agent) { return (agent && agent.profile) || weaveProfile(); }

  // 真实轨迹模板：G:\raby model\trajectories.json
  // (curves3d/v2, worm 1, 两笔 114/158 点, 标定 61.06 px/mm)；每笔按弧长重采样到 140 点、逐笔等比归一化到 [-1,1]。
  // 织块里的每一条纤维都是这组实测折线的缩放/旋转/散布复制，不再用正弦或随机游走合成。
  const WEAVE_MEASURED_PATHS = [
  [
    -0.2858,0.3183,-0.2858,0.3003,-0.2858,0.2823,-0.2858,0.2643,-0.2855,0.2463,-0.2849,0.2283,-0.2841,0.2104,-0.2832,0.1924,
    -0.2823,0.1744,-0.2814,0.1565,-0.2805,0.1385,-0.2796,0.1205,-0.2787,0.1025,-0.2779,0.0846,-0.2770,0.0666,-0.2765,0.0486,
    -0.2764,0.0306,-0.2764,0.0126,-0.2764,-0.0054,-0.2764,-0.0234,-0.2764,-0.0413,-0.2764,-0.0593,-0.2764,-0.0773,-0.2764,-0.0953,
    -0.2764,-0.1133,-0.2764,-0.1313,-0.2777,-0.1492,-0.2808,-0.1669,-0.2842,-0.1846,-0.2863,-0.2024,-0.2906,-0.2191,-0.3050,-0.2298,
    -0.3199,-0.2399,-0.3375,-0.2431,-0.3555,-0.2425,-0.3603,-0.2278,-0.3607,-0.2098,-0.3607,-0.1918,-0.3607,-0.1738,-0.3605,-0.1558,
    -0.3595,-0.1379,-0.3572,-0.1200,-0.3541,-0.1023,-0.3493,-0.0850,-0.3409,-0.0690,-0.3332,-0.0528,-0.3275,-0.0358,-0.3176,-0.0213,
    -0.3045,-0.0090,-0.2908,0.0026,-0.2767,0.0139,-0.2627,0.0251,-0.2492,0.0370,-0.2362,0.0494,-0.2229,0.0616,-0.2080,0.0716,
    -0.1939,0.0829,-0.1810,0.0953,-0.1683,0.1081,-0.1555,0.1208,-0.1428,0.1335,-0.1301,0.1462,-0.1173,0.1589,-0.1046,0.1716,
    -0.0920,0.1844,-0.0803,0.1981,-0.0700,0.2129,-0.0605,0.2282,-0.0508,0.2433,-0.0407,0.2582,-0.0304,0.2729,-0.0202,0.2878,
    -0.0108,0.3031,-0.0031,0.3193,0.0023,0.3365,0.0073,0.3538,0.0131,0.3708,0.0202,0.3873,0.0229,0.4050,0.0226,0.4229,
    0.0128,0.4359,-0.0039,0.4400,-0.0219,0.4400,-0.0399,0.4400,-0.0578,0.4393,-0.0751,0.4353,-0.0900,0.4252,-0.1047,0.4149,
    -0.1168,0.4016,-0.1273,0.3870,-0.1346,0.3706,-0.1409,0.3538,-0.1444,0.3363,-0.1452,0.3183,-0.1452,0.3003,-0.1453,0.2824,
    -0.1456,0.2644,-0.1468,0.2464,-0.1487,0.2285,-0.1511,0.2107,-0.1529,0.1928,-0.1541,0.1748,-0.1545,0.1569,-0.1546,0.1389,
    -0.1546,0.1209,-0.1546,0.1029,-0.1546,0.0849,-0.1546,0.0669,-0.1546,0.0489,-0.1546,0.0309,-0.1546,0.0129,-0.1546,-0.0051,
    -0.1546,-0.0231,-0.1546,-0.0411,-0.1546,-0.0591,-0.1546,-0.0770,-0.1546,-0.0950,-0.1546,-0.1130,-0.1546,-0.1310,-0.1546,-0.1490,
    -0.1546,-0.1670,-0.1546,-0.1850,-0.1546,-0.2030,-0.1546,-0.2210,-0.1638,-0.2317,-0.1687,-0.2408,-0.1586,-0.2557,-0.1484,-0.2705,
    -0.1440,-0.2875,-0.1391,-0.3046,-0.1301,-0.3200,-0.1185,-0.3338,-0.1064,-0.3470,-0.0940,-0.3600,-0.0813,-0.3728,-0.0686,-0.3855,
    -0.0555,-0.3978,-0.0420,-0.4098,-0.0280,-0.4210,-0.0118,-0.4282,0.0038,-0.4241,0.0178,-0.4128,0.0306,-0.4003,0.0409,-0.3857,
    0.0480,-0.3692,0.0549,-0.3526,0.0626,-0.3363,0.0715,-0.3207,0.0765,-0.3034,0.0833,-0.2868,0.0917,-0.2708,0.0969,-0.2539,
    0.0987,-0.2360,0.0997,-0.2180,0.1012,-0.2001,0.1031,-0.1822,0.1053,-0.1644,0.1077,-0.1465,0.1108,-0.1288,0.1150,-0.1113,
    0.1194,-0.0939,0.1236,-0.0764,0.1273,-0.0588,0.1305,-0.0411,0.1337,-0.0234,0.1372,-0.0057,0.1412,0.0118,0.1455,0.0293,
    0.1499,0.0467,0.1533,0.0644,0.1547,0.0823,0.1576,0.1001,0.1615,0.1176,0.1637,0.1354,0.1640,0.1534,0.1646,0.1713,
    0.1670,0.1891,0.1708,0.2067,0.1733,0.2245,0.1733,0.2425,0.1733,0.2605,0.1602,0.2703,0.1425,0.2715,0.1268,0.2640,
    0.1197,0.2484,0.1175,0.2306,0.1171,0.2126,0.1171,0.1946,0.1171,0.1766,0.1165,0.1587,0.1139,0.1409,0.1091,0.1235,
    0.1078,0.1056,0.1078,0.0876,0.1078,0.0696,0.1083,0.0516,0.1116,0.0341,0.1180,0.0173,0.1259,0.0012,0.1340,-0.0149,
    0.1423,-0.0309,0.1513,-0.0464,0.1611,-0.0615,0.1698,-0.0773,0.1791,-0.0927,0.1879,-0.1084,0.1915,-0.1256,0.1951,-0.1432,
    0.2032,-0.1589,0.2136,-0.1736,0.2201,-0.1898,0.2209,-0.2077,0.2251,-0.2251,0.2332,-0.2412,0.2384,-0.2584,0.2389,-0.2764,
    0.2389,-0.2944,0.2389,-0.3123,0.2389,-0.3303,0.2389,-0.3483,0.2389,-0.3529,0.2389,-0.3349,0.2390,-0.3169,0.2392,-0.2989,
    0.2407,-0.2811,0.2456,-0.2638,0.2527,-0.2472,0.2593,-0.2305,0.2660,-0.2138,0.2724,-0.1970,0.2789,-0.1802,0.2853,-0.1634,
    0.2917,-0.1466,0.2980,-0.1297,0.3043,-0.1129,0.3107,-0.0960,0.3170,-0.0792,0.3232,-0.0623,0.3295,-0.0454,0.3358,-0.0286,
    0.3420,-0.0117,0.3482,0.0052,0.3542,0.0222,0.3589,0.0395,0.3607,0.0573,0.3607,0.0753,0.3607,0.0933,0.3607,0.1113,
    0.3607,0.1293,0.3606,0.1473,0.3567,0.1648,0.3478,0.1800,0.3369,0.1943,0.3278,0.2097,0.3206,0.2262,0.3130,0.2425,
    0.3040,0.2581,0.2932,0.2723,0.2776,0.2805,0.2657,0.2674,0.2626,0.2497,0.2602,0.2318,0.2584,0.2139,0.2586,0.1960,
    0.2615,0.1783,0.2658,0.1608,0.2708,0.1435,0.2759,0.1263,0.2809,0.1090,0.2858,0.0917,0.2905,0.0743,0.2950,0.0569,
    0.2992,0.0394,0.3032,0.0218,0.3067,0.0042,0.3100,-0.0135,0.3133,-0.0312,0.3171,-0.0488,0.3212,-0.0663,0.3254,-0.0838,
    0.3293,-0.1013,0.3322,-0.1191,0.3334,-0.1370,0.3376,-0.1545,0.3425,-0.1718,0.3470,-0.1892,0.3502,-0.2069,0.3514,-0.2248,
    0.3514,-0.2428,0.3514,-0.2608,0.3514,-0.2788,0.3514,-0.2968,0.3514,-0.3148,0.3514,-0.3328,0.3514,-0.3508,0.3513,-0.3688,
    0.3505,-0.3867,0.3485,-0.4046,0.3455,-0.4224,0.3420,-0.4400
  ],
  ];

  function weaveTemplates(agent) {
    const pt = agent && agent.profile && agent.profile.pathTemplate;
    if (pt && Array.isArray(pt.strokes) && pt.strokes.length &&
        Array.isArray(pt.strokes[0]) && typeof pt.strokes[0][0] === 'number') {
      return pt.strokes;
    }
    return WEAVE_MEASURED_PATHS;
  }

  function weaveWallRepel(walls, x, y, r) {
    if (!walls || !walls.length) return { x, y };
    let px = x, py = y;
    walls.forEach(line => {
      const pts = line.pts || line;
      for (let k = 0; k < pts.length - 1; k++) {
        const ax = pts[k].x, ay = pts[k].y, bx = pts[k + 1].x, by = pts[k + 1].y;
        const dx = bx - ax, dy = by - ay;
        const L2 = dx * dx + dy * dy || 1;
        let t = ((px - ax) * dx + (py - ay) * dy) / L2;
        t = Math.max(0, Math.min(1, t));
        const qx = ax + dx * t, qy = ay + dy * t;
        const d = Math.hypot(px - qx, py - qy);
        if (d < r) {
          const n = d || 1;
          px = qx + (px - qx) / n * r;
          py = qy + (py - qy) / n * r;
        }
      }
    });
    return { x: px, y: py };
  }

  // 点到多边形边界的最短距离（用于给轮廓留边距）
  // 缺口：控制点 -> 闭合平滑曲线（Catmull-Rom）。所有判定/绘制都走这一份，形状才是"曲线闭合"。
  function weaveNotchCurve(pts) {
    if (!Array.isArray(pts) || pts.length < 3) return pts || [];
    // 向心 Catmull-Rom（alpha=0.5）：锚点疏密不均时不会鼓出自交的小圈/尖角
    const n = pts.length;
    const get = (i) => pts[((i % n) + n) % n];
    const alpha = 0.5;
    const lerp = (a, b, t) => ({ x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t });
    const out = [];
    const steps = 8;
    for (let i = 0; i < n; i++) {
      const p0 = get(i - 1), p1 = get(i), p2 = get(i + 1), p3 = get(i + 2);
      const d01 = Math.pow(Math.hypot(p1.x - p0.x, p1.y - p0.y), alpha) || 1e-4;
      const d12 = Math.pow(Math.hypot(p2.x - p1.x, p2.y - p1.y), alpha) || 1e-4;
      const d23 = Math.pow(Math.hypot(p3.x - p2.x, p3.y - p2.y), alpha) || 1e-4;
      const t0 = 0, t1 = t0 + d01, t2 = t1 + d12, t3 = t2 + d23;
      for (let s2 = 0; s2 < steps; s2++) {
        const tt = t1 + (t2 - t1) * (s2 / steps);
        const A1 = lerp(p0, p1, (tt - t0) / (t1 - t0));
        const A2 = lerp(p1, p2, (tt - t1) / (t2 - t1));
        const A3 = lerp(p2, p3, (tt - t2) / (t3 - t2));
        const B1 = lerp(A1, A2, (tt - t0) / (t2 - t0));
        const B2 = lerp(A2, A3, (tt - t1) / (t3 - t1));
        out.push(lerp(B1, B2, (tt - t1) / (t2 - t1)));
      }
    }
    return out;
  }

  function weavePolyDist(pts, x, y) {
    let best = Infinity;
    for (let i = 0, n = pts.length; i < n; i++) {
      const a = pts[i], b = pts[(i + 1) % n];
      const dx = b.x - a.x, dy = b.y - a.y;
      const L2 = dx * dx + dy * dy || 1;
      let t = ((x - a.x) * dx + (y - a.y) * dy) / L2;
      t = Math.max(0, Math.min(1, t));
      const d = Math.hypot(x - (a.x + dx * t), y - (a.y + dy * t));
      if (d < best) best = d;
    }
    return best;
  }

  function weaveInPoly(pts, x, y) {
    let inside = false;
    for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
      const xi = pts[i].x, yi = pts[i].y, xj = pts[j].x, yj = pts[j].y;
      if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / ((yj - yi) || 1e-9) + xi) inside = !inside;
    }
    return inside;
  }

  // Catmull-Rom 平滑：壁/轮廓按控制点插值成曲线（像建模软件的平滑手柄效果）
  function weaveSmooth(pts, closed, tol) {
    if (!pts || pts.length < 2) return pts || [];
    const cl = !!closed && pts.length >= 3;
    // 闭合时在两端各补一个环绕点，接缝处切线才连续（不然首尾会鼓出一个折角）
    const P = cl
      ? [pts[pts.length - 1], ...pts, pts[0], pts[1]].map(p => ({ x: p.x, y: p.y }))
      : pts.map(p => ({ x: p.x, y: p.y }));
    if (!cl) P.push(P[0]);
    const out = [];
    const steps = 5;
    for (let i = 0; i < P.length - 1; i++) {
      const p0 = P[Math.max(0, i - 1)], p1 = P[i], p2 = P[i + 1], p3 = P[Math.min(P.length - 1, i + 2)];
      for (let s = 0; s < steps; s++) {
        const t = s / steps, t2 = t * t, t3 = t2 * t;
        out.push({
          x: 0.5 * (2 * p1.x + (-p0.x + p2.x) * t + (2 * p0.x - 5 * p1.x + 4 * p2.x - p3.x) * t2 + (-p0.x + 3 * p1.x - 3 * p2.x + p3.x) * t3),
          y: 0.5 * (2 * p1.y + (-p0.y + p2.y) * t + (2 * p0.y - 5 * p1.y + 4 * p2.y - p3.y) * t2 + (-p0.y + 3 * p1.y - 3 * p2.y + p3.y) * t3),
        });
      }
    }
    out.push(P[P.length - 1]);
    return out;
  }

  // 可织区域判定：格内（或自定义轮廓内）、圆孔外、缺口外（用显式几何，避免 SDF 符号约定混淆）
  function weaveAllowed(cell, x, y, margin) {
    const m = margin || 2;
    if (cell.outline && cell.outline.length >= 3) {
      if (!weaveInPoly(cell.outline, x, y)) return false;
      if (weavePolyDist(cell.outline, x, y) < m) return false;
    } else if (Math.abs(x) > cell.w / 2 - m || Math.abs(y) > cell.h / 2 - m) return false;
    if (cell.notch && Math.hypot(x - cell.notch.cx, y - cell.notch.cy) < cell.notch.r + m) return false;
    // 手画的缺口：任意闭合多边形（不是圆），内侧与贴边都算不能织
    if (Array.isArray(cell.notchPts) && cell.notchPts.length >= 3) {
      const cv = weaveNotchCurve(cell.notchPts);
      if (weaveInPoly(cv, x, y) || weavePolyDist(cv, x, y) < m) return false;
    }
    const islands = cell.islands || (cell.island ? [cell.island] : []);
    for (let k = 0; k < islands.length; k++) {
      if (Math.hypot(x - islands[k].cx, y - islands[k].cy) < islands[k].r + m) return false;
    }
    return true;
  }

  function weaveCellSpecAt(agent, ix, iy, seed) {
    const rng = mulberry32(seed >>> 0);
    const base = Math.min(agent.w, agent.h);
    const shape = agent.shape || 'plain';
    const cell = { w: agent.w, h: agent.h, shape, ix, iy, notch: null, notchPts: null, islands: [],
      outline: (Array.isArray(agent.outline) && agent.outline.length >= 3) ? agent.outline : null };
    if (shape === 'notch' || shape === 'notchIsland') {
      // 参考图里既有四分之一圆缺角，也有贴边的半圆缺口
      const edge = rng() < 0.55;
      if (edge) {
        const side = Math.floor(rng() * 4);
        const t = 0.2 + rng() * 0.6;
        cell.notch = {
          corner: -1,
          cx: side === 0 ? -agent.w / 2 : (side === 1 ? agent.w / 2 : (t - 0.5) * agent.w),
          cy: side === 2 ? -agent.h / 2 : (side === 3 ? agent.h / 2 : (t - 0.5) * agent.h),
          r: base * (0.30 + rng() * 0.20),
        };
      } else {
        const corner = Math.floor(rng() * 4);
        cell.notch = {
          corner,
          cx: (corner % 2 === 1 ? 1 : -1) * agent.w / 2,
          cy: (corner < 2 ? -1 : 1) * agent.h / 2,
          r: base * (0.26 + rng() * 0.18),
        };
      }
    }
    if (shape === 'island' || shape === 'notchIsland') {
      // 大圆孔负空间：每格 1–2 个（参考图里孔径约为格宽的 45%–70%）
      const n = 1 + (rng() < 0.5 ? 1 : 0);
      for (let k = 0; k < n; k++) {
        cell.islands.push({
          cx: (rng() - 0.5) * agent.w * 0.40,
          cy: (rng() - 0.5) * agent.h * 0.40,
          r: base * (0.22 + rng() * 0.13),
        });
      }
    }
    return cell;
  }

  function weaveCellSpec(agent) { return weaveCellSpecAt(agent, 0, 0, (agent.seed >>> 0) || 1); }

  function weaveSDF(cell, x, y) {
    let d = Math.max(Math.abs(x) - cell.w / 2, Math.abs(y) - cell.h / 2);
    if (cell.notch) {
      d = Math.max(d, -(Math.hypot(x - cell.notch.cx, y - cell.notch.cy) - cell.notch.r));
    }
    const islands = cell.islands || (cell.island ? [cell.island] : []);
    for (let k = 0; k < islands.length; k++) {
      const isl = islands[k];
      d = Math.max(d, -(Math.hypot(x - isl.cx, y - isl.cy) - isl.r));
    }
    return d;
  }

  function weaveSimplify(pts, tol) {
    if (pts.length < 3) return pts;
    const keep = new Uint8Array(pts.length);
    keep[0] = 1; keep[pts.length - 1] = 1;
    const stack = [[0, pts.length - 1]];
    while (stack.length) {
      const [a, b] = stack.pop();
      const ax = pts[a].x, ay = pts[a].y, bx = pts[b].x, by = pts[b].y;
      const dx = bx - ax, dy = by - ay, L = Math.hypot(dx, dy) || 1;
      let maxD = -1, maxI = -1;
      for (let i = a + 1; i < b; i++) {
        const d = Math.abs((pts[i].x - ax) * dy - (pts[i].y - ay) * dx) / L;
        if (d > maxD) { maxD = d; maxI = i; }
      }
      if (maxD > tol && maxI > 0) { keep[maxI] = 1; stack.push([a, maxI], [maxI, b]); }
    }
    return pts.filter((_, i) => keep[i]);
  }

  function weaveChain(segs) {
    if (!segs.length) return [];
    const key = p => Math.round(p.x * 8) + ':' + Math.round(p.y * 8);
    const map = new Map();
    segs.forEach((s, i) => {
      [s[0], s[1]].forEach(p => {
        const k = key(p);
        if (!map.has(k)) map.set(k, []);
        map.get(k).push(i);
      });
    });
    const used = new Uint8Array(segs.length);
    const out = [];
    for (let i = 0; i < segs.length; i++) {
      if (used[i]) continue;
      used[i] = 1;
      const line = [segs[i][0], segs[i][1]];
      for (let g = 0; g < 400; g++) {
        const endK = key(line[line.length - 1]);
        const cands = (map.get(endK) || []).filter(j => !used[j]);
        if (!cands.length) break;
        const s = segs[cands[0]];
        used[cands[0]] = 1;
        line.push(key(s[0]) === endK ? s[1] : s[0]);
      }
      for (let g = 0; g < 400; g++) {
        const startK = key(line[0]);
        const cands = (map.get(startK) || []).filter(j => !used[j]);
        if (!cands.length) break;
        const s = segs[cands[0]];
        used[cands[0]] = 1;
        line.unshift(key(s[0]) === startK ? s[1] : s[0]);
      }
      if (line.length > 1) {
        const closed = key(line[0]) === key(line[line.length - 1]);
        if (closed && line.length > 4) {
          const open = line.slice(0, -1);
          const simp = weaveSimplify(open, 0.4);
          simp.push({ x: simp[0].x, y: simp[0].y });
          out.push(simp);
        } else {
          out.push(weaveSimplify(line, 0.4));
        }
      }
    }
    return out;
  }

  function weaveContour(cell) {
    const W = cell.w, H = cell.h;
    const step = Math.max(2, Math.min(W, H) / 60);
    const x0 = -W / 2 - 2, y0 = -H / 2 - 2;
    const nx = Math.ceil((W + 4) / step) + 1;
    const ny = Math.ceil((H + 4) / step) + 1;
    const v = new Float32Array(nx * ny);
    for (let j = 0; j < ny; j++) {
      for (let i = 0; i < nx; i++) {
        v[j * nx + i] = weaveSDF(cell, x0 + i * step, y0 + j * step);
      }
    }
    const segs = [];
    const ip = (a, b, va, vb) => {
      const t = va / (va - vb || 1e-6);
      return { x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t };
    };
    for (let j = 0; j < ny - 1; j++) {
      for (let i = 0; i < nx - 1; i++) {
        const v00 = v[j * nx + i], v10 = v[j * nx + i + 1];
        const v01 = v[(j + 1) * nx + i], v11 = v[(j + 1) * nx + i + 1];
        let code = 0;
        if (v00 < 0) code |= 1;
        if (v10 < 0) code |= 2;
        if (v11 < 0) code |= 4;
        if (v01 < 0) code |= 8;
        if (code === 0 || code === 15) continue;
        const a = { x: x0 + i * step, y: y0 + j * step };
        const b = { x: x0 + (i + 1) * step, y: y0 + j * step };
        const c = { x: x0 + (i + 1) * step, y: y0 + (j + 1) * step };
        const d = { x: x0 + i * step, y: y0 + (j + 1) * step };
        const top = () => ip(a, b, v00, v10);
        const right = () => ip(b, c, v10, v11);
        const bottom = () => ip(d, c, v01, v11);
        const left = () => ip(a, d, v00, v01);
        switch (code) {
          case 1: case 14: segs.push([left(), top()]); break;
          case 2: case 13: segs.push([top(), right()]); break;
          case 3: case 12: segs.push([left(), right()]); break;
          case 4: case 11: segs.push([right(), bottom()]); break;
          case 6: case 9: segs.push([top(), bottom()]); break;
          case 7: case 8: segs.push([left(), bottom()]); break;
          case 5: segs.push([left(), top()], [right(), bottom()]); break;
          case 10: segs.push([top(), right()], [bottom(), left()]); break;
        }
      }
    }
    return weaveChain(segs);
  }

  function weaveSdfGrad(cell, x, y) {
    const e = 0.8;
    return {
      dx: (weaveSDF(cell, x + e, y) - weaveSDF(cell, x - e, y)) / (2 * e),
      dy: (weaveSDF(cell, x, y + e) - weaveSDF(cell, x, y - e)) / (2 * e),
    };
  }

  function weaveProject(cell, x, y, pad) {
    for (let k = 0; k < 5; k++) {
      const d = weaveSDF(cell, x, y);
      if (d <= -pad) break;
      const g = weaveSdfGrad(cell, x, y);
      const len = Math.hypot(g.dx, g.dy) || 1;
      const push = d + pad + 0.3;
      x -= g.dx / len * push;
      y -= g.dy / len * push;
    }
    return { x, y };
  }

  /* 一根丝 = 「真实丝迹回放」连成的连续线：
     每一笔都是实测样本里蚕走过的折线（弧长重采样后的原始形状，不理想化）；
     一笔织完 → 短距离爬行到下一处 → 再织一笔。密织时多根这样的丝叠在一格里。
     碰到格边或圆孔负空间就断笔（真实蚕不会穿墙），返回若干段折线。 */
  // 织块主方向按格决定（同格所有丝同向），参考图每块方向一致
  function weaveBandAngle(cell) {
    return (weaveHash01(cell.ix, cell.iy, 991) - 0.5) * 0.9;
  }

  // 把（可能多笔的）实测丝路接成一条连续核：一笔走完接下一笔
  function weaveRoutePoints(agent) {
    const tpls = weaveTemplates(agent);
    if (!tpls || !tpls.length) return [];
    if (tpls.length === 1) return tpls[0];
    const flat = [];
    tpls.forEach(t => { for (let i = 0; i < t.length; i++) flat.push(t[i]); });
    return flat;
  }

  // 一条丝 = 这条实测丝路在块内连续走 2–3 圈（不是把短笔缩成小圈铺 4×4）。
  // 撞壁的走法：不断线、不镜面折射，而是**贴着壁滑**——只保留切向分量，丝就顺着壁过去。
  function weaveThread(cell, agent, seed, customWalls, bandIndex, bandCount) {
    const rng = mulberry32(seed >>> 0);
    const W = cell.w, H = cell.h;
    const minWH = Math.min(W, H);
    const cov = Math.max(0.15, Math.min(0.85, Number.isFinite(agent.coverage) ? agent.coverage : 0.55));
    const route = weaveRoutePoints(agent);
    const sn2 = route.length >> 1;
    const segs = [];
    const bi = bandIndex || 0;
    if (!sn2) return segs;
    // 丝路尺度：scaleK = 一条实测丝路铺成格子宽度的几倍。
    // 实测单次吐丝 bbox 9.5×11.59 mm，样本 cell_mm=10 → 1.0 就是"一次吐丝≈一格"的真实比例，
    // 现在的 0.22–0.32 是把丝路缩小了 3–4 倍（一段丝的尺度失真），所以默认按真实比例走。
    const k = Number.isFinite(agent.scaleK) ? agent.scaleK : 0.9;
    const fit = minWH * k * (0.94 + cov * 0.10);
    // 3×3 位阵 + 多层叠放：每条丝路铺到格子 1/4 上下，整格才铺得开；孔洞挡住时绕壁过去
    const islands = cell.islands || (cell.island ? [cell.island] : []);
    const tileN = 9;
    const ti = bi % tileN;
    const vi = Math.floor(bi / tileN);
    const col = (ti % 3) - 1;
    const row = Math.floor(ti / 3) - 1;
    let px0 = col * W * 0.36 + (rng() - 0.5) * W * 0.12;
    let py0 = row * H * 0.36 + (rng() - 0.5) * H * 0.12;
    for (let t = 0; t < 6; t++) {
      let bad = false;
      for (let ii = 0; ii < islands.length; ii++) {
        if (Math.hypot(px0 - islands[ii].cx, py0 - islands[ii].cy) < islands[ii].r * 0.55) { bad = true; break; }
      }
      if (!bad) break;
      px0 += (rng() - 0.5) * W * 0.16;
      py0 += (rng() - 0.5) * H * 0.16;
    }
    const baseAng = weaveBandAngle(cell) + (rng() - 0.5) * 0.6 + vi * 0.35;
    const wob = Math.max(0.6, minWH * 0.003);
    const wallR = minWH * 0.02;
    let cur = [];
    const flush = () => { if (cur.length > 3) segs.push(cur); cur = []; };
    let last = { x: px0, y: py0 };
    const push = (x, y) => {
      const q = weaveWallRepel(customWalls, x, y, wallR);
      cur.push({ x: q.x, y: q.y });
      last = { x: q.x, y: q.y };
    };
    const ang = baseAng;
    const sc = fit * (0.94 + rng() * 0.14);
    const cs = Math.cos(ang), sn = Math.sin(ang);
    // 让 route[0] 落在落点上（这一条丝从这里开始爬）
    const ox = last.x - (route[0] * sc * cs - route[1] * sc * sn);
    const oy = last.y - (route[0] * sc * sn + route[1] * sc * cs);
    for (let k = 0; k < sn2; k += 2) {
      const kx = route[k * 2] * sc, ky = route[k * 2 + 1] * sc;
      const px = ox + kx * cs - ky * sn + (rng() - 0.5) * wob;
      const py = oy + kx * sn + ky * cs + (rng() - 0.5) * wob;
      if (weaveAllowed(cell, px, py, 2)) { push(px, py); continue; }
      // —— 撞壁 ——
      const circ = weaveWallNormal(cell, px, py);
      if (!circ) {
        // 撞的是块的外框：把点压到框上继续走。
        // 这样跨块接缝处不会被硬切成"一堆断头"，而是丝一直铺到框边再被裁掉。
        const ef = weaveWallProject(cell, px, py, 1.2);
        if (ef) push(ef.x, ef.y);
        continue;
      }
      // 圆形壁（孔 / 缺口）：真实蚕不会把丝织到孔里：丝在壁面收口（端点落在壁上），
      // 然后跳过孔洞，从孔另一侧重新起一段丝。中间那段空白正好被孔遮住，看不出断口；
      // 不做贴壁圆弧（那会沿孔口连成一条亮环），也不做镜面折返（那是锐角）。
      const e = weaveWallProject(cell, px, py, 1.4);
      if (e) push(e.x, e.y);
      flush();
      // 碰壁之后蚕会摆头换方向再试几次：从接触点朝两侧短距离试探，每次都被壁挡回。
      // 这些短段散在壁外侧、长度和方向都不同，所以孔口密度是「试出来的」，
      // 不是另画一圈——不会连成等半径亮环，也不会出现镜面锐角。
      const bdx = px - last.x, bdy = py - last.y;
      const bd = (bdx || bdy) ? Math.atan2(bdy, bdx) : 0;
      const tries = 2;
      for (let t2 = 0; t2 < tries; t2++) {
        const dz = (t2 % 2 ? 1 : -1) * (Math.PI / 2 + (rng() - 0.5) * 0.9);
        let sx = last.x, sy = last.y, sdir = bd + dz;
        const trial = [];
        for (let s = 0; s < 12; s++) {
          const stp = 1.5 + rng() * 1.3;
          sx += Math.cos(sdir) * stp;
          sy += Math.sin(sdir) * stp;
          if (!weaveAllowed(cell, sx, sy, 1)) break;
          trial.push({ x: sx, y: sy });
          sdir += (rng() - 0.5) * 0.6;
        }
        if (trial.length > 2) segs.push(trial);
      }
      let okJ = -1;
      for (let j = k + 1; j < Math.min(sn2, k + 60); j++) {
        const qx = route[j * 2] * sc, qy = route[j * 2 + 1] * sc;
        const wx = ox + qx * cs - qy * sn, wy = oy + qx * sn + qy * cs;
        if (weaveAllowed(cell, wx, wy, 2)) { okJ = j; break; }
      }
      if (okJ < 0) break;
      k = okJ - 1;
    }
    flush();
    return segs;
  }


  function weaveHash01(ix, iy, seed) {
    let h = Math.imul(ix, 374761393) ^ Math.imul(iy, 668265263) ^ (seed >>> 0);
    h = Math.imul(h ^ (h >>> 13), 1274126177);
    return ((h ^ (h >>> 16)) >>> 0) / 4294967295;
  }

  function weaveCellContent(agent, ix, iy) {
    if (!agent.cache || typeof agent.cache.get !== 'function') agent.cache = new Map();
    const key = ix + ',' + iy;
    const hit = agent.cache.get(key);
    if (hit) return hit;
    const seed = (((agent.seed >>> 0) ^ Math.imul(ix, 374761393) ^ Math.imul(iy, 668265263)) ^ 0x9e3779b9) >>> 0;
    const cell0 = weaveCellSpecAt(agent, ix, iy, seed);
    const custom = agent.custom || (agent.custom = { walls: {}, paths: {}, shapes: {} });
    if (!custom.shapes) custom.shapes = {};
    const manual = custom.shapes[key];
    const cell = {
      w: cell0.w, h: cell0.h, shape: cell0.shape, ix, iy,
      notch: manual && 'notch' in manual ? manual.notch : cell0.notch,
      notchPts: manual && manual.notchPts ? manual.notchPts : cell0.notchPts,
      islands: manual && manual.islands ? manual.islands : cell0.islands,
      outline: cell0.outline,
    };
    const customWalls = (custom.walls && custom.walls[key]) || [];
    const customPaths = (custom.paths && custom.paths[key]) || [];
    const n = Math.max(1, Math.min(12, Math.round(agent.worms || 6)));
    // 一条丝 = 一排实测笔迹；每格丝数决定排数（越多越密，参考图那种层层叠压）
    const covN = Math.max(0.15, Math.min(0.85, Number.isFinite(agent.coverage) ? agent.coverage : 0.55));
    // 覆盖率同时驱动「排数」与「笔迹尺寸」：0.2 稀疏、0.7 密织
    // 一条丝 = 一条长回放（一格里 2–3 趟），所以丝数是 12 上下，不再是一百多条短笔
    const bandCount = Math.max(20, Math.min(72, Math.round(n * 7.0 * (0.55 + covN * 1.3))));
    const paths = [];
    // 参考图里有整块空着的黑格：按格哈希留缺口（人工编辑过的格不封）
    // 手放的单元一定织满；只有整场铺格模式才按哈希留空格（参考图里有整块黑板）
    const blank = !customWalls.length && !customPaths.length && !manual
      && agent.tileField && weaveHash01(ix, iy, seed + 7) > 0.88;
    if (!blank) {
      for (let b = 0; b < bandCount; b++) {
        const segs = weaveThread(cell, agent, (seed + b * 7919 + 17) >>> 0, customWalls, b, bandCount);
        segs.forEach(seg => {
          const pts = Array.isArray(seg) ? seg : seg.pts;
          const mul = Array.isArray(seg) ? 1 : (seg.mul != null ? seg.mul : 1);
          if (pts.length > 6) paths.push({
            pts, seed, b,
            a: (0.13 + weaveHash01(b, b + 31, seed) * 0.22) * (0.72 + covN * 0.5) * mul,
          });
        });
      }
      customPaths.forEach(p => {
        const pts = (p.pts || p).map(q => ({ x: q.x, y: q.y }));
        if (pts.length > 2) paths.push({ pts, seed, custom: true });
      });
    }
    // 丝迹一律收口：先躲开孔洞/缺口，再夹进格子矩形；穿洞的线段就地加密后逐点贴回孔缘
    const cwHalf = Math.max(8, cell.w / 2 - 1.2), chHalf = Math.max(8, cell.h / 2 - 1.2);
    const holeCenters = (cell.islands || (cell.island ? [cell.island] : []))
      .concat(cell.notch ? [cell.notch] : []);
    const clampRect = (x, y) => ({
      x: Math.max(-cwHalf, Math.min(cwHalf, x)),
      y: Math.max(-chHalf, Math.min(chHalf, y)),
    });
    const nearHole = (x, y) => holeCenters.some(o => Math.hypot(x - o.cx, y - o.cy) < o.r + 9)
      || (Array.isArray(cell.notchPts) && cell.notchPts.length >= 3 && weavePolyDist(weaveNotchCurve(cell.notchPts), x, y) < 9);
    paths.forEach(p => {
      const src = p.pts;
      const out = [];
      for (let i = 0; i < src.length; i++) {
        const q = clampRect(src[i].x, src[i].y);
        const proj = weaveWallProject(cell, q.x, q.y, 1.6);
        const c = proj || q;
        const prev = out.length ? out[out.length - 1] : null;
        if (prev && holeCenters.length && (nearHole(prev.x, prev.y) || nearHole(c.x, c.y))) {
          // 两个点都在孔附近：中间插入若干点，逐点贴回孔缘，避免一根弦横穿孔洞
          const seg = Math.hypot(c.x - prev.x, c.y - prev.y);
          const n = Math.max(1, Math.min(24, Math.ceil(seg / 4)));
          for (let k = 1; k < n; k++) {
            const t = k / n;
            const mx = prev.x + (c.x - prev.x) * t, my = prev.y + (c.y - prev.y) * t;
            const pr = weaveWallProject(cell, mx, my, 1.6);
            out.push(pr || { x: mx, y: my });
          }
        }
        out.push(c);
      }
      p.pts = out;
    });
    const content = { cell, paths, walls: weaveContour(cell), customWalls, seed, blank };
    agent.cache.set(key, content);
    if (agent.cache.size > 360) agent.cache.delete(agent.cache.keys().next().value);
    return content;
  }

  function buildWeave(agent) {
    agent.cache = new Map();
    agent.paths = [];
    agent.walls = [];
    const origin = weaveCellContent(agent, 0, 0);
    agent.sample = {
      threads: origin.paths.length,
      points: origin.paths.reduce((s, p) => s + p.pts.length, 0),
      walls: origin.walls.length,
      custom: (agent.custom ? Object.keys(agent.custom.walls || {}).length + Object.keys(agent.custom.paths || {}).length : 0),
    };
    if (!Number.isFinite(agent.u)) agent.u = 0;
  }

  function makeWeaveAgent(x, y, seed) {
    const s = (seed == null ? Math.floor(Math.random() * 1e9) : seed) >>> 0;
    // 场地里只有一只实测蚕时，新单元默认就用这只蚕的数据（单蚕一格）
    const worms = habitat.agents.filter(a => a.kind === 'route' && a.wormId != null);
    const soleWorm = worms.length === 1 ? worms[0].wormId : null;
    return {
      id: 'wv-' + (habitat.agents.filter(a => a.kind === 'weave').length + 1),
      kind: 'weave',
      mode: 'idle',
      bodyVisible: true,
      x: x, y: y,
      w: 200, h: 200,
      coverage: 0.55,
      scaleK: 0.9,
      measuredWorm: soleWorm,   // 这块单元用的是哪只蚕的实测数据（null = 用合并后的单条实测丝路）
      shape: 'island',
      worms: 8,
      wallAff: 0.6,
      seed: s,
      tone: 0.62 + (s % 1000) / 1000 * 0.5,
      gap: 8,
      strata: 2,
      outline: null,
      u: 0,
      duration: 22,
      speedScale: 1,
      tileField: false,
      silk: [],
      heading: 0,
      walls: [],
      paths: [],
      custom: { walls: {}, paths: {}, shapes: {} },
      cache: null,
      sample: null,
    };
  }

  function addWeaveAgent() {
    const a = arenaSpec();
    const base = a.kind === 'circle' ? a.r : Math.min(a.hw, a.hh);
    const x = Math.round((Math.random() - 0.5) * base * 0.2);
    const y = Math.round((Math.random() - 0.5) * base * 0.2);
    pushUndo();
    const agent = makeWeaveAgent(x, y);
    agent.w = agent.h = Math.round(Math.min(260, Math.max(160, base * 1.25)));
    agent.u = 1;             // 手动放进去的块直接显示织好的样子，别给一个空格让人以为没放上
    buildWeave(agent);
    habitat.agents.push(agent);
    habitat.selected = agent.id;
    agent.flashUntil = (typeof performance !== 'undefined' ? performance.now() : Date.now()) + 1600;
    renderList();
    toast('已放入 1 块织网单元（' + agent.id + '，第 ' + habitat.agents.filter(x => x.kind === 'weave').length + ' 块）。画布上闪的那块就是它。', 'ok');
    hint('一个织网单元就是一格：放几个单元就有几块。格里的圆孔/缺口/壁/丝路都能用「开始编辑形状」+ 拖手柄改。');
  }

  // 按轮廓新建：点顶点 → 双击封闭 → 生成一个多边形单元
  function startOutlineUnit() {
    habitat.newOutline = [];
    hint('按轮廓新建：在画布上依次点外框顶点（凹多边形也行），双击封闭并生成单元；Esc 取消。');
  }

  function finishOutlineUnit() {
    const pts = (habitat.newOutline || []).slice();
    habitat.newOutline = null;
    if (pts.length < 3) { toast('外框至少 3 个顶点。', 'err'); hint('已取消轮廓绘制。'); return; }
    const cx = pts.reduce((s, p) => s + p.x, 0) / pts.length;
    const cy = pts.reduce((s, p) => s + p.y, 0) / pts.length;
    const local = pts.map(p => ({ x: p.x - cx, y: p.y - cy }));
    const hw = Math.max.apply(null, local.map(p => Math.abs(p.x)));
    const hh = Math.max.apply(null, local.map(p => Math.abs(p.y)));
    pushUndo();
    const agent = makeWeaveAgent(cx, cy);
    agent.w = Math.max(80, Math.min(340, Math.round(hw * 2)));
    agent.h = Math.max(80, Math.min(340, Math.round(hh * 2)));
    agent.outline = local;
    agent.shape = 'island';
    agent.u = 0;
    buildWeave(agent);
    habitat.agents.push(agent);
    habitat.selected = agent.id;
    renderList();
    toast('已按 ' + pts.length + ' 个顶点新建织网单元 ' + agent.id + '。', 'ok');
    hint('轮廓单元已经建好；点「开始」让蚕在轮廓里织，或进编辑继续拖顶点。');
  }

  // 铺块群：有上限的马赛克阵列（默认 6×6 网格里挑 ≤20 块，贴近参考图的块数与大小）
  function addWeaveMosaic() {
    const a = arenaSpec();
    const spanW = (a.kind === 'circle' ? a.r * 2 : a.hw * 2) * 0.98;
    const spanH = (a.kind === 'circle' ? a.r * 2 : a.hh * 2) * 0.98;
    const cols = 5, rows = 5;
    // 块的大小贴近参考图：单块约占场宽 1/4.5（参考图 1095px 宽、块≈245px）
    const tile = Math.max(48, Math.min(340, Math.round(Math.min(spanW / 4.6, spanH / 4.6))));
    const cap = 20;
    const existing = habitat.agents.filter(x => x.kind === 'weave').length;
    if (existing >= cap) { toast('织网单元已经有 ' + existing + ' 个（上限 ' + cap + '），先删几个再铺。', 'err'); return; }
    pushUndo();
    const cand = [];
    for (let j = 0; j < rows; j++) {
      for (let i = 0; i < cols; i++) {
        const x = (i - (cols - 1) / 2) * tile * 1.03;
        const y = (j - (rows - 1) / 2) * tile * 1.03;
        if (blocked(x, y)) continue;
        cand.push({ x, y, i, j });
      }
    }
    // 打乱后按 60% 左右占有率取块，总数量不超过上限
    for (let k = cand.length - 1; k > 0; k--) {
      const r = Math.floor(Math.random() * (k + 1));
      const tmp = cand[k]; cand[k] = cand[r]; cand[r] = tmp;
    }
    const want = Math.min(cap - existing, Math.max(9, Math.round(cand.length * 0.62)));
    cand.slice(0, want).forEach(pos => {
      // 块群不规则化：位置 ±4%、尺寸 ±5%、亮度随机（参考图里块边缘是轻微错位的）
      const jx = (Math.random() - 0.5) * tile * 0.08;
      const jy = (Math.random() - 0.5) * tile * 0.08;
      const sz = tile * (0.95 + Math.random() * 0.10);
      const agent = makeWeaveAgent(pos.x + jx, pos.y + jy);
      agent.w = agent.h = Math.round(sz);
      agent.gap = 8;
      agent.strata = 2;
      agent.worms = 6;
      agent.shape = Math.random() < 0.72 ? 'island' : 'notchIsland';
      agent.tone = 0.58 + Math.random() * 0.55;
      agent.u = 0;
      buildWeave(agent);
      habitat.agents.push(agent);
      habitat.selected = agent.id;
    });
    renderList();
    toast('已铺 ' + want + ' 块（' + cols + '×' + rows + ' 位阵里挑的，单元 ' + Math.round(tile) + 'px，上限 ' + cap + '）。', 'ok');
    hint('块群是有上限的：5×5 位阵里挑出约六成，块大小一致、形状随机带大圆孔；每块都能单独拖/改形状/改亮度。');
  }

  function drawWeave(ctx, agent, v) {
    const cw = Math.max(60, agent.w), ch = Math.max(60, agent.h);
    // 一个织网单元 = 一格（手动放多少就有多少块）；只有显式开启 tileField 才整场铺格
    const cells = agent.tileField ? weaveVisibleCells(agent, v) : [[0, 0]];
    const u = Math.max(0, Math.min(1, agent.u || 0));
    const seed = agent.seed >>> 0;
    ctx.save();
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    cells.forEach(([i, j]) => {
      const content = weaveCellContent(agent, i, j);
      if (!agent.tileField) content.blank = false;   // 手放的单元一定织满，不留空格
      const ox = agent.x + i * cw;
      const oy = agent.y + j * ch;
      const gap = Math.max(0, Number.isFinite(agent.gap) ? agent.gap : 6);
      const tone = Math.max(0.35, Math.min(1.25, Number.isFinite(agent.tone) ? agent.tone : 0.85));
      // 块缝：四边裁掉 gap 的黑边，参考图里块与块之间是硬黑缝
      ctx.save();
      ctx.beginPath();
      ctx.rect(v.px(ox - cw / 2 + gap / 2), v.py(oy - ch / 2 + gap / 2),
        Math.max(1, (cw - gap) * v.s), Math.max(1, (ch - gap) * v.s));
      ctx.clip();
      // 织块边界：不再描 SDF 轮廓线（那条等粗细圆环会被读成「画出来的圆圈」），
      // 块缝由 gap 裁切形成；多边形单元只描自己的外框
      ctx.globalCompositeOperation = 'source-over';
      if (!content.blank) {
        if (content.cell && content.cell.outline) {
          ctx.strokeStyle = 'rgba(206,216,210,0.22)';
          ctx.beginPath();
          content.cell.outline.forEach((q, k) => {
            const px = v.px(ox + q.x), py = v.py(oy + q.y);
            if (k === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
          });
          ctx.closePath();
          ctx.stroke();
        }
      }
      // 人工画的壁：只在“编辑这一格”时显示；画成圆滑曲线（不是折线），
      // 成品、导出的视频/图片/母版里都不出现
      const eShow = habitat.weaveEdit;
      const wallsVisible = !habitat.composing && eShow && eShow.agentId === agent.id;
      if (wallsVisible && content.customWalls && content.customWalls.length) {
        ctx.strokeStyle = 'rgba(236,242,238,0.62)';
        ctx.lineWidth = Math.max(1, 1.2 * v.s);
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        content.customWalls.forEach(line => {
          const src = line.pts || line;
          if (!src.length) return;
          // 顶点之间走二次贝塞尔（穿过两点的中点）：哪怕只点两下，也是弧线不是折线
          const path = src.slice();
          if (line.closed && path.length > 2) path.push(path[0]);
          ctx.beginPath();
          const P = (q) => ({ x: v.px(ox + q.x), y: v.py(oy + q.y) });
          const a0 = P(path[0]);
          ctx.moveTo(a0.x, a0.y);
          for (let k = 1; k < path.length - 1; k++) {
            const cur = P(path[k]);
            const nx = P(path[k + 1]);
            ctx.quadraticCurveTo(cur.x, cur.y, (cur.x + nx.x) / 2, (cur.y + nx.y) / 2);
          }
          const lastP = P(path[path.length - 1]);
          ctx.quadraticCurveTo(lastP.x, lastP.y, lastP.x, lastP.y);
          if (line.closed) ctx.closePath();
          ctx.stroke();
          // 顶点提示（编辑态才有的小点，告诉你右键可以删）
          if (eShow) {
            ctx.fillStyle = 'rgba(236,242,238,0.5)';
            src.forEach(q => {
              ctx.fillRect(v.px(ox + q.x) - 1.5, v.py(oy + q.y) - 1.5, 3, 3);
            });
          }
        });
      }
      if (agent.bodyVisible === false) { ctx.restore(); return; }
      const delay = weaveHash01(i, j, seed) * 0.18;
      const lu = Math.max(0, Math.min(1, (u - delay) / (1 - delay || 1)));
      if (lu <= 0) { ctx.restore(); return; }
      const light = Math.max(0.16, Math.min(0.86, (0.30 + weaveHash01(i, j, seed + 101) * 0.30) * tone));
      ctx.globalCompositeOperation = 'lighter';
      const strata = Math.max(1, Math.min(3, Math.round(agent.strata || 1)));
      if (lu >= 0.995) {
        // 已织满的块用离屏位图（每帧不再重画上万点）
        const img = weaveRasterFor(agent, content, cw, ch, light, tone, strata);
        ctx.drawImage(img, v.px(ox - cw / 2), v.py(oy - ch / 2), cw * v.s, ch * v.s);
        ctx.restore();
        return;
      }
      const baseW = Math.max(0.8, 1.15 * Math.max(1, v.s * 0.6));
      // 按丝的实际长度顺序推进：蚕是一根一根往前织，不是整块同时长
      const cum = weavePathCum(content);
      const target = lu * cum.total;
      let headPt = null;
      // 柔雾只铺一遍（全量，不做位移），负责丝层的空气感
      ctx.lineWidth = baseW * 3.2;
      content.paths.forEach((p, idx) => {
        const start = cum.acc[idx];
        if (start >= target) return;
        ctx.strokeStyle = 'rgba(226,232,228,' + Math.max(0.03, Math.min(0.09, light * 0.07)).toFixed(2) + ')';
        ctx.beginPath();
        for (let k = 0; k < p.pts.length; k++) {
          const px = v.px(ox + p.pts[k].x), py = v.py(oy + p.pts[k].y);
          if (k === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
        }
        ctx.stroke();
      });
      // 分层：按带序号分给不同层，每层丝线集合不同、只有亚像素级错位
      // （不再把同一套线整层平移复制，避免"两层一样的图叠在一起"的鬼影）
      for (let L = 0; L < strata; L++) {
        const off = (L - (strata - 1) / 2) * cw * 0.006;
        const lTone = 1 - L * 0.12;
        ctx.lineWidth = baseW * (1 - L * 0.08);
        content.paths.forEach((p, idx) => {
          if ((p.b != null ? p.b : idx) % strata !== L) return;
          const start = cum.acc[idx];
          if (start >= target) return;
          const frac = Math.min(1, (target - start) / (cum.seg[idx] || 1));
          const n = Math.max(2, Math.floor(p.pts.length * frac));
          const alpha = Math.max(0.12, Math.min(0.95, (p.a != null ? p.a : 0.4) * (light / 0.42) * lTone * 0.82));
          ctx.strokeStyle = 'rgba(226,232,228,' + alpha.toFixed(2) + ')';
          ctx.beginPath();
          for (let k = 0; k < n; k++) {
            const px = v.px(ox + p.pts[k].x + off), py = v.py(oy + p.pts[k].y + off);
            if (k === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
          }
          ctx.stroke();
          if (L === strata - 1) headPt = p.pts[Math.min(p.pts.length - 1, Math.max(0, n - 1))];
        });
      }
      // 吐丝头：沿已织出的丝往前跑，让"蚕正在爬"看得见
      if (headPt) {
        const sx = v.px(ox + headPt.x), sy = v.py(oy + headPt.y);
        ctx.globalCompositeOperation = 'source-over';
        ctx.fillStyle = 'rgba(240,245,242,0.9)';
        ctx.beginPath();
        ctx.arc(sx, sy, Math.max(2, 2.2 * v.s * 0.6), 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.restore();
    });
    ctx.restore();
  }

  // 撞壁收口：把越界的点沿最短方向贴到壁上（丝碰到壁就停在这里），
  // 让每一条丝的"尽头"落在壁面上，孔口附近的密度就是这样一点点堆出来的
  function weaveWallProject(cell, x, y, pad) {
    const p = pad || 1.6;
    let best = null;
    const keep = (nx, ny, d) => {
      if (!Number.isFinite(nx) || !Number.isFinite(ny)) return;
      if (!best || d < best.d) best = { x: nx, y: ny, d };
    };
    const islands = cell.islands || (cell.island ? [cell.island] : []);
    islands.forEach(isl => {
      const dx = x - isl.cx, dy = y - isl.cy;
      const d = Math.hypot(dx, dy) || 1e-6;
      if (d < isl.r + p) {
        const rr = isl.r + p + 0.6;
        keep(isl.cx + dx / d * rr, isl.cy + dy / d * rr, Math.abs(isl.r + p - d));
      }
    });
    if (cell.notch) {
      const dx = x - cell.notch.cx, dy = y - cell.notch.cy;
      const d = Math.hypot(dx, dy) || 1e-6;
      if (d < cell.notch.r + p) {
        const rr = cell.notch.r + p + 0.6;
        keep(cell.notch.cx + dx / d * rr, cell.notch.cy + dy / d * rr, Math.abs(cell.notch.r + p - d));
      }
    }
    // 手画的缺口（闭合多边形）：把点推到多边形外面，最近的那条边上
    if (Array.isArray(cell.notchPts) && cell.notchPts.length >= 3) {
      const pts = weaveNotchCurve(cell.notchPts);
      const inside = weaveInPoly(pts, x, y);
      const d = weavePolyDist(pts, x, y);
      if (inside || d < p) {
        let bx = x, by = y, bd = Infinity;
        for (let i = 0, n = pts.length; i < n; i++) {
          const q0 = pts[i], q1 = pts[(i + 1) % n];
          const ex = q1.x - q0.x, ey = q1.y - q0.y;
          const L2 = ex * ex + ey * ey || 1;
          let t = ((x - q0.x) * ex + (y - q0.y) * ey) / L2;
          t = Math.max(0, Math.min(1, t));
          const cx1 = q0.x + ex * t, cy1 = q0.y + ey * t;
          const dd = Math.hypot(x - cx1, y - cy1);
          if (dd < bd) { bd = dd; bx = cx1; by = cy1; }
        }
        let nx = x - bx, ny = y - by;
        const L = Math.hypot(nx, ny) || 1e-6;
        nx /= L; ny /= L;
        if (inside) { nx = -nx; ny = -ny; }
        keep(bx + nx * (p + 0.6), by + ny * (p + 0.6), bd);
      }
    }
    const hw = cell.w / 2 - p, hh = cell.h / 2 - p;
    if (Math.abs(x) > hw) keep(Math.sign(x) * hw, y, Math.abs(x) - hw);
    if (Math.abs(y) > hh) keep(x, Math.sign(y) * hh, Math.abs(y) - hh);
    return best ? { x: best.x, y: best.y } : null;
  }

  // 撞壁法线：越界点若是掉进圆孔/缺口，返回孔心指向该点的单位法线 + 壁面接触点
  function weaveWallNormal(cell, x, y) {
    let best = null;
    const test = (cx0, cy0, r) => {
      const dx = x - cx0, dy = y - cy0;
      const d = Math.hypot(dx, dy) || 1e-6;
      if (d >= r + 2) return;
      const gap = r + 2 - d;
      if (!best || gap > best.gap) {
        best = { nx: dx / d, ny: dy / d, cx: cx0 + (dx / d) * (r + 2), cy: cy0 + (dy / d) * (r + 2), gap,
          ccx: cx0, ccy: cy0, r };
      }
    };
    const islands = cell.islands || (cell.island ? [cell.island] : []);
    islands.forEach(isl => test(isl.cx, isl.cy, isl.r));
    if (cell.notch) test(cell.notch.cx, cell.notch.cy, cell.notch.r);
    if (Array.isArray(cell.notchPts) && cell.notchPts.length >= 3) {
      const pts = weaveNotchCurve(cell.notchPts);
      const inside = weaveInPoly(pts, x, y);
      const d = weavePolyDist(pts, x, y);
      if (inside || d < 6) {
        let bx = x, by = y, bd = Infinity;
        for (let i = 0, n = pts.length; i < n; i++) {
          const q0 = pts[i], q1 = pts[(i + 1) % n];
          const ex = q1.x - q0.x, ey = q1.y - q0.y;
          const L2 = ex * ex + ey * ey || 1;
          let t = ((x - q0.x) * ex + (y - q0.y) * ey) / L2;
          t = Math.max(0, Math.min(1, t));
          const cx1 = q0.x + ex * t, cy1 = q0.y + ey * t;
          const dd = Math.hypot(x - cx1, y - cy1);
          if (dd < bd) { bd = dd; bx = cx1; by = cy1; }
        }
        let nx = x - bx, ny = y - by;
        const L = Math.hypot(nx, ny) || 1e-6;
        nx /= L; ny /= L;
        if (inside) { nx = -nx; ny = -ny; }
        const gap = Math.max(0, 6 - bd);
        if (!best || gap > best.gap) {
          best = { nx, ny, cx: bx + nx * 2, cy: by + ny * 2, gap, ccx: bx, ccy: by, r: 0 };
        }
      }
    }
    if (!best) return null;
    return { x: best.nx, y: best.ny, cx: best.cx, cy: best.cy, ccx: best.ccx, ccy: best.ccy, r: best.r };
  }

  // 每条丝的长度与前缀和（按实际折线长度推进用）
  function weavePathCum(content) {    if (content.cum) return content.cum;
    const acc = [], seg = [];
    let total = 0;
    content.paths.forEach(p => {
      acc.push(total);
      let len = 0;
      for (let k = 1; k < p.pts.length; k++) {
        len += Math.hypot(p.pts[k].x - p.pts[k - 1].x, p.pts[k].y - p.pts[k - 1].y);
      }
      seg.push(len);
      total += len;
    });
    content.cum = { acc, seg, total: total || 1 };
    return content.cum;
  }

  // 已织满的块缓存成离屏位图；tone / 分层变了就重画
  function weaveRasterFor(agent, content, cw, ch, light, tone, strata) {
    const layers = Math.max(1, Math.min(3, Math.round(strata || 1)));
    const key = (agent.seed >>> 0) + '|' + Math.round(cw) + 'x' + Math.round(ch) + '|' + tone.toFixed(2) + '|' + layers;
    if (content.raster && content.rasterKey === key) return content.raster;
    const W = 512;
    const H = Math.max(64, Math.round(512 * ch / cw));
    const cv = document.createElement('canvas');
    cv.width = W;
    cv.height = H;
    const g = cv.getContext('2d');
    g.fillStyle = 'rgba(0,0,0,0)';
    g.clearRect(0, 0, W, H);
    g.lineCap = 'round';
    g.lineJoin = 'round';
    g.globalCompositeOperation = 'lighter';
    const kx = W / cw, ky = H / ch;
    const baseW = Math.max(0.9, 1.15 * Math.max(1, kx * 0.34));
    // 柔雾一遍（全量，不位移）
    g.lineWidth = baseW * 3.2;
    content.paths.forEach(p => {
      g.strokeStyle = 'rgba(226,232,228,' + Math.max(0.03, Math.min(0.09, light * 0.07)).toFixed(2) + ')';
      g.beginPath();
      for (let k = 0; k < p.pts.length; k++) {
        const q = p.pts[k];
        const X = (q.x + cw / 2) * kx, Y = (q.y + ch / 2) * ky;
        if (k === 0) g.moveTo(X, Y); else g.lineTo(X, Y);
      }
      g.stroke();
    });
    // 分层按带序号分集合，亚像素错位（不做整层复制）
    for (let L = 0; L < layers; L++) {
      const off = (L - (layers - 1) / 2) * cw * 0.006;
      const lTone = 1 - L * 0.12;
      g.lineWidth = baseW * (1 - L * 0.08);
      content.paths.forEach((p, idx) => {
        if ((p.b != null ? p.b : idx) % layers !== L) return;
        const alpha = Math.max(0.12, Math.min(0.95, (p.a != null ? p.a : 0.4) * (light / 0.42) * lTone * 0.82));
        g.strokeStyle = 'rgba(226,232,228,' + alpha.toFixed(2) + ')';
        g.beginPath();
        for (let k = 0; k < p.pts.length; k++) {
          const q = p.pts[k];
          const X = (q.x + off + cw / 2) * kx, Y = (q.y + off + ch / 2) * ky;
          if (k === 0) g.moveTo(X, Y); else g.lineTo(X, Y);
        }
        g.stroke();
      });
    }
    content.raster = cv;
    content.rasterKey = key;
    return cv;
  }

  function weaveVisibleCells(agent, v) {
    const cw = Math.max(60, agent.w), ch = Math.max(60, agent.h);
    const wx0 = (0 - v.cx) / v.s - agent.x;
    const wx1 = (v.w - v.cx) / v.s - agent.x;
    const wy0 = (0 - v.cy) / v.s - agent.y;
    const wy1 = (v.h - v.cy) / v.s - agent.y;
    let i0 = Math.floor(wx0 / cw) - 1, i1 = Math.floor(wx1 / cw) + 1;
    let j0 = Math.floor(wy0 / ch) - 1, j1 = Math.floor(wy1 / ch) + 1;
    if (i1 - i0 > 16) i1 = i0 + 16;
    if (j1 - j0 > 16) j1 = j0 + 16;
    const cells = [];
    for (let j = j0; j <= j1; j++) for (let i = i0; i <= i1; i++) cells.push([i, j]);
    return cells;
  }

  let toastTimer = 0;
  function toast(msg, kind) {
    const el = document.getElementById('habToast');
    if (!el) return;
    el.textContent = msg;
    el.className = 'show' + (kind ? ' ' + kind : '');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { el.className = ''; }, 2600);
  }

  function hint(msg) {
    const el = document.getElementById('habHint');
    if (el) el.textContent = msg;
  }

  const ghost = document.getElementById('habGhost');

  function drive() {
    const t = habitat.tempC;
    const h = habitat.humidity / 100;
    const tempDelta = t - 25;
    const speed = 22 * (1 + tempDelta * 0.035) * (0.72 + h * 0.45);
    const sway = 0.55 + Math.abs(tempDelta) * 0.03 + (1 - h) * 0.65;
    const pauseChance = Math.min(0.35, Math.abs(tempDelta) * 0.012 + (h < 0.45 ? 0.08 : 0));
    const silkAlpha = 0.22 + h * 0.18;
    return { speed, sway, pauseChance, silkAlpha, version: MODEL };
  }

  function pushUndo() {
    habitat.undo.push(JSON.stringify({
      agents: habitat.agents,
      orphans: habitat.orphans,
      obstacles: habitat.obstacles,
    }));
    if (habitat.undo.length > 24) habitat.undo.shift();
    habitat.redo = [];        // 新的改动把"重做"清掉
    syncHistoryUI();
  }

  function snapshotNow() {
    return JSON.stringify({
      agents: habitat.agents,
      orphans: habitat.orphans,
      obstacles: habitat.obstacles,
    });
  }

  function restoreSnapshot(json) {
    const data = JSON.parse(json);
    habitat.agents = data.agents || [];
    habitat.orphans = data.orphans || [];
    habitat.obstacles = data.obstacles || [];
    habitat.selected = null;
    habitat.weaveEdit = null;
    habitat.drag = null;
    habitat.newOutline = null;
    habitat.agents.forEach(a => {
      if (a.kind === 'weave') { a.cache = null; buildWeave(a); }
      if (a.kind === 'route') applyRouteTransform(a);
    });
    renderList();
    syncHistoryUI();
  }

  function undoStep() {
    if (!habitat.undo.length) { toast('没有可撤销的改动。', 'err'); return false; }
    habitat.redo.push(snapshotNow());
    if (habitat.redo.length > 24) habitat.redo.shift();
    restoreSnapshot(habitat.undo.pop());
    toast('已撤销一步（还能重做 ' + habitat.redo.length + ' 步）。', 'ok');
    return true;
  }

  function redoStep() {
    if (!habitat.redo.length) { toast('没有可重做的改动。', 'err'); return false; }
    habitat.undo.push(snapshotNow());
    if (habitat.undo.length > 24) habitat.undo.shift();
    restoreSnapshot(habitat.redo.pop());
    toast('已重做一步（还能撤销 ' + habitat.undo.length + ' 步）。', 'ok');
    return true;
  }

  function syncHistoryUI() {
    const u = document.getElementById('habUndo');
    const r = document.getElementById('habRedo');
    if (u) u.textContent = '撤销（Ctrl+Z）' + (habitat.undo.length ? ' · ' + habitat.undo.length : '');
    if (r) r.textContent = '重做（Ctrl+Shift+Z）' + (habitat.redo.length ? ' · ' + habitat.redo.length : '');
    if (u) u.disabled = !habitat.undo.length;
    if (r) r.disabled = !habitat.redo.length;
  }

  function makeRandomDemo() {
    const n = habitat.agents.filter(a => a.kind === 'random').length + 1;
    habitat.agents.push({
      id: 'sw-' + n,
      kind: 'random',
      wormId: null,
      mode: 'bench',
      bodyVisible: true,
      x: 0, y: 0, heading: -Math.PI / 2,
      silk: [],
      phase: n * 1.7,
      turnSign: n % 2 ? 1 : -1,
      pauseUntil: 0,
      speedScale: 1,
    });
  }

  function normalizeRoute(raw) {
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    raw.forEach(p => {
      minX = Math.min(minX, p.x); minY = Math.min(minY, p.y);
      maxX = Math.max(maxX, p.x); maxY = Math.max(maxY, p.y);
    });
    const span = Math.max(maxX - minX, maxY - minY) || 1;
    const s = 110 / span;
    const cx = (minX + maxX) / 2, cy = (minY + maxY) / 2;
    return raw.map(p => ({ x: (p.x - cx) * s, y: (p.y - cy) * s }));
  }

  function transformRoute(agent) {
    const cs = Math.cos(agent.rot || 0);
    const sn = Math.sin(agent.rot || 0);
    const sc = agent.scale || 1;
    return agent.route.map(p => {
      const lx = p.x * sc, ly = p.y * sc;
      return {
        x: lx * cs - ly * sn + (agent.offX || 0),
        y: lx * sn + ly * cs + (agent.offY || 0),
      };
    });
  }

  function applyRouteTransform(agent) {
    const pts = transformRoute(agent);
    agent.routeWorld = pts;
    agent.silk = pts.slice().reverse();
    if (!pts.length) {
      // 这只蚕还没有轨迹（例如刚建格、还没导入实测数据）：先停在落点上，不报错
      agent.x = agent.offX || 0;
      agent.y = agent.offY || 0;
      return;
    }
    const h = pts[0];
    agent.x = h.x;
    agent.y = h.y;
    const n = pts[Math.min(1, pts.length - 1)];
    agent.heading = Math.atan2(n.y - h.y, n.x - h.x);
  }

  function sampleRoute(agent, u) {
    const pts = agent.routeWorld || agent.silk;
    if (!pts.length) return { x: agent.x, y: agent.y };
    const f = Math.max(0, Math.min(1, u)) * (pts.length - 1);
    const i = Math.floor(f);
    const t = f - i;
    const a = pts[i];
    const b = pts[Math.min(pts.length - 1, i + 1)];
    return { x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t };
  }

  // 局部实测笔迹（以蚕自身为原点，不含场地偏移）
  function sampleRouteCentered(agent, u) {
    const pts = agent.route || [];
    if (pts.length < 2) return { x: 0, y: 0 };
    const f = Math.max(0, Math.min(1, u)) * (pts.length - 1);
    const i = Math.floor(f);
    const t = f - i;
    const a = pts[i];
    const b = pts[Math.min(pts.length - 1, i + 1)];
    return { x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t };
  }

  // 蚕归属的织网单元：优先记住的那块，没记住就取最近的一块
  function weaveUnitFor(agent) {
    const units = habitat.agents.filter(u => u.kind === 'weave');
    if (!units.length) return null;
    let unit = units.find(u => u.id === agent.homeUnitId);
    if (unit) return unit;
    let best = null, bd = Infinity;
    units.forEach(u => {
      const d = Math.hypot(u.x - agent.x, u.y - agent.y);
      if (d < bd) { bd = d; best = u; }
    });
    if (best) agent.homeUnitId = best.id;
    return best;
  }

  // 场地巡游轨迹：让蚕把实测笔迹一遍遍铺到整个场地上（方向是合成的，局部形态是实测的）
  function roamPoint(agent, t) {
    const ph = (agent.wormId || 1) * 1.7 + (agent.homePhase || agent.phase || 0);
    // 单个单元格内活动：把巡游中心绑到所属的织网单元，半径收在格内
    if (agent.scope === 'cell') {
      const unit = weaveUnitFor(agent);
      if (unit) {
        const r = Math.min(unit.w, unit.h) * 0.15;
        // 两条频率不整除的正弦叠一点慢漂移：同一格里也不会踩出规则的一排
        const drift = Math.sin(t * 0.27 + ph * 1.7) * r * 0.45;
        return {
          x: unit.x + Math.cos(t * 1.55 + ph) * r + drift,
          y: unit.y + Math.sin(t * 1.22 + ph * 1.3) * r * 0.9 + Math.cos(t * 0.19 + ph) * r * 0.35,
        };
      }
      // 还没放织网单元就先按整场跑，放了再自动收进格内
    }
    const a = arenaSpec();
    const span = a.kind === 'circle' ? a.r : Math.min(a.hw, a.hh);
    const rr = span * (0.20 + 0.62 * (0.5 + 0.5 * Math.sin(t * 1.45 + ph)));
    const ang = t * 2.05 + ph;
    return {
      x: Math.cos(ang) * rr * 0.92,
      y: Math.sin(ang * 0.87 + 0.4) * rr * 0.86,
    };
  }

  /* 一只"蚕衣"是一种蚕：同一只蚕的数据可以同时用在很多格里，各自生成一个实例，
     互不抢占；实例从格子里的随机点位（或你拖放的点位）起步。 */
  function spawnCellWorm(unit, wid, x, y) {
    const primary = habitat.agents.find(a => a.kind === 'route' && a.wormId === wid && a.id === 'rt-' + wid)
      || habitat.agents.find(a => a.kind === 'route' && a.wormId === wid);
    const id = 'rt-' + wid + '@' + unit.id;
    let a = habitat.agents.find(z => z.id === id);
    if (!a) {
      a = {
        id: id, kind: 'route', wormId: wid,
        color: primary ? primary.color : '#d4c8b0',
        mode: 'idle', bodyVisible: true,
        route: primary && primary.route ? primary.route.slice() : [],
        offX: 0, offY: 0, rot: 0, scale: 1, follow: false, u: 0, phase: 0,
        turnSign: 1, pauseUntil: 0, speedScale: 1, silk: [],
        scope: 'cell', homeUnitId: unit.id, x: 0, y: 0, heading: 0,
      };
      habitat.agents.push(a);
    } else {
      if (primary && primary.route && primary.route.length) a.route = primary.route.slice();
      a.homeUnitId = unit.id;
      a.scope = 'cell';
    }
    // 起点：优先用你拖放的点位，否则在格子里随机落一处（不排队、不横排）
    const mx = unit.w * 0.34, my = unit.h * 0.34;
    a.offX = Number.isFinite(x) ? x : unit.x + (Math.random() * 2 - 1) * mx;
    a.offY = Number.isFinite(y) ? y : unit.y + (Math.random() * 2 - 1) * my;
    // 每只实例的朝向/大小/巡游相位都随机：不会排成一行一样的八字
    a.rot = (Math.random() * 2 - 1) * 0.85;
    a.scale = 0.78 + Math.random() * 0.28;
    a.phase = Math.random() * Math.PI * 2;
    a.turnSign = Math.random() < 0.5 ? 1 : -1;
    a.homePhase = Math.random() * Math.PI * 2;
    a.travel = 0;
    a.mode = 'idle';
    applyRouteTransform(a);
    a.silk = [];
    return a;
  }

  function measuredSource() {
    const pushed = window.__previewTrajs;
    if (Array.isArray(pushed) && pushed.length) return pushed;
    try {
      const payload = buildPreviewPayload();
      if (payload && Array.isArray(payload.trajectories) && payload.trajectories.length) return payload.trajectories;
    } catch (_) { /* 描图器还没数据 */ }
    return [];
  }

  function syncMeasured() {
    const srcs = measuredSource();
    const valid = srcs.map((t, i) => ({
      t, i,
      raw: (t.points || []).filter(p => p && Number.isFinite(p.x) && Number.isFinite(p.y)),
    })).filter(x => x.raw.length >= 2);
    const seen = new Set();
    valid.forEach(({ t, i, raw }, order) => {
      const wid = t.wormId != null ? t.wormId : i + 1;
      seen.add(wid);
      const route = normalizeRoute(raw);
      const existing = habitat.agents.find(a => a.kind === 'route' && a.wormId === wid && a.id === 'rt-' + wid);
      if (existing) {
        existing.route = route;
        existing.color = t.color || existing.color;
        const wasCell = existing.homeUnitId;
        applyRouteTransform(existing);
        if (wasCell) existing.silk = [];
        if (existing.mode === 'bench' || existing.mode === 'drag') existing.mode = 'idle';
      } else {
        const agent = {
          id: 'rt-' + wid,
          kind: 'route',
          wormId: wid,
          color: t.color || '#d4c4a8',
          mode: 'idle',
          bodyVisible: true,
          route: route,
          offX: (order - (valid.length - 1) / 2) * 26,
          offY: 0,
          rot: 0,
          scale: 1,
          follow: false,
          u: 0,
          phase: 0,
          turnSign: 1,
          pauseUntil: 0,
          speedScale: 1,
          silk: [],
          // 默认收进单元格：场地里已经有织网单元时，蚕就在格里爬，不会满场画巨型八字
          scope: habitat.agents.some(u => u.kind === 'weave') ? 'cell' : 'field',
          homeUnitId: null,
          x: 0, y: 0, heading: 0,
        };
        applyRouteTransform(agent);
        habitat.agents.push(agent);
      }
      // 各格里"同一种蚕"的实例也跟着换新数据（它们共用同一份实测点）
      habitat.agents.forEach(a => {
        if (a.kind === 'route' && a.wormId === wid && a.id !== 'rt-' + wid) {
          a.route = route;
          applyRouteTransform(a);
          if (a.homeUnitId) a.silk = [];
        }
      });
    });
    // 只清理没有数据的"源头蚕"，格内实例（id 带 @）一律留着
    habitat.agents = habitat.agents.filter(a =>
      a.kind !== 'route' || seen.has(a.wormId) || a.id.indexOf('@') > 0);
    renderList();
    syncRoutePanel();
    return valid.length;
  }

  /* 点列文件（trajectories.json / curves3d）→ 场地里的实测蚕；返回新增/更新的蚕数 */
  function importPointCloudDoc(doc) {
    const strokes = [];
    if (Array.isArray(doc.curves3d)) {
      doc.curves3d.forEach(c => {
        if (c && Array.isArray(c.points) && c.points.length >= 2) strokes.push({ wormId: c.wormId, pts: c.points });
      });
    }
    if (!strokes.length && Array.isArray(doc.trajectories)) {
      doc.trajectories.forEach((t, i) => {
        if (t && Array.isArray(t.points) && t.points.length >= 2) strokes.push({ wormId: t.wormId != null ? t.wormId : i + 1, pts: t.points });
      });
    }
    if (!strokes.length) return 0;
    pushUndo();
    const byWorm = new Map();
    strokes.forEach(st => {
      const pts = st.pts
        .map(p => ({ x: Number.isFinite(p.x_mm) ? p.x_mm : p.x, y: Number.isFinite(p.y_mm) ? p.y_mm : p.y }))
        .filter(p => Number.isFinite(p.x) && Number.isFinite(p.y));
      if (pts.length < 2) return;
      const wid = st.wormId != null ? st.wormId : 1;
      if (!byWorm.has(wid)) byWorm.set(wid, []);
      byWorm.get(wid).push(...pts);     // 同一只蚕的多笔按顺序接成一条丝路
    });
    let added = 0;
    byWorm.forEach((pts, wid) => {
      const route = normalizeRoute(pts);
      const existing = habitat.agents.find(x => x.kind === 'route' && x.wormId === wid);
      if (existing) { existing.route = route; applyRouteTransform(existing); }
      else {
        const agent = {
          id: 'rt-' + wid, kind: 'route', wormId: wid, color: '#d4c8b0', mode: 'idle',
          bodyVisible: true, route: route, offX: 0, offY: 0, rot: 0, scale: 1,
          follow: false, u: 0, phase: 0, turnSign: 1, pauseUntil: 0, speedScale: 1,
          silk: [], scope: 'cell', homeUnitId: null, x: 0, y: 0, heading: 0,
        };
        applyRouteTransform(agent);
        habitat.agents.push(agent);
      }
      added++;
    });
    habitat.agents.forEach(a => { if (a.kind === 'weave') { a.cache = null; buildWeave(a); } });
    renderList();
    return added;
  }

  function importMeasuredTrajectories() {
    const n = syncMeasured();
    if (!n) toast('还没描好的实测轨迹：先在上方描线，再回到这里。', 'err');
    else toast('已同步 ' + n + ' 条实测轨迹到场地。', 'ok');
  }

  /* ===== 描图器 → 蚕室 自动同步 =====
     上面描完/改完，下面的蚕不用点按钮就跟着换；用"数据指纹"轮询，避免反复重建。 */
  let lastMeasuredSig = null;
  function measuredSignature() {
    const srcs = measuredSource();
    if (!srcs.length) return '';
    return srcs.map(t => (t.wormId != null ? t.wormId : '?') + ':' + ((t.points || []).length)).join('|');
  }
  function autoSyncMeasured(force) {
    if (!document.getElementById('habWorldWrap')) return;
    const sig = measuredSignature();
    if (!sig || (!force && sig === lastMeasuredSig)) return;
    const changed = lastMeasuredSig !== null && sig !== lastMeasuredSig;
    lastMeasuredSig = sig;
    const n = syncMeasured();
    if (!n) return;
    const stat = document.getElementById('habSyncStat');
    if (stat) {
      stat.textContent = '实测 ' + n + ' 只 · 演示 ' +
        habitat.agents.filter(a => a.kind === 'random').length + ' 只';
    }
    if (changed) hint('描图器里的 ' + n + ' 条实测轨迹已自动同步到场地——下面那只蚕就是它。');
  }
  setInterval(() => autoSyncMeasured(false), 1200);

  const bg = document.getElementById('habBg');
  const far = document.getElementById('habLeaves');
  const mist = document.getElementById('habMist');
  const world = document.getElementById('habWorld');
  const depth = document.getElementById('habDepth');
  const wrap = document.getElementById('habWorldWrap');

  function fit(canvas, scale) {
    const r = wrap.getBoundingClientRect();
    const w = Math.max(2, Math.floor(r.width * (scale || 1)));
    const h = Math.max(2, Math.floor(r.height * (scale || 1)));
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
    }
    return { w, h, cssW: r.width, cssH: r.height };
  }

  function view() {
    const w = world.width, h = world.height;
    const a = arenaSpec();
    const span = a.kind === 'circle' ? a.r * 2 : Math.max(a.hw, a.hh) * 2;
    const baseScale = Math.min(w, h) / (span * 1.35);
    const s = baseScale * habViewport.zoom;
    const cx = w / 2 + habViewport.panX;
    const cy = h / 2 + habViewport.panY;
    return {
      w, h, s, cx, cy,
      px: x => cx + x * s,
      py: y => cy + y * s,
    };
  }

  function screenToHab(ev) {
    const rect = world.getBoundingClientRect();
    const sx = (ev.clientX - rect.left) * (world.width / rect.width);
    const sy = (ev.clientY - rect.top) * (world.height / rect.height);
    const v = view();
    return { x: (sx - v.cx) / v.s, y: (sy - v.cy) / v.s, sx, sy };
  }

  function updateHabZoomLabel() {
    const el = document.getElementById('habZoomLabel');
    if (el) el.textContent = Math.round(habViewport.zoom * 100) + '%';
  }

  function zoomAt(sx, sy, factor) {
    if (!world.width || !world.height) return;
    const before = view();
    const wx = (sx - before.cx) / before.s;
    const wy = (sy - before.cy) / before.s;
    habViewport.zoom = Math.max(0.12, Math.min(8, habViewport.zoom * factor));
    const after = view();
    habViewport.panX += sx - (after.cx + wx * after.s);
    habViewport.panY += sy - (after.cy + wy * after.s);
    updateHabZoomLabel();
  }

  function resetHabView() {
    habViewport.zoom = 1;
    habViewport.panX = 0;
    habViewport.panY = 0;
    updateHabZoomLabel();
  }

  function drawLeaf(ctx, x, y, rot, rx, ry, fill) {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(rot);
    ctx.beginPath();
    ctx.moveTo(0, -ry);
    ctx.bezierCurveTo(rx, -ry * 0.25, rx * 0.72, ry * 0.45, 0, ry);
    ctx.bezierCurveTo(-rx * 0.72, ry * 0.45, -rx, -ry * 0.25, 0, -ry);
    ctx.shadowColor = 'rgba(0,0,0,0.30)';
    ctx.shadowBlur = 7;
    ctx.shadowOffsetY = 2;

    ctx.fillStyle = fill;
    ctx.fill();

    ctx.shadowColor = 'transparent';
    ctx.shadowBlur = 0;
    ctx.shadowOffsetY = 0;
    ctx.beginPath();
    ctx.moveTo(0, -ry * 0.8);
    ctx.lineTo(0, ry * 0.75);
    ctx.strokeStyle = 'rgba(180,196,176,0.18)';
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.restore();
  }

  function drawBackdropLeaf(ctx, x, y, rot, rx, ry, opacity) {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(rot);
    ctx.globalAlpha = opacity;

    ctx.shadowColor = 'rgba(0,0,0,0.34)';
    ctx.shadowBlur = 18;

    ctx.beginPath();
    ctx.moveTo(0, -ry);
    ctx.bezierCurveTo(
      rx * 0.92, -ry * 0.28,
      rx * 0.72, ry * 0.48,
      0, ry
    );
    ctx.bezierCurveTo(
      -rx * 0.72, ry * 0.48,
      -rx * 0.92, -ry * 0.28,
      0, -ry
    );

    const grad = ctx.createLinearGradient(-rx, 0, rx, 0);
    grad.addColorStop(0, 'rgba(17,35,29,0.92)');
    grad.addColorStop(0.48, 'rgba(42,70,52,0.86)');
    grad.addColorStop(1, 'rgba(16,31,27,0.92)');

    ctx.fillStyle = grad;
    ctx.fill();

    ctx.shadowBlur = 0;
    ctx.strokeStyle = 'rgba(142,171,139,0.20)';
    ctx.lineWidth = 1;

    ctx.beginPath();
    ctx.moveTo(0, -ry * 0.88);
    ctx.quadraticCurveTo(0, 0, 0, ry * 0.88);
    ctx.stroke();

    for (let i = 0; i < 6; i++) {
      const t = -0.55 + i * 0.19;
      const yy = t * ry;
      const spread = rx * (0.28 + 0.28 * Math.cos(t * 1.35));
      const side = i % 2 ? -1 : 1;

      ctx.beginPath();
      ctx.moveTo(0, yy);
      ctx.quadraticCurveTo(
        side * spread * 0.48,
        yy - ry * 0.05,
        side * spread,
        yy - ry * 0.18
      );

      ctx.strokeStyle = 'rgba(160,184,148,0.12)';
      ctx.lineWidth = 0.8;
      ctx.stroke();
    }

    ctx.restore();
  }

  function paintStatic() {
    fit(bg, 1);
    fit(far, 1);

    const w = bg.width;
    const h = bg.height;
    const g = bg.getContext('2d');

    g.clearRect(0, 0, w, h);
    // 纯黑底（展陈参考：黑场 + 密织丝块）
    g.fillStyle = '#000000';
    g.fillRect(0, 0, w, h);

    const f = far.getContext('2d');
    f.clearRect(0, 0, w, h);
  }

  function paintMist() {
    // 展陈要求纯黑场：原低频柔光已去掉，只清屏
    const m = fit(mist, 0.22);
    const ctx = mist.getContext('2d');
    ctx.clearRect(0, 0, m.w, m.h);
  }

  function paintDepth() {
    const d = fit(depth, 1);
    const ctx = depth.getContext('2d');
    // 展陈要求纯黑场：前景叶片与环境光已删除，深度层只做清屏
    ctx.clearRect(0, 0, d.w, d.h);
  }

  function silkLook() {
    const mode = habitat.silkMode || 'silk';
    const width = Math.max(0.2, Math.min(3, Number.isFinite(habitat.silkWidth) ? habitat.silkWidth : 1));
    const gain = Math.max(0.2, Math.min(2.5, Number.isFinite(habitat.silkGain) ? habitat.silkGain : 1));
    if (mode === 'matte') return { width, gain, comp: 'source-over', rgb: '206,212,208' };
    if (mode === 'bright') return { width, gain, comp: 'lighter', rgb: '244,248,244' };
    if (mode === 'ink') return { width, gain, comp: 'source-over', rgb: '168,182,176' };
    return { width, gain, comp: 'lighter', rgb: '226,230,228' };
  }

  function drawSilk(ctx, pts, v, alpha) {
    if (!pts || pts.length < 2) return;
    const look = silkLook();
    ctx.save();
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.globalCompositeOperation = look.comp;
    ctx.strokeStyle = 'rgba(' + look.rgb + ',' + Math.max(0, Math.min(1, alpha * look.gain)) + ')';
    ctx.lineWidth = look.width;
    ctx.beginPath();
    ctx.moveTo(v.px(pts[0].x), v.py(pts[0].y));
    for (let i = 1; i < pts.length; i++) ctx.lineTo(v.px(pts[i].x), v.py(pts[i].y));
    ctx.stroke();
    ctx.restore();
  }

  function drawSilkInRect(ctx, pts, v, alpha, unit) {
    if (!unit || !pts || pts.length < 2) { drawSilk(ctx, pts, v, alpha); return; }
    const hw = unit.w / 2 * 0.98, hh = unit.h / 2 * 0.98;
    const clamped = pts.map(p => ({
      x: Math.max(unit.x - hw, Math.min(unit.x + hw, p.x)),
      y: Math.max(unit.y - hh, Math.min(unit.y + hh, p.y)),
    }));
    drawSilk(ctx, clamped, v, alpha);
  }

  function drawHabitatWorm(ctx, agent, v) {
    if (!agent.bodyVisible || agent.mode === 'bench') return;

    const sizeK = Math.max(0.4, Math.min(2.6,
      (Number.isFinite(habitat.wormSize) ? habitat.wormSize : 1) * (Number.isFinite(agent.scale) ? agent.scale : 1)));
    const bodyLen = 78 * sizeK;
    const pts = [{ x: agent.x, y: agent.y }];
    let acc = 0;

    for (let i = agent.silk.length - 1; i >= 0 && acc < bodyLen; i--) {
      const b = agent.silk[i];
      const a = pts[pts.length - 1];
      const seg = Math.hypot(b.x - a.x, b.y - a.y) * v.s;

      if (seg < 0.4) continue;

      if (acc + seg >= bodyLen) {
        const u = (bodyLen - acc) / seg;
        pts.push({
          x: a.x + (b.x - a.x) * u,
          y: a.y + (b.y - a.y) * u
        });
        acc = bodyLen;
      } else {
        pts.push(b);
        acc += seg;
      }
    }

    if (acc < bodyLen) {
      pts.push({
        x: agent.x - Math.cos(agent.heading) * ((bodyLen - acc) / v.s),
        y: agent.y - Math.sin(agent.heading) * ((bodyLen - acc) / v.s)
      });
    }

    const scr = pts.map(p => ({
      x: v.px(p.x),
      y: v.py(p.y)
    }));

    for (let i = 0; i < scr.length; i++) {
      const prev = scr[Math.max(0, i - 1)];
      const next = scr[Math.min(scr.length - 1, i + 1)];
      const t = safeUnit(next.x - prev.x, next.y - prev.y);

      scr[i].tx = t.x;
      scr[i].ty = t.y;
      scr[i].nx = -t.y;
      scr[i].ny = t.x;
    }

    for (let i = 1; i < scr.length; i++) {
      if (scr[i - 1].nx * scr[i].nx +
          scr[i - 1].ny * scr[i].ny < 0) {
        scr[i].nx *= -1;
        scr[i].ny *= -1;
      }
    }

    const maxHalf = 6.4 * sizeK;

    const widthAt = t => {
      if (t < 0.12) {
        const q = Math.max(0, Math.min(1, t / 0.12));
        return 0.40 + 0.42 * q * q * (3 - 2 * q);
      }
      if (t < 0.24) {
        const q = (t - 0.12) / 0.12;
        return 0.82 + 0.18 * q * q * (3 - 2 * q);
      }
      if (t < 0.78) {
        return 1 - 0.05 * ((t - 0.24) / 0.54);
      }
      if (t < 0.90) {
        const q = (t - 0.78) / 0.12;
        return 0.95 - 0.20 * q * q * (3 - 2 * q);
      }
      const q = (t - 0.90) / 0.10;
      return 0.75 - 0.70 * q * q * (3 - 2 * q);
    };

    const hw = i => widthAt(
      i / Math.max(1, scr.length - 1)
    ) * maxHalf;

    const left = [];
    const right = [];

    for (let i = 0; i < scr.length; i++) {
      left.push({
        x: scr[i].x + scr[i].nx * hw(i),
        y: scr[i].y + scr[i].ny * hw(i)
      });
      right.push({
        x: scr[i].x - scr[i].nx * hw(i),
        y: scr[i].y - scr[i].ny * hw(i)
      });
    }

    let minX = Infinity, minY = Infinity;
    let maxX = -Infinity, maxY = -Infinity;

    scr.forEach(p => {
      minX = Math.min(minX, p.x - maxHalf);
      minY = Math.min(minY, p.y - maxHalf);
      maxX = Math.max(maxX, p.x + maxHalf);
      maxY = Math.max(maxY, p.y + maxHalf);
    });

    ctx.save();
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';

    ctx.beginPath();
    ctx.moveTo(left[0].x, left[0].y);

    for (let i = 1; i < left.length; i++) {
      const a = left[i - 1];
      const b = left[i];
      ctx.quadraticCurveTo(
        a.x, a.y,
        (a.x + b.x) * 0.5,
        (a.y + b.y) * 0.5
      );
    }

    ctx.lineTo(left[left.length - 1].x, left[left.length - 1].y);
    ctx.lineTo(right[right.length - 1].x, right[right.length - 1].y);

    for (let i = right.length - 1; i > 0; i--) {
      const a = right[i];
      const b = right[i - 1];
      ctx.quadraticCurveTo(
        a.x, a.y,
        (a.x + b.x) * 0.5,
        (a.y + b.y) * 0.5
      );
    }

    ctx.lineTo(right[0].x, right[0].y);
    ctx.closePath();

    const bodyGrad = ctx.createLinearGradient(
      minX, minY, maxX, maxY
    );
    bodyGrad.addColorStop(0, '#fffdf6');
    bodyGrad.addColorStop(0.26, '#f2f0e8');
    bodyGrad.addColorStop(0.62, '#e6e3d9');
    bodyGrad.addColorStop(1, '#c7c3b9');

    ctx.save();

    ctx.shadowColor = 'rgba(0,0,0,0.34)';
    ctx.shadowBlur = 5;
    ctx.shadowOffsetX = 0;
    ctx.shadowOffsetY = 2;

    ctx.fillStyle = bodyGrad;
    ctx.fill();

    ctx.restore();

    ctx.strokeStyle = 'rgba(126,122,113,0.30)';
    ctx.lineWidth = 0.68;
    ctx.stroke();

    ctx.save();
    ctx.clip();

    ctx.strokeStyle = 'rgba(255,255,250,0.46)';
    ctx.lineWidth = maxHalf * 0.40;
    ctx.beginPath();
    ctx.moveTo(scr[0].x, scr[0].y);

    for (let i = 1; i < scr.length; i++) {
      const a = scr[i - 1];
      const b = scr[i];
      ctx.quadraticCurveTo(
        a.x, a.y,
        (a.x + b.x) * 0.5,
        (a.y + b.y) * 0.5
      );
    }
    ctx.stroke();

    const ringTs = [
      0.14, 0.22, 0.30, 0.38, 0.46,
      0.54, 0.62, 0.70, 0.78, 0.85
    ];

    ringTs.forEach(t => {
      const f = t * (scr.length - 1);
      const i = Math.min(scr.length - 1, Math.floor(f));
      const j = Math.min(scr.length - 1, i + 1);
      const q = f - i;

      const tangent = safeUnit(
        scr[i].tx + (scr[j].tx - scr[i].tx) * q,
        scr[i].ty + (scr[j].ty - scr[i].ty) * q
      );

      const normal = safeUnit(
        scr[i].nx + (scr[j].nx - scr[i].nx) * q,
        scr[i].ny + (scr[j].ny - scr[i].ny) * q
      );

      const p = {
        x: scr[i].x + (scr[j].x - scr[i].x) * q,
        y: scr[i].y + (scr[j].y - scr[i].y) * q
      };

      const w = maxHalf * widthAt(t) * 0.88;

      ctx.beginPath();
      ctx.moveTo(
        p.x + normal.x * w,
        p.y + normal.y * w
      );
      ctx.quadraticCurveTo(
        p.x + tangent.x * 1.2,
        p.y + tangent.y * 1.2,
        p.x - normal.x * w,
        p.y - normal.y * w
      );

      ctx.strokeStyle = 'rgba(119,115,106,0.30)';
      ctx.lineWidth = 0.58;
      ctx.stroke();
    });

    for (let j = 0; j < 6; j++) {
      const t = 0.36 + j * 0.075;
      const i = Math.min(
        scr.length - 1,
        Math.round(t * (scr.length - 1))
      );

      const p = scr[i];
      const w = hw(i) * 0.76;

      ctx.fillStyle = 'rgba(103,99,91,0.30)';

      for (const side of [-1, 1]) {
        ctx.beginPath();
        ctx.ellipse(
          p.x + p.nx * w * side,
          p.y + p.ny * w * side,
          0.78, 0.46,
          Math.atan2(p.ny, p.nx),
          0, Math.PI * 2
        );
        ctx.fill();
      }
    }

    ctx.restore();

    const hornI = Math.min(
      scr.length - 1,
      Math.round(0.90 * (scr.length - 1))
    );
    const horn = scr[hornI];
    const hornW = hw(hornI) * 0.20;

    ctx.beginPath();
    ctx.moveTo(
      horn.x - horn.nx * hornW,
      horn.y - horn.ny * hornW
    );
    ctx.quadraticCurveTo(
      horn.x + horn.tx * 2.8 - horn.nx * hornW * 0.6,
      horn.y + horn.ty * 2.8 - horn.ny * hornW * 0.6,
      horn.x + horn.tx * 7.0 + horn.nx * hornW * 1.6,
      horn.y + horn.ty * 7.0 + horn.ny * hornW * 1.6
    );
    ctx.lineTo(
      horn.x + horn.tx * 2.2,
      horn.y + horn.ty * 2.2
    );
    ctx.closePath();
    ctx.fillStyle = '#b8b3a8';
    ctx.fill();

    const head = scr[0];
    const headCx = head.x - head.tx * 2.4;
    const headCy = head.y - head.ty * 2.4;

    ctx.beginPath();
    ctx.ellipse(
      headCx, headCy,
      maxHalf * 0.48,
      maxHalf * 0.29,
      Math.atan2(-head.ty, -head.tx),
      0, Math.PI * 2
    );

    const headGrad = ctx.createLinearGradient(
      headCx - maxHalf, headCy - maxHalf,
      headCx + maxHalf, headCy + maxHalf
    );
    headGrad.addColorStop(0, '#715b49');
    headGrad.addColorStop(0.48, '#514034');
    headGrad.addColorStop(1, '#302720');

    ctx.fillStyle = headGrad;
    ctx.fill();

    ctx.strokeStyle = 'rgba(35,27,22,0.52)';
    ctx.lineWidth = 0.55;
    ctx.stroke();

    ctx.restore();
  }

  function paintWorld() {
    fit(world, 1);
    const ctx = world.getContext('2d');
    const v = view();
    ctx.clearRect(0, 0, v.w, v.h);
    ctx.save();
    // 场地格线：世界坐标锚定（不随任何个体移动），可隐藏
    if (habitat.showGrid !== false) {
      const gs = 40;
      const wx0 = (0 - v.cx) / v.s, wx1 = (v.w - v.cx) / v.s;
      const wy0 = (0 - v.cy) / v.s, wy1 = (v.h - v.cy) / v.s;
      ctx.strokeStyle = 'rgba(210,220,214,0.10)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (let gx = Math.ceil(wx0 / gs) * gs; gx <= wx1; gx += gs) {
        ctx.moveTo(v.px(gx), v.py(wy0));
        ctx.lineTo(v.px(gx), v.py(wy1));
      }
      for (let gy = Math.ceil(wy0 / gs) * gs; gy <= wy1; gy += gs) {
        ctx.moveTo(v.px(wx0), v.py(gy));
        ctx.lineTo(v.px(wx1), v.py(gy));
      }
      ctx.stroke();
    }
    const env = drive();
    if (habitat.reference && habitat.reference.length > 1) {
      drawSilk(ctx, habitat.reference, v, 0.09);
    }
    habitat.orphans.forEach(line => drawSilk(ctx, line, v, env.silkAlpha));
    const editAgent = habitat.weaveEdit ? weaveEditAgent() : null;
    habitat.agents.forEach(agent => {
      if (agent.mode === 'bench') return;
      if (agent.kind === 'weave') {
        // 丝被隐藏时，只留一圈很淡的虚线框，方便找回这一块在哪
        const hideSilk = habitat.hideSilkAll || agent.hideSilk;
        if (hideSilk) {
          ctx.save();
          ctx.strokeStyle = 'rgba(226,232,228,0.16)';
          ctx.setLineDash([6, 6]);
          ctx.strokeRect(
            v.px(agent.x - agent.w / 2), v.py(agent.y - agent.h / 2),
            agent.w * v.s, agent.h * v.s
          );
          ctx.restore();
        } else {
        // 编辑某一块时，其余块压暗到 42%，一眼就知道"现在在改哪一块"
        const dimOther = editAgent && editAgent.id !== agent.id;
        if (dimOther) ctx.save();
        if (dimOther) ctx.globalAlpha = 0.42;
        drawWeave(ctx, agent, v);
        if (dimOther) ctx.restore();
        }
        if (agent.id === habitat.selected) {
          ctx.strokeStyle = 'rgba(230,236,233,0.35)';
          ctx.strokeRect(
            v.px(agent.x - agent.w / 2), v.py(agent.y - agent.h / 2),
            agent.w * v.s, agent.h * v.s
          );
        }
        // 刚放入 / 刚改过的块：边框闪两下，让人看清"变化落在哪一块"
        if (agent.flashUntil && performance.now() < agent.flashUntil) {
          const k = Math.max(0, (agent.flashUntil - performance.now()) / 1500);
          ctx.save();
          ctx.strokeStyle = 'rgba(240,180,90,' + (0.35 + 0.55 * Math.abs(Math.sin(k * Math.PI * 3))).toFixed(3) + ')';
          ctx.lineWidth = 2;
          ctx.setLineDash([7, 5]);
          ctx.strokeRect(
            v.px(agent.x - agent.w / 2) - 3, v.py(agent.y - agent.h / 2) - 3,
            agent.w * v.s + 6, agent.h * v.s + 6
          );
          ctx.restore();
        }
        drawWeaveHandles(ctx, agent, v);
        if (editAgent && editAgent.id === agent.id) drawEditLivePreview(ctx, agent, v);
        return;
      }
      if (agent.kind === 'route') {
        const unit = agent.scope === 'cell' ? weaveUnitFor(agent) : null;
        const hideSilk = habitat.hideSilkAll || agent.hideSilk;
        const hideBody = habitat.hideBodies || agent.hideBody;
        // 收进格子的蚕：丝迹逐点夹在格内（不依赖 canvas clip，边界一定干净）
        if (!hideSilk) {
          if (unit) drawSilkInRect(ctx, agent.silk, v, env.silkAlpha, unit);
          else drawSilk(ctx, agent.silk, v, env.silkAlpha);
        }
        if (!hideBody) drawHabitatWorm(ctx, agent, v);
      } else {
        if (!(habitat.hideSilkAll || agent.hideSilk)) drawSilk(ctx, agent.silk, v, env.silkAlpha);
        if (!(habitat.hideBodies || agent.hideBody)) drawHabitatWorm(ctx, agent, v);
      }
      if (agent.id === habitat.selected) {
        ctx.strokeStyle = 'rgba(230,236,233,0.35)';
        ctx.strokeRect(v.px(agent.x) - 16, v.py(agent.y) - 16, 32, 32);
      }
    });
    ctx.restore();
  }

  /* 这一格用哪只蚕：下拉里列出场地里所有实测蚕 */
  function refreshWeaveWormSelect() {
    const sel = document.getElementById('habWeaveWorm');
    if (!sel) return;
    const a = habitat.agents.find(x => x.id === habitat.selected && x.kind === 'weave');
    const routes = habitat.agents.filter(x => x.kind === 'route' && x.wormId != null && x.id === 'rt-' + x.wormId);
    if (!a) { sel.innerHTML = '<option value="">先选一块织网单元</option>'; sel.disabled = true; return; }
    sel.disabled = false;
    const types = [];
    routes.forEach(r => { if (types.indexOf(r.wormId) < 0) types.push(r.wormId); });
    sel.innerHTML = '<option value="">合并丝路（默认）</option>' +
      (types.length > 1 ? '<option value="all">全部蚕（每种一只）</option>' : '') +
      types.map(wid => {
        const has = habitat.agents.some(x => x.kind === 'route' && x.wormId === wid && x.homeUnitId === a.id);
        return '<option value="' + wid + '">蚕 ' + wid + (has ? '（已在这格）' : '') + '</option>';
      }).join('');
    sel.value = a.measuredWorm != null ? String(a.measuredWorm) : (a.wormParty ? 'all' : '');
  }

  /* 把某一种蚕指定给某一块单元（可重复调用；同种蚕可同时服务多格） */
  function assignWormToUnit(unitId, val) {
    const a = habitat.agents.find(x => x.id === unitId && x.kind === 'weave');
    if (!a) return 0;
    pushUndo();
    a.wormParty = val === 'all';
    const widRaw = (val === '' || val == null || val === 'all') ? null : String(val).replace(/[^0-9.-]/g, '');
    const wid = widRaw == null ? null : Number(widRaw);
    const widOk = Number.isFinite(wid) ? wid : null;
    a.measuredWorm = widOk;
    if (val === 'all') {
      const types = [];
      habitat.agents.forEach(x => {
        if (x.kind === 'route' && x.wormId != null && types.indexOf(x.wormId) < 0) types.push(x.wormId);
      });
      types.forEach(t => spawnCellWorm(a, t));
      return types.length;
    }
    if (widOk == null) {
      habitat.agents.forEach(x => {
        if (x.kind === 'route' && x.homeUnitId === a.id && x.id.indexOf('@') > 0) {
          x.homeUnitId = null;
          x.scope = 'field';
        }
      });
      return 0;
    }
    spawnCellWorm(a, widOk);
    return 1;
  }

  function renderList() {
    refreshWeaveWormSelect();
    const box = document.getElementById('habAgents');
    const syncStat = document.getElementById('habSyncStat');
    const routeN = habitat.agents.filter(a => a.kind === 'route').length;
    const weaveN = habitat.agents.filter(a => a.kind === 'weave').length;
    const demoN = habitat.agents.length - routeN - weaveN;
    if (syncStat) syncStat.textContent = '实测 ' + routeN + ' 只 · 演示 ' + demoN + ' 只 · 织网单元 ' + weaveN + ' 个';
    if (!habitat.agents.length) {
      box.innerHTML = '<div class="hab-note">暂无个体：描好的蚕会自动出现在这里；也可添加随机演示蚕。</div>';
      syncFieldStatus();
      syncRoutePanel();
      return;
    }
    box.innerHTML = habitat.agents.map(a => {
      const label = { bench: '待放入', idle: '已放置', drag: '拖动中', run: '爬行', paused: '暂停' }[a.mode] || a.mode;
      const disp = a.kind === 'route' ? '蚕 ' + a.wormId : (a.kind === 'weave' ? '织网单元 ' + a.id : a.id);
      const tag = a.kind === 'route' ? '<span class="tag">实测</span>'
        : (a.kind === 'weave' ? '<span class="tag">织网单元</span>' : '<span class="tag">演示</span>');
      const tip = a.kind === 'route'
        ? (a.mode === 'idle' || a.mode === 'paused' ? '<span class="drag-tip">可拖动改位置</span>' : '<span class="drag-tip">拖动可改位置</span>')
        : (a.kind === 'weave'
          ? '<span class="drag-tip">可拖动改位置</span>'
          : (a.mode === 'bench' ? '<span class="drag-tip">按住拖到场地放入</span>' : '<span class="drag-tip">可拖动改位置</span>'));
      const bodyOff = habitat.hideBodies || a.hideBody;
      const silkOff = habitat.hideSilkAll || a.hideSilk;
      const minis = a.kind === 'weave'
        ? '<div class="mini-row"><button type="button" class="mini' + (silkOff ? ' off' : '') + '" data-act="silk">丝' + (silkOff ? '：已隐藏' : '：显示中') + '</button></div>'
        : '<div class="mini-row">' +
          '<button type="button" class="mini' + (bodyOff ? ' off' : '') + '" data-act="body">蚕' + (bodyOff ? '：已隐藏' : '：显示中') + '</button>' +
          '<button type="button" class="mini' + (silkOff ? ' off' : '') + '" data-act="silk">丝' + (silkOff ? '：已隐藏' : '：显示中') + '</button>' +
          '</div>';
      return '<div class="agent-card' + (a.id === habitat.selected ? ' on' : '') + '" data-id="' + a.id + '"><b>' + disp + '</b>' + tag + '<br><span class="hab-note">' + label + (a.bodyVisible ? '' : ' · 身体已隐藏') + '</span>' + tip + minis + '</div>';
    }).join('');
    syncFieldStatus();
    syncRoutePanel();
  }

  // 场地里现在到底有什么：放/删之后一眼能看出数量变化，不用去猜
  function syncFieldStatus() {
    const el = document.getElementById('habFieldStatus');
    if (!el) return;
    const agents = habitat.agents || [];
    const nW = agents.filter(a => a.kind === 'weave').length;
    const nR = agents.filter(a => a.kind === 'route').length;
    const nD = agents.filter(a => a.kind !== 'weave' && a.kind !== 'route').length;
    const nO = (habitat.obstacles || []).length;
    el.textContent = '场地里现在有：' + nW + ' 块织网单元 · ' + nR + ' 只蚕 · ' + nD + ' 个演示个体 · ' + nO + ' 个障碍。';
  }

  function renderDrive() {
    const d = drive();
    document.getElementById('habTempVal').textContent = habitat.tempC.toFixed(1);
    document.getElementById('habHumVal').textContent = String(habitat.humidity);
    document.getElementById('habDrive').textContent =
      '演示：速度 ' + d.speed.toFixed(1) + '，摆动 ' + d.sway.toFixed(2) + '，停顿倾向 ' + d.pauseChance.toFixed(2) + '。模型 ' + MODEL + '。';
    document.getElementById('habClock').textContent = '模拟 ' + habitat.simTime.toFixed(1) + ' s';
    const timeSlider = document.getElementById('habTime');
    if (timeSlider && !timeSlider.dataset.scrubbing) {
      timeSlider.value = String(Math.min(parseFloat(timeSlider.max) || 60, habitat.simTime));
    }
  }

  /* ===== 时间滑条：拖到哪就停在哪 =====
     拖动 = 把整场"重算到这一刻"并暂停；丝绸也会重算，所以停在中间看到的就是那一刻的样子。 */
  function seekTo(target) {
    const want = Math.max(0, Math.min(120, Number.isFinite(target) ? target : 0));
    const movable = habitat.agents.filter(a => a.kind === 'route' || a.kind === 'weave');
    if (!movable.length) {
      toast('场地里还没有可运动的个体。', 'err');
      return;
    }
    movable.forEach(a => {
      if (a.mode === 'drag' || a.mode === 'bench') return;
      a.mode = 'run';
      if (a.kind === 'route') { a.u = 0; a.travel = 0; a.silk = []; a.follow = true; }
      else { a.u = 0; }
    });
    habitat.simTime = 0;
    const dt = 0.05;
    const steps = Math.min(2400, Math.round(want / dt));
    for (let i = 0; i < steps; i++) step(dt);
    habitat.simTime = want;
    movable.forEach(a => { if (a.mode === 'run') a.mode = 'paused'; });
    habitat.runningClock = false;
    renderDrive();
    renderList();
    const clock = document.getElementById('habClock');
    if (clock) clock.textContent = '停在第 ' + want.toFixed(1) + ' s';
    hint('已停在 ' + want.toFixed(1) + ' s。点「继续」从这一刻往下走，或再拖滑条换位置。');
  }

  function bindTimeSlider() {
    const el = document.getElementById('habTime');
    if (!el) return;
    let timer = 0;
    let dragging = false;
    el.addEventListener('pointerdown', () => { dragging = true; el.dataset.scrubbing = '1'; });
    el.addEventListener('input', () => {
      el.dataset.scrubbing = '1';
      clearTimeout(timer);
      timer = setTimeout(() => { seekTo(parseFloat(el.value)); }, 140);
    });
    const done = () => {
      clearTimeout(timer);
      dragging = false;
      seekTo(parseFloat(el.value));
      delete el.dataset.scrubbing;
    };
    el.addEventListener('change', done);
    el.addEventListener('pointerup', () => { if (dragging) done(); });
  }

  function selectAgent(id) {
    habitat.selected = id;
    habitat.selectedLeaf = null;
    renderList();
  }

  function placeAgent(agent, x, y) {
    if (blocked(x, y)) return false;
    agent.x = x;
    agent.y = y;
    if (agent.mode === 'bench') agent.silk = [{ x, y, t: habitat.simTime }];
    agent.mode = 'idle';
    return true;
  }

  function panelVal(id, txt) { const el = document.getElementById(id); if (el) el.textContent = txt; }
  function panelSet(id, val) { const el = document.getElementById(id); if (el) el.value = val; }
  function panelCheck(id, on) { const el = document.getElementById(id); if (el) el.checked = !!on; }

  function syncRoutePanel() {
    const a = chosen();
    const info = document.getElementById('habRouteInfo');
    const weavePanel = document.getElementById('habWeavePanel');
    if (!a) {
      if (weavePanel) weavePanel.hidden = true;
      info.textContent = '未选中个体';
      panelSet('habAdjX', 0); panelVal('habAdjXVal', '0');
      panelSet('habAdjY', 0); panelVal('habAdjYVal', '0');
      panelSet('habAdjRot', 0); panelVal('habAdjRotVal', '0°');
      panelSet('habAdjScale', 1); panelVal('habAdjScaleVal', '1.00');
      panelSet('habAdjFollow', false);
      panelCheck('habAdjFollow', false);
      panelSet('habAdjSpeed', 1); panelVal('habAdjSpeedVal', '1.00×');
      ['habAdjRot', 'habAdjScale', 'habAdjFollow', 'habAdjSpeed'].forEach(id => { const el = document.getElementById(id); if (el) el.disabled = true; });
      return;
    }
    const isRoute = a.kind === 'route';
    if (a.kind === 'weave') {
      if (weavePanel) weavePanel.hidden = false;
      const prog = Math.round((a.u || 0) * 100);
      const sample = a.sample || { threads: 0, points: 0, walls: 0 };
      info.innerHTML = '织网单元 ' + a.id + ' · 细格 ' + Math.round(a.w) + '×' + Math.round(a.h) +
        ' · 每格 ' + sample.threads + ' 根丝 · ' + prog + '% · 轨迹：' +
        (a.profile && a.profile.source && a.profile.source.kind === 'measured'
          ? '实测（' + (a.profile.label || a.profile.id || '样本') + '）'
          : '实测样本 raby-1 回放');
      panelSet('habAdjX', Math.round(a.x)); panelVal('habAdjXVal', String(Math.round(a.x)));
      panelSet('habAdjY', Math.round(a.y)); panelVal('habAdjYVal', String(Math.round(a.y)));
      panelSet('habAdjRot', 0); panelVal('habAdjRotVal', '0°');
      panelSet('habAdjScale', 1); panelVal('habAdjScaleVal', '1.00');
      panelSet('habAdjFollow', false); panelCheck('habAdjFollow', false);
      panelSet('habAdjSpeed', Number.isFinite(a.speedScale) ? a.speedScale : 1);
      panelVal('habAdjSpeedVal', (Number.isFinite(a.speedScale) ? a.speedScale : 1).toFixed(2) + '×');
      ['habAdjRot', 'habAdjScale', 'habAdjFollow'].forEach(id => { const el = document.getElementById(id); if (el) el.disabled = true; });
      const speedEl = document.getElementById('habAdjSpeed');
      if (speedEl) speedEl.disabled = false;
      panelSet('habWeaveW', Math.round(a.w)); panelVal('habWeaveWVal', Math.round(a.w) + 'px');
      panelSet('habWeaveH', Math.round(a.h)); panelVal('habWeaveHVal', Math.round(a.h) + 'px');
      panelSet('habWeaveCov', a.coverage); panelVal('habWeaveCovVal', (a.coverage || 0).toFixed(2));
      const sk = Number.isFinite(a.scaleK) ? a.scaleK : 0.9;
      panelSet('habWeaveScaleK', sk); panelVal('habWeaveScaleKVal', sk.toFixed(2) + '×');
      panelSet('habWeaveWorms', a.worms || 6); panelVal('habWeaveWormsVal', String(a.worms || 6));
      panelSet('habWeaveTone', Math.round((a.tone == null ? 0.85 : a.tone) * 100) / 100);
      panelVal('habWeaveToneVal', (a.tone == null ? 0.85 : a.tone).toFixed(2));
      const strataEl = document.getElementById('habWeaveStrata');
      if (strataEl) strataEl.value = String(Math.max(1, Math.min(3, a.strata || 2)));
      panelVal('habWeaveStrataVal', String(Math.max(1, Math.min(3, a.strata || 2))));
      panelSet('habWeaveGap', a.gap == null ? 6 : a.gap);
      panelVal('habWeaveGapVal', String(a.gap == null ? 6 : a.gap));
      const shapeSel = document.getElementById('habWeaveShape');
      if (shapeSel) shapeSel.value = a.shape || 'island';
      const note = document.getElementById('habWeaveNote');
      if (note) note.textContent = '每格 ' + sample.points + ' 点 · 黑底细网格（可隐藏）' +
        ' · 轨迹：' + (a.profile ? (a.profile.label || a.profile.id || '自定义') : '实测样本 raby-1 回放') +
        ' · 自定义壁/丝路 ' + (sample.custom || 0) + ' 条 · 种子 ' + a.seed;
      return;
    }
    if (weavePanel) weavePanel.hidden = true;
    info.innerHTML = isRoute ? '实测 · 蚕 ' + a.wormId + ' · ' + a.route.length + ' 点' : '随机个体 · ' + a.id;
    const px = isRoute ? (a.offX || 0) : a.x;
    const py = isRoute ? (a.offY || 0) : a.y;
    panelSet('habAdjX', Math.round(px)); panelVal('habAdjXVal', String(Math.round(px)));
    panelSet('habAdjY', Math.round(py)); panelVal('habAdjYVal', String(Math.round(py)));
    const deg = Math.round((a.rot || 0) * 180 / Math.PI);
    panelSet('habAdjRot', deg); panelVal('habAdjRotVal', deg + '°');
    panelSet('habAdjScale', a.scale || 1); panelVal('habAdjScaleVal', (a.scale || 1).toFixed(2));
    panelSet('habAdjFollow', !!a.follow);
    panelCheck('habAdjFollow', !!a.follow);
    const scopeEl = document.getElementById('habAdjScope');
    if (scopeEl) {
      scopeEl.value = a.scope === 'cell' ? 'cell' : 'field';
      scopeEl.disabled = !isRoute;
    }
    ['habAdjRot', 'habAdjScale', 'habAdjFollow'].forEach(id => { const el = document.getElementById(id); if (el) el.disabled = !isRoute; });
    const speedScale = Number.isFinite(a.speedScale) ? a.speedScale : 1;
    panelSet('habAdjSpeed', speedScale);
    panelVal('habAdjSpeedVal', speedScale.toFixed(2) + '×');
    const speedEl = document.getElementById('habAdjSpeed');
    if (speedEl) speedEl.disabled = false;
  }

  function bindRoutePanel() {
    const bind = (id, fn) => { const el = document.getElementById(id); if (el) el.addEventListener('input', fn); };
    bind('habAdjX', () => { const a = chosen(); if (!a) return; const v = parseFloat(document.getElementById('habAdjX').value); if (a.kind === 'route') { a.offX = v; applyRouteTransform(a); } else { a.x = v; } syncRoutePanel(); });
    bind('habAdjY', () => { const a = chosen(); if (!a) return; const v = parseFloat(document.getElementById('habAdjY').value); if (a.kind === 'route') { a.offY = v; applyRouteTransform(a); } else { a.y = v; } syncRoutePanel(); });
    bind('habAdjRot', () => { const a = chosen(); if (!a || a.kind !== 'route') return; a.rot = parseFloat(document.getElementById('habAdjRot').value) * Math.PI / 180; applyRouteTransform(a); syncRoutePanel(); });
    bind('habAdjScale', () => { const a = chosen(); if (!a || a.kind !== 'route') return; a.scale = parseFloat(document.getElementById('habAdjScale').value); applyRouteTransform(a); syncRoutePanel(); });
    bind('habAdjSpeed', () => {
      const a = chosen(); if (!a) return;
      const value = parseFloat(document.getElementById('habAdjSpeed').value);
      a.speedScale = Math.max(0.1, Math.min(3, Number.isFinite(value) ? value : 1));
      panelVal('habAdjSpeedVal', a.speedScale.toFixed(2) + '×');
    });
    const fol = document.getElementById('habAdjFollow');
    if (fol) fol.addEventListener('change', () => {
      const a = chosen(); if (!a) return;
      a.follow = fol.checked;
      if (a.follow && a.mode === 'idle') a.mode = 'run';
      renderList();
    });
    const scopeSel = document.getElementById('habAdjScope');
    if (scopeSel) scopeSel.addEventListener('change', () => {
      const a = chosen(); if (!a || a.kind !== 'route') return;
      a.scope = scopeSel.value === 'cell' ? 'cell' : 'field';
      a.homeUnitId = null;
      a.silk = [];          // 换了活动范围，先把之前的场地笔迹清掉，免得残留线索误导
      a.travel = 0;
      if (a.scope === 'cell' && !habitat.agents.some(u => u.kind === 'weave')) {
        hint('还没有织网单元：先放一个/铺一块群，蚕才会收进单格。');
      } else if (a.scope === 'cell') {
        const unit = weaveUnitFor(a);
        hint('已收进单元格' + (unit ? '「' + unit.id + '」' : '') + '：蚕只在这个格内爬行吐丝，丝不会越界（旧的场地笔迹已清掉）。');
      } else {
        hint('跨格模式：蚕沿整场巡游，会依次穿过多个织网单元。');
      }
      renderList();
    });
    const rebuildWeave = () => {
      const a = chosen();
      if (!a || a.kind !== 'weave') return;
      buildWeave(a);
      a.u = 0;
      if (a.mode !== 'run') a.mode = 'idle';
      syncRoutePanel();
    };
    bind('habWeaveW', () => {
      const a = chosen(); if (!a || a.kind !== 'weave') return;
      a.w = Math.max(80, Math.min(1200, parseFloat(document.getElementById('habWeaveW').value) || 200));
      panelVal('habWeaveWVal', Math.round(a.w) + 'px');
      rebuildWeave();
    });
    bind('habWeaveH', () => {
      const a = chosen(); if (!a || a.kind !== 'weave') return;
      a.h = Math.max(80, Math.min(1200, parseFloat(document.getElementById('habWeaveH').value) || 200));
      panelVal('habWeaveHVal', Math.round(a.h) + 'px');
      rebuildWeave();
    });
    bind('habWeaveCov', () => {
      const a = chosen(); if (!a || a.kind !== 'weave') return;
      a.coverage = Math.max(0.15, Math.min(0.85, parseFloat(document.getElementById('habWeaveCov').value) || 0.55));
      panelVal('habWeaveCovVal', a.coverage.toFixed(2));
      rebuildWeave();
    });
    bind('habWeaveScaleK', () => {
      const a = chosen(); if (!a || a.kind !== 'weave') return;
      a.scaleK = Math.max(0.2, Math.min(1.2, parseFloat(document.getElementById('habWeaveScaleK').value) || 0.9));
      panelVal('habWeaveScaleKVal', a.scaleK.toFixed(2) + '×');
      rebuildWeave();
      hint('丝路尺度 ' + a.scaleK.toFixed(2) + '×：' + (a.scaleK >= 0.95
        ? '一条丝路≈整格，这是实测 1:1 的比例（一次吐丝 ≈ 一格）。'
        : '一条丝路≈' + Math.round(a.scaleK * 100) + '% 格宽，相当于把实测缩小了约 ' + (1 / a.scaleK).toFixed(1) + ' 倍。'));
    });
    bind('habWeaveWorms', () => {
      const a = chosen(); if (!a || a.kind !== 'weave') return;
      a.worms = Math.max(1, Math.min(12, parseInt(document.getElementById('habWeaveWorms').value, 10) || 6));
      panelVal('habWeaveWormsVal', String(a.worms));
      rebuildWeave();
    });
    bind('habWeaveTone', () => {
      const a = chosen(); if (!a || a.kind !== 'weave') return;
      a.tone = Math.max(0.4, Math.min(1.2, parseFloat(document.getElementById('habWeaveTone').value) || 0.85));
      panelVal('habWeaveToneVal', a.tone.toFixed(2));
    });
    bind('habWeaveGap', () => {
      const a = chosen(); if (!a || a.kind !== 'weave') return;
      a.gap = Math.max(0, Math.min(40, parseFloat(document.getElementById('habWeaveGap').value) || 0));
      panelVal('habWeaveGapVal', String(a.gap));
    });
    bind('habWeaveStrata', () => {
      const a = chosen(); if (!a || a.kind !== 'weave') return;
      a.strata = Math.max(1, Math.min(3, parseInt(document.getElementById('habWeaveStrata').value, 10) || 2));
      panelVal('habWeaveStrataVal', String(a.strata));
    });
    const wormSel = document.getElementById('habWeaveWorm');
    if (wormSel) wormSel.addEventListener('change', () => {
      const a = chosen(); if (!a || a.kind !== 'weave') return;
      const val = wormSel.value;
      const n = assignWormToUnit(a.id, val);
      if (val === 'all') hint('这一格现在让 ' + n + ' 种蚕一起织：每种一个实例，起点随机落在格内。');
      else if (val === '') hint('这一格用合并后的实测丝路（所有蚕的数据并成一条）。');
      else hint('这一格现在用「蚕 ' + val + '」。同一种蚕可以同时用在很多格，互不影响。');
      renderList();
    });
    const weaveEditBtn = document.getElementById('habWeaveEdit');
    const weaveEditDone = document.getElementById('habWeaveEditDone');
    const weaveToolsEl = document.getElementById('habWeaveTools');
    const weaveLegendEl = document.getElementById('habWeaveLegend');

    function weaveEditToolName(t) {
      return ({ shape: '形状', hole: '孔洞', notch: '缺口', wall: '加壁', path: '加丝路', outline: '外框' })[t] || '形状';
    }
    function syncWeaveToolUI() {
      const e = habitat.weaveEdit;
      const on = !!(e && e.agentId);
      if (weaveEditBtn) {
        weaveEditBtn.textContent = on ? '退出编辑' : '编辑这一格';
        weaveEditBtn.setAttribute('aria-pressed', on ? 'true' : 'false');
      }
      if (weaveToolsEl) weaveToolsEl.setAttribute('aria-disabled', on ? 'false' : 'true');
      if (weaveLegendEl) weaveLegendEl.style.display = on ? '' : 'none';
      if (!weaveToolsEl) return;
      weaveToolsEl.querySelectorAll('.hab-tool').forEach(btn => {
        const active = on && btn.dataset.wtool === ((e && e.tool) || 'shape');
        btn.setAttribute('aria-pressed', active ? 'true' : 'false');
      });
    }
    function setWeaveTool(t) {
      const e = habitat.weaveEdit;
      if (!e || !e.agentId) { toast('先点「编辑这一格」，再选工具。', 'err'); return; }
      e.tool = t;
      // 画线类工具进入"连续加点"状态；形状/孔洞是纯拖拽，缺口现在也改成自己点出一圈
      e.mode = (t === 'wall' || t === 'path' || t === 'outline' || t === 'notch') ? t : null;
      if (t === 'notch') { e.drafts = {}; }
      if (t === 'outline') e.outlinePts = e.outlinePts || [];
      syncWeaveToolUI();
      syncEditNote();
    }
    if (weaveToolsEl) weaveToolsEl.addEventListener('click', (ev) => {
      const btn = ev.target.closest('.hab-tool');
      if (!btn) return;
      setWeaveTool(btn.dataset.wtool);
    });

    function enterWeaveEdit(targetId) {
      const a = targetId
        ? habitat.agents.find(x => x.id === targetId)
        : chosen();
      if (!a || a.kind !== 'weave') { toast('先在场地点中一块织网单元，再编辑。', 'err'); return; }
      selectAgent(a.id);
      habitat.weaveEdit = {
        agentId: a.id, ix: 0, iy: 0,
        mode: null,
        tool: habitat.weaveEdit && habitat.weaveEdit.tool ? habitat.weaveEdit.tool : 'shape',
        drafts: {},
      };
      syncWeaveToolUI();
      syncEditNote();
      hint('现在在改「' + a.id + '」：直接拖手柄就能改。点另一块会自动切到那一块，点空白处就退出编辑。');
    }
    function exitWeaveEdit() {
      const e = habitat.weaveEdit;
      if (e && e.agentId) finishWeaveEditLine();
      habitat.weaveEdit = null;
      habitat.hoverHandle = null;
      syncWeaveToolUI();
      syncEditNote();
      if (world) world.style.cursor = '';
      hint('已退出形状编辑，可以继续播放或放新的单元。');
    }
    function deleteWeaveUnit(a) {
      if (!a || a.kind !== 'weave') { toast('先点中一块织网单元，再删除。', 'err'); return; }
      pushUndo();
      if (habitat.weaveEdit && habitat.weaveEdit.agentId === a.id) exitWeaveEdit();
      const label = a.id;
      habitat.agents = habitat.agents.filter(x => x.id !== a.id);
      if (habitat.selected === a.id) habitat.selected = null;
      habitat.hoverHandle = null;
      if (a.cache && a.cache.clear) a.cache.clear();
      if (typeof renderList === 'function') renderList();
      const rest = habitat.agents.filter(x => x.kind === 'weave').length;
      toast('删掉了这一块织网单元（' + label + '）。还剩 ' + rest + ' 块。按 Ctrl+Z 可以撤回。', 'ok');
    }
    // 编辑相关函数只活在这个面板闭包里，而场地画布的指针事件在更外层：
    // 用一个全局小桥把它们接出去，避免同一套逻辑写两遍。
    window.__weaveHooks = Object.assign(window.__weaveHooks || {}, {
      enter: enterWeaveEdit,
      exit: exitWeaveEdit,
      deleteAt: (p) => (typeof weaveDeleteAt === 'function' ? weaveDeleteAt(p) : false),
      deleteUnit: (id) => deleteWeaveUnit(habitat.agents.find(x => x.id === id) || chosen()),
    });
    if (weaveEditBtn) weaveEditBtn.addEventListener('click', () => {
      if (habitat.weaveEdit && habitat.weaveEdit.agentId) exitWeaveEdit();
      else enterWeaveEdit();
    });
    if (weaveEditDone) weaveEditDone.addEventListener('click', () => {
      if (!habitat.weaveEdit || !habitat.weaveEdit.agentId) { toast('现在不在编辑状态。', 'err'); return; }
      exitWeaveEdit();
      toast('已保存这一格的修改。', 'ok');
    });
    syncWeaveToolUI();
    const weaveEditEnd = document.getElementById('habWeaveEditEnd');
    if (weaveEditEnd) weaveEditEnd.addEventListener('click', finishWeaveEditLine);
    const notchRedraw = document.getElementById('habWeaveNotchRedraw');
    if (notchRedraw) notchRedraw.addEventListener('click', () => {
      const a = weaveEditAgent();
      const e = habitat.weaveEdit;
      if (!a || !e) { hint('先点一块织网单元进编辑，再用「重画缺口」。'); return; }
      pushUndo();
      const sh = ensureShapeOverride(a, e.ix, e.iy);
      delete sh.notchPts;
      delete sh.notch;
      if (a.cache && a.cache.delete) a.cache.delete(e.ix + ',' + e.iy);
      weaveCellContent(a, e.ix, e.iy);
      setWeaveTool('notch');
      e.mode = 'notch';
      e.drafts = {};
      syncEditNote();
      toast('旧缺口已清掉：在格内点几下围出新形状，双击（或点「这一笔收尾」）收尾。', 'ok');
    });
    const weaveEditClear = document.getElementById('habWeaveEditClear');
    if (weaveEditClear) weaveEditClear.addEventListener('click', clearWeaveCellCustom);
    const gridToggle = document.getElementById('habGridToggle');
    if (gridToggle) gridToggle.addEventListener('change', () => {
      habitat.showGrid = !!gridToggle.checked;
    });
    const hideAllBody = document.getElementById('habHideAllBody');
    if (hideAllBody) hideAllBody.addEventListener('change', () => {
      habitat.hideBodies = !!hideAllBody.checked;
      renderList();
    });
    const hideAllSilk = document.getElementById('habHideAllSilk');
    if (hideAllSilk) hideAllSilk.addEventListener('change', () => {
      habitat.hideSilkAll = !!hideAllSilk.checked;
      renderList();
    });
    // 蚕的大小 / 沿丝路重复 / 丝线粗细 / 亮度 / 观感
    const wormSizeEl = document.getElementById('habWormSize');
    if (wormSizeEl) wormSizeEl.addEventListener('input', () => {
      habitat.wormSize = parseFloat(wormSizeEl.value) || 1;
      const lab = document.getElementById('habWormSizeVal');
      if (lab) lab.textContent = habitat.wormSize.toFixed(2) + '×';
    });
    const pathBoostEl = document.getElementById('habPathBoost');
    if (pathBoostEl) pathBoostEl.addEventListener('input', () => {
      habitat.pathBoost = parseFloat(pathBoostEl.value) || 1;
      const lab = document.getElementById('habPathBoostVal');
      if (lab) lab.textContent = habitat.pathBoost.toFixed(1) + '×';
    });
    const silkWidthEl = document.getElementById('habSilkWidth');
    if (silkWidthEl) silkWidthEl.addEventListener('input', () => {
      habitat.silkWidth = parseFloat(silkWidthEl.value) || 1;
      const lab = document.getElementById('habSilkWidthVal');
      if (lab) lab.textContent = habitat.silkWidth.toFixed(1);
    });
    const silkGainEl = document.getElementById('habSilkGain');
    if (silkGainEl) silkGainEl.addEventListener('input', () => {
      habitat.silkGain = parseFloat(silkGainEl.value) || 1;
      const lab = document.getElementById('habSilkGainVal');
      if (lab) lab.textContent = habitat.silkGain.toFixed(1) + '×';
    });
    const silkModeEl = document.getElementById('habSilkMode');
    if (silkModeEl) silkModeEl.addEventListener('change', () => {
      habitat.silkMode = silkModeEl.value || 'silk';
    });
    const shapeSel = document.getElementById('habWeaveShape');
    if (shapeSel) shapeSel.addEventListener('change', () => {
      const a = chosen(); if (!a || a.kind !== 'weave') return;
      a.shape = shapeSel.value;
      rebuildWeave();
    });
    const weaveRebuild = document.getElementById('habWeaveRebuild');
    if (weaveRebuild) weaveRebuild.addEventListener('click', () => {
      const a = chosen(); if (!a || a.kind !== 'weave') return;
      pushUndo();
      a.seed = Math.floor(Math.random() * 1e9) >>> 0;
      rebuildWeave();
      toast('已按新种子重织。', 'ok');
    });
    const profileBtn = document.getElementById('habWeaveLoadProfile');
    const profileFile = document.getElementById('habWeaveProfileFile');
    if (profileBtn && profileFile) {
      profileBtn.addEventListener('click', () => profileFile.click());
      profileFile.addEventListener('change', () => {
        const a = chosen();
        const f = profileFile.files && profileFile.files[0];
        if (!a || a.kind !== 'weave' || !f) return;
        const reader = new FileReader();
        reader.onload = () => {
          try {
            const prof = JSON.parse(reader.result);
            if (!prof || typeof prof !== 'object') throw new Error('文件不是 JSON 对象');
            // A. 运动指纹（描图器「导出指纹」产物）
            if (/silkworm-motion-profile/.test(prof.schema || '')) {
              pushUndo();
              if (prof.pathTemplate && Array.isArray(prof.pathTemplate.strokes)) {
                prof.pathTemplate.strokes = prof.pathTemplate.strokes.map(st =>
                  Array.isArray(st[0]) ? st.reduce((acc, p) => (acc.push(p[0], p[1]), acc), []) : st
                );
              }
              a.profile = prof;
              rebuildWeave();
              const kind = prof.source && prof.source.kind === 'measured' ? '实测' : '演示（非实测）';
              toast('已载入指纹：' + (prof.wormId || prof.id || '未命名') + '（' + kind + '）', 'ok');
              hint(prof.fingerprint && prof.fingerprint.strokeAspects
                ? '指纹的实测纵横比已参与生成；每格密度由「每格蚕数」与覆盖率控制。'
                : '指纹只影响纵横比与包络数量；密度/颜色仍由覆盖率控制。');
              return;
            }
            // B. 实测点列（trajectories.json / 描图器「导出 JSON」的 curves3d）→ 直接进场地当一只实测蚕
            const added = importPointCloudDoc(prof);
            if (added) {
              toast('已从点列载入 ' + added + ' 只实测蚕（' + (prof.curves3d ? prof.curves3d.length : prof.trajectories.length) + ' 笔）。蚕已自动收进单元格。', 'ok');
              hint('这是"实测点列"文件（x_mm / y_mm），不是运动指纹；两者都能用，指纹影响形态参数，点列直接当轨迹回放。');
              return;
            }
            // C. 场景/工程文件：给出明确的下一步，而不是一句"格式不对"
            if (/silkworm-habitat\/|silkworm-led-scene/.test(prof.type || '')) {
              toast('这是场地/母版场景文件：用「打开工程」或在场地里「导入场景」来载入，不是织网单元的指纹。', 'err');
              return;
            }
            throw new Error('文件里既没有 curves3d/trajectories 点列，也不是 silkworm-motion-profile/v1');
          } catch (err) {
            toast('读取失败：' + err.message + '。可用：①描图器顶栏「导出 JSON」的 curves3d ②trajectories.json（x_mm/y_mm）③P0 脚本的运动指纹（schema=silkworm-motion-profile/v1，界面不导出）。', 'err');
          }
          profileFile.value = '';
        };
        reader.readAsText(f, 'utf-8');
      });
    }
    document.getElementById('habAdjCenter').addEventListener('click', () => {
      const a = chosen(); if (!a) return;
      if (a.kind === 'route') { a.offX = 0; a.offY = 0; a.rot = 0; a.scale = 1; a.u = 0; applyRouteTransform(a); }
      else if (!blocked(0, 0)) { a.x = 0; a.y = 0; }
      renderList();
    });
    const habDeleteUnitBtn = document.getElementById('habDeleteUnit');
    if (habDeleteUnitBtn) habDeleteUnitBtn.addEventListener('click', () => {
      const a = (habitat.weaveEdit && habitat.weaveEdit.agentId)
        ? habitat.agents.find(x => x.id === habitat.weaveEdit.agentId)
        : chosen();
      deleteWeaveUnit(a);
    });
    document.getElementById('habAdjDrop').addEventListener('click', () => {
      const a = chosen(); if (!a) return;
      pushUndo();
      const label = a.kind === 'route' ? ('蚕 ' + a.wormId) : (a.kind === 'weave' ? ('织网单元 ' + a.id) : a.id);
      habitat.agents = habitat.agents.filter(x => x.id !== a.id);
      habitat.selected = null;
      renderList();
      toast('已移除「' + label + '」。剩下 ' + habitat.agents.filter(x => x.kind === 'weave').length + ' 块织网单元、' +
        habitat.agents.filter(x => x.kind === 'route').length + ' 只蚕。', 'ok');
    });
  }

  function step(dt) {
    const env = drive();
    habitat.agents.forEach(agent => {
      if (agent.mode !== 'run') return;
      if (agent.kind === 'weave') {
        const dur = Number.isFinite(agent.duration) && agent.duration > 0 ? agent.duration : 22;
        const sp = Number.isFinite(agent.speedScale) ? agent.speedScale : 1;
        agent.u = Math.min(1, (agent.u || 0) + dt / dur * sp);
        if (agent.u >= 1) agent.mode = 'idle';
        return;
      }
      if (agent.kind === 'route') {
        if (agent.follow && agent.route && agent.route.length >= 2) {
          const speedScale = Number.isFinite(agent.speedScale) ? agent.speedScale : 1;
          // 「沿丝路重复」：数值越大，蚕越在同一片区域反复走同一条大路径 → 那条路径被走得更密
          const boost = Math.max(1, Math.min(6, Number.isFinite(habitat.pathBoost) ? habitat.pathBoost : 1));
          // 真实吐丝形态（局部） + 场地巡游（整体）：蚕一路爬过整个场地，边爬边重复实测笔迹
          agent.u = (agent.u + dt * 0.18 * speedScale * boost) % 1;
          agent.travel = (agent.travel || 0) + dt * 0.075 * speedScale / Math.sqrt(boost);
          const g = roamPoint(agent, agent.travel);
          const l = sampleRouteCentered(agent, agent.u);
          // 格内活动时，这一笔的尺寸跟着格子走（≈1/3 格宽），不会画成一整个场地的巨型八字
          let sc = (agent.scale || 1) * 0.6;
          let unit = null;
          if (agent.scope === 'cell') {
            unit = weaveUnitFor(agent);
            // 一格里的这一趟吐丝：单次实测笔迹约占格子短边的七成（真实样本 bbox≈0.95×1.16 格），留出巡游余量
            const wormSize = Number.isFinite(habitat.wormSize) ? habitat.wormSize : 1;
            if (unit) sc = Math.min(unit.w, unit.h) * 0.72 / 110 * (agent.scale || 1) * wormSize;
          }
          const cs = Math.cos(agent.rot || 0), sn = Math.sin(agent.rot || 0);
          const lx = l.x * sc, ly = l.y * sc;
          let x = g.x + lx * cs - ly * sn;
          let y = g.y + lx * sn + ly * cs;
          if (unit) {
            // 再兜一层：不管笔迹怎么摆，落点都压在格子里（留 6% 边距）
            const mx = unit.w * 0.47, my = unit.h * 0.47;
            x = Math.max(unit.x - mx, Math.min(unit.x + mx, x));
            y = Math.max(unit.y - my, Math.min(unit.y + my, y));
            // 壁当作实体：撞到壁就贴着壁滑开，看起来像"绕过去"，而不是线被穿过去
            const sizeK = Math.max(0.5, Math.min(2.4,
              (Number.isFinite(habitat.wormSize) ? habitat.wormSize : 1) * (Number.isFinite(agent.scale) ? agent.scale : 1)));
            const q = pushOutOfWalls(unit, x, y, 7 * sizeK);
            if (q.pushed) {
              const dx = q.x - x, dy = q.y - y;
              const n = Math.hypot(dx, dy) || 1e-6;
              // 每帧最多挪 1.4×体型：避免"啪"一下瞬移（那就是抖）
              const cap = Math.max(0.8, 1.4 * sizeK);
              const k = Math.min(1, cap / n);
              // 被推开的同时顺着壁滑一点，读起来是"擦着壁绕过去"
              const tx = -dy / n, ty = dx / n;
              const sgn = Math.sign(tx * Math.cos(agent.heading) + ty * Math.sin(agent.heading)) || 1;
              x += dx * k + sgn * tx * cap * 0.45;
              y += dy * k + sgn * ty * cap * 0.45;
            }
          }
          const px = agent.x, py = agent.y;
          agent.x = x;
          agent.y = y;
          if (Math.hypot(x - px, y - py) > 0.4) agent.heading = Math.atan2(y - py, x - px);
          const lastPt = agent.silk[agent.silk.length - 1];
          if (!lastPt || Math.hypot(lastPt.x - x, lastPt.y - y) > 2.2) {
            agent.silk.push({ x, y, t: habitat.simTime });
            if (agent.silk.length > 6000) agent.silk.shift();
          }
        }
        return;
      }
      const rand = mulberry32((habitat.seed * 1000 + Math.floor(habitat.simTime * 20) + agent.id.length * 17) >>> 0);
      if (performance.now() < agent.pauseUntil) return;
      if (rand() < env.pauseChance * dt) {
        agent.pauseUntil = performance.now() + 500 + rand() * 700;
        return;
      }
      agent.phase += dt * (0.8 + env.sway);
      const turn = Math.sin(agent.phase) * env.sway * dt * agent.turnSign;
      agent.heading += Math.max(-1.2 * dt, Math.min(1.2 * dt, turn));
      const speedScale = Number.isFinite(agent.speedScale) ? agent.speedScale : 1;
      const actualSpeed = env.speed * speedScale;
      const nx = agent.x + Math.cos(agent.heading) * actualSpeed * dt;
      const ny = agent.y + Math.sin(agent.heading) * actualSpeed * dt;
      if (!blocked(nx, ny)) {
        agent.x = nx;
        agent.y = ny;
        const last = agent.silk[agent.silk.length - 1];
        if (!last || Math.hypot(last.x - nx, last.y - ny) > 1.2) {
          agent.silk.push({ x: nx, y: ny, t: habitat.simTime });
        }
      } else {
        agent.heading += agent.turnSign * 1.6 * dt;
      }
    });
  }

  let last = 0;
  function frame(ts) {
    const dt = Math.min(0.05, last ? (ts - last) / 1000 : 0.016);
    last = ts;
    if (habitat.agents.some(a => a.mode === 'run')) {
      habitat.runningClock = true;
      habitat.simTime += dt;
      step(dt);
    }
    paintMist();
    paintWorld();
    renderDrive();
    requestAnimationFrame(frame);
  }

  world.addEventListener('pointerdown', (ev) => {
    if (ev.button === 1 || ev.shiftKey || habViewport.panMode) {
      habitat.drag = {
        kind: 'pan',
        x: ev.clientX,
        y: ev.clientY,
        panX: habViewport.panX,
        panY: habViewport.panY,
      };
      world.setPointerCapture(ev.pointerId);
      world.classList.add('panning');
      ev.preventDefault();
      return;
    }
    const p = screenToHab(ev);
    // 按轮廓新建：点几下画出外框顶点，双击封闭后建单元
    if (habitat.newOutline) {
      habitat.newOutline.push({ x: p.x, y: p.y });
      hint('已点 ' + habitat.newOutline.length + ' 个顶点；再点继续，双击封闭并新建单元（Esc 取消）。');
      return;
    }
    // 织网形状编辑：先命中手柄（移动/缩放/顶点），否则点空白加顶点
    if (habitat.weaveEdit && habitat.weaveEdit.agentId) {
      const a = habitat.agents.find(x => x.id === habitat.weaveEdit.agentId);
      if (a && a.kind === 'weave') {
        const e = habitat.weaveEdit;
        // 先判断有没有点到"另一块"：点到另一块就整块切过去（不再把这一下当成画点）
        const otherUnit = habitat.agents.find(z => z.kind === 'weave' && z.id !== a.id &&
          Math.abs(z.x - p.x) <= z.w / 2 && Math.abs(z.y - p.y) <= z.h / 2);
        if (otherUnit) {
          const key0 = e.ix + ',' + e.iy;
          if (e.mode && (weaveEditDraft(e, key0) || []).length >= 2) finishWeaveEditLine();
          if (window.__weaveHooks && window.__weaveHooks.enter) window.__weaveHooks.enter(otherUnit.id);
          return;
        }
        const v = view();
        const tol = 14 / v.s;
        const hs = weaveHandles(a, e.ix, e.iy);
        // 缺口工具下把抓取半径放大（白点小、又贴着曲线，手要够得着）
        const tol2 = (e.tool === 'notch') ? 22 / v.s : tol;
        const hit = hs.find(h => Math.hypot(h.x - p.x, h.y - p.y) <= tol2);
        if (hit) {
          if (ev.altKey && deleteWeaveHandleVertex(hit)) return;
          pushUndo();
          habitat.drag = { kind: 'weaveHandle', handle: hit };
          try { world.setPointerCapture(ev.pointerId); } catch (_) { /* 合成事件无 pointer id */ }
          syncEditNote();
          return;
        }
        if (e.mode === 'outline') {
          e.outlinePts = e.outlinePts || [];
          e.outlinePts.push({ x: p.x, y: p.y });
          syncEditNote();
          return;
        }
        // 形状 / 孔洞 / 缺口：不画线，只认拖手柄；点空白按工具语义挪孔或缺口
        if (!e.mode) {
          if (e.tool === 'hole') {
            pushUndo();
            const sh = ensureShapeOverride(a, 0, 0);
            if (!sh.islands || !sh.islands.length) sh.islands = [{ cx: 0, cy: 0, r: Math.min(a.w, a.h) * 0.26 }];
            sh.islands[0].cx = Math.max(-a.w / 2, Math.min(a.w / 2, p.x - a.x));
            sh.islands[0].cy = Math.max(-a.h / 2, Math.min(a.h / 2, p.y - a.y));
            if (a.cache && a.cache.delete) a.cache.delete('0,0');
            weaveCellContent(a, 0, 0);
            syncEditNote();
            toast('孔洞已移到你点的地方。', 'ok');
            return;
          }
          if (e.tool === 'notch') {
            pushUndo();
            const sh = ensureShapeOverride(a, 0, 0);
            if (!sh.notch) sh.notch = { cx: 0, cy: 0, r: Math.min(a.w, a.h) * 0.34 };
            sh.notch.cx = Math.max(-a.w / 2, Math.min(a.w / 2, p.x - a.x));
            sh.notch.cy = Math.max(-a.h / 2, Math.min(a.h / 2, p.y - a.y));
            if (a.cache && a.cache.delete) a.cache.delete('0,0');
            weaveCellContent(a, 0, 0);
            syncEditNote();
            toast('缺口已移到你点的地方。', 'ok');
            return;
          }
          hint('要加壁或丝路，先点上面的「加壁」/「加丝路」，再在格子里点顶点。');
          return;
        }
        const c = weaveCellAt(a, p);
        if (!a.tileField) {
          const inside = Math.abs(p.x - a.x) <= a.w / 2 && Math.abs(p.y - a.y) <= a.h / 2;
          if (!inside) {
            // 点到格外：正在画的那一笔先收尾
            const key0 = e.ix + ',' + e.iy;
            if (e.mode && (weaveEditDraft(e, key0) || []).length >= 2) finishWeaveEditLine();
            // 点到的是另一块：直接切到那一块继续编辑；点的是纯空白才退出
            const other = habitat.agents.find(z => z.kind === 'weave' &&
              Math.abs(z.x - p.x) <= z.w / 2 && Math.abs(z.y - p.y) <= z.h / 2);
            if (other && other.id !== a.id && window.__weaveHooks && window.__weaveHooks.enter) {
              window.__weaveHooks.enter(other.id);
              return;
            }
            if (window.__weaveHooks && window.__weaveHooks.exit) window.__weaveHooks.exit();
            return;
          }
          e.ix = 0; e.iy = 0;
        } else if (e.ix !== c.ix || e.iy !== c.iy) { e.ix = c.ix; e.iy = c.iy; }
        const ek = e.ix + ',' + e.iy;
        const dr = weaveEditDraft(e, ek);
        if (e.mode === 'notch') {
          const sh2 = (a.custom && a.custom.shapes && a.custom.shapes[ek]) || null;
          const pts2 = (sh2 && sh2.notchPts && sh2.notchPts.length >= 3) ? sh2.notchPts
            : ((weaveCellContent(a, e.ix, e.iy).cell || {}).notchPts || null);
          // 已经有缺口、还没在重画：点在这条线上＝就地插一个锚点（平面软件的老规矩）
          if (pts2 && pts2.length >= 3 && !dr.length) {
            const ox2 = a.x + e.ix * a.w, oy2 = a.y + e.iy * a.h;
            let bi = -1, bd = Infinity, bt = 0.5;
            for (let i = 0; i < pts2.length; i++) {
              const q0 = pts2[i], q1 = pts2[(i + 1) % pts2.length];
              const ax2 = ox2 + q0.x, ay2 = oy2 + q0.y, bx2 = ox2 + q1.x, by2 = oy2 + q1.y;
              const ex = bx2 - ax2, ey = by2 - ay2, L2 = ex * ex + ey * ey || 1;
              let t2 = ((p.x - ax2) * ex + (p.y - ay2) * ey) / L2;
              t2 = Math.max(0, Math.min(1, t2));
              const dd = Math.hypot(p.x - (ax2 + ex * t2), p.y - (ay2 + ey * t2));
              if (dd < bd) { bd = dd; bi = i; bt = t2; }
            }
            let near = Infinity;
            pts2.forEach(q => { near = Math.min(near, Math.hypot(p.x - (ox2 + q.x), p.y - (oy2 + q.y))); });
            if (bd <= 24 / view().s && near > 10 / view().s) {
              pushUndo();
              const sh = ensureShapeOverride(a, e.ix, e.iy);
              const arr = (sh.notchPts && sh.notchPts.length >= 3) ? sh.notchPts : pts2.map(v2 => ({ x: v2.x, y: v2.y }));
              sh.notchPts = arr;
              if (sh.notch) delete sh.notch;
              const q0 = arr[bi], q1 = arr[(bi + 1) % arr.length];
              arr.splice(bi + 1, 0, {
                x: q0.x + (q1.x - q0.x) * bt,
                y: q0.y + (q1.y - q0.y) * bt,
              });
              if (a.cache && a.cache.delete) a.cache.delete(ek);
              weaveCellContent(a, e.ix, e.iy);
              // 插完直接进入"拖这个新锚点"，手感跟钢笔工具一样顺
              habitat.drag = { kind: 'weaveHandle', handle: { kind: 'notchV', vi: bi + 1 } };
              syncEditNote();
              hint('在这条线上加了一个锚点，现在直接拖动它就能微调。');
              return;
            }
            hint('点在缺口的"线"上才会加锚点；拖白点改形状，想推倒重画点「重画缺口」。');
            return;
          }
          if (dr.length && Math.hypot(dr[dr.length - 1].x - c.lx, dr[dr.length - 1].y - c.ly) < 12) return;
        }
        dr.push({ x: c.lx, y: c.ly });
        syncEditNote();
        return;
      }
    }
    const hit = habitat.agents.find(a => {
      if (a.mode === 'bench') return false;
      if (a.kind === 'weave') {
        return Math.abs(a.x - p.x) <= a.w / 2 && Math.abs(a.y - p.y) <= a.h / 2;
      }
      return Math.hypot(a.x - p.x, a.y - p.y) < 16;
    });
    if (!hit) {
      // 点场地空白 = 退出这一格的编辑（不用再去找「退出编辑」按钮）
      if (habitat.weaveEdit && habitat.weaveEdit.agentId && window.__weaveHooks && window.__weaveHooks.exit) {
        window.__weaveHooks.exit();
      }
      return;
    }
    selectAgent(hit.id);
    // 点到某一块：直接把编辑切到这一块，不必先选再点「编辑这一格」
    if (hit.kind === 'weave' && (!habitat.weaveEdit || habitat.weaveEdit.agentId !== hit.id)) {
      if (window.__weaveHooks && window.__weaveHooks.enter) window.__weaveHooks.enter(hit.id);
    }
    habitat.drag = { kind: 'agent', id: hit.id, modeBefore: hit.mode === 'drag' ? 'idle' : hit.mode, x0: hit.x, y0: hit.y };
    hit.mode = 'drag';
    renderList();
    world.setPointerCapture(ev.pointerId);
  });

  // 壁是实体：把落在壁附近的点沿法线推开，蚕就"绕"着壁走（不用改巡游数学）
  function pushOutOfWalls(unit, x, y, margin) {
    if (!unit || !unit.custom || !unit.custom.walls) return { x, y, pushed: false };
    const list = (unit.custom.walls && unit.custom.walls['0,0']) || [];
    let px = x, py = y, pushed = false;
    list.forEach(line => {
      const pts = line.pts || line;
      for (let k = 1; k < pts.length; k++) {
        const ax = unit.x + pts[k - 1].x, ay = unit.y + pts[k - 1].y;
        const bx = unit.x + pts[k].x, by = unit.y + pts[k].y;
        const d = distToSeg(px, py, ax, ay, bx, by);
        if (d < margin) {
          const ex = bx - ax, ey = by - ay;
          const L = Math.hypot(ex, ey) || 1;
          const nx = -ey / L, ny = ex / L;
          const side = ((px - ax) * ey - (py - ay) * ex) >= 0 ? 1 : -1;
          const push = margin - d;
          px += nx * side * push;
          py += ny * side * push;
          pushed = true;
        }
      }
    });
    return { x: px, y: py, pushed };
  }

  // 右键删除：手柄/顶点（孔洞、缺口、壁顶点、丝路顶点）或整条壁/丝路/整个缺口
  function distToSeg(px, py, ax, ay, bx, by) {
    const dx = bx - ax, dy = by - ay;
    const L2 = dx * dx + dy * dy || 1;
    const t = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / L2));
    return Math.hypot(px - (ax + dx * t), py - (ay + dy * t));
  }

  function weaveDeleteAt(p) {
    const e = habitat.weaveEdit;
    if (!e || !e.agentId) return false;
    const a = habitat.agents.find(x => x.id === e.agentId);
    if (!a || a.kind !== 'weave') return false;
    const v = view();
    const tol = 16 / v.s;
    const key = e.ix + ',' + e.iy;
    const ox = a.x + e.ix * a.w, oy = a.y + e.iy * a.h;
    const hs = weaveHandles(a, e.ix, e.iy);
    // 右键优先认"能删的东西"：孔洞/缺口/壁顶点/丝路顶点/外框顶点，
    // 而不是同一位置上不可删的整块挪动十字
    const delKinds = { islandMove: 3, islandR: 3, notchMove: 3, notchR: 3, notchV: 3, wallV: 2, pathV: 2, outlineV: 2, outlineMid: 1 };
    const cand = hs
      .map(h => ({ h, d: Math.hypot(h.x - p.x, h.y - p.y) }))
      .filter(o => o.d <= tol && delKinds[o.h.kind])
      .sort((x, y) => (delKinds[y.h.kind] - delKinds[x.h.kind]) || (x.d - y.d));
    const hit = cand.length ? cand[0].h : null;
    if (hit) {
      if (hit.kind === 'islandMove' || hit.kind === 'islandR') {
        pushUndo();
        const sh = ensureShapeOverride(a, e.ix, e.iy);
        if (sh.islands && sh.islands[hit.i]) {
          sh.islands.splice(hit.i, 1);
          if (a.cache && a.cache.delete) a.cache.delete(key);
          weaveCellContent(a, e.ix, e.iy);
          syncEditNote();
          toast('已删掉这个孔洞。想再加就选「孔洞」工具点一下。', 'ok');
        }
        return true;
      }
      if (hit.kind === 'notchMove' || hit.kind === 'notchR') {
        pushUndo();
        const sh = ensureShapeOverride(a, e.ix, e.iy);
        if (sh.notch) {
          delete sh.notch;
          if (a.cache && a.cache.delete) a.cache.delete(key);
          weaveCellContent(a, e.ix, e.iy);
          syncEditNote();
          toast('已删掉这个缺口。', 'ok');
        }
        return true;
      }
      if (deleteWeaveHandleVertex(hit)) return true;
    }
    // 右键按在壁 / 丝路的线上：删掉整条
    const buckets = [
      { lines: (a.custom && a.custom.walls && a.custom.walls[key]) || [], type: 'wall', name: '壁' },
      { lines: (a.custom && a.custom.paths && a.custom.paths[key]) || [], type: 'path', name: '丝路' },
    ];
    for (const b of buckets) {
      for (let i = 0; i < b.lines.length; i++) {
        const line = b.lines[i];
        const pts = line.pts || line;
        for (let k = 1; k < pts.length; k++) {
          if (distToSeg(p.x, p.y, ox + pts[k - 1].x, oy + pts[k - 1].y, ox + pts[k].x, oy + pts[k].y) <= tol) {
            pushUndo();
            b.lines.splice(i, 1);
            if (!b.lines.length) delete (b.type === 'wall' ? a.custom.walls : a.custom.paths)[key];
            if (a.cache && a.cache.delete) a.cache.delete(key);
            weaveCellContent(a, e.ix, e.iy);
            syncEditNote();
            toast('已删掉这一条' + b.name + '。', 'ok');
            return true;
          }
        }
      }
    }
    // 右键按在缺口里（没压到手柄）：删掉缺口
    const c = weaveCellContent(a, e.ix, e.iy);
    if (Array.isArray(c.cell.notchPts) && c.cell.notchPts.length >= 3) {
      const np = weaveNotchCurve(c.cell.notchPts).map(q => ({ x: q.x + ox, y: q.y + oy }));
      if (weaveInPoly(np, p.x, p.y) || weavePolyDist(np, p.x, p.y) <= tol) {
        pushUndo();
        const sh = ensureShapeOverride(a, e.ix, e.iy);
        if (sh.notchPts) {
          delete sh.notchPts;
          if (a.cache && a.cache.delete) a.cache.delete(key);
          weaveCellContent(a, e.ix, e.iy);
          syncEditNote();
          toast('已删掉这个缺口。', 'ok');
        }
        return true;
      }
    }
    if (c.cell && c.cell.notch) {
      const nt = c.cell.notch;
      if (Math.hypot(p.x - (ox + nt.cx), p.y - (oy + nt.cy)) <= nt.r) {
        pushUndo();
        const sh = ensureShapeOverride(a, e.ix, e.iy);
        if (sh.notch) {
          delete sh.notch;
          if (a.cache && a.cache.delete) a.cache.delete(key);
          weaveCellContent(a, e.ix, e.iy);
          syncEditNote();
          toast('已删掉这个缺口。', 'ok');
        }
        return true;
      }
    }
    hint('右键任意位置都会开菜单；压到锚点 / 孔 / 缺口时，菜单第一项就是「删除这个锚点」「删除整个缺口」。');
    return false;
  }

  // 右键菜单：点格内空白处弹出「这一格能做什么」，点到可删的东西时仍然右键=删
  // 菜单节点在脚本之后才被解析，这里必须每次现查，不能提前缓存
  const getCtxMenu = () => document.getElementById('habCtxMenu');
  function hideCtxMenu() { const el = getCtxMenu(); if (el) el.style.display = 'none'; }
  function showCtxMenu(clientX, clientY, items) {
    const el = getCtxMenu();
    if (!el) return;
    el.innerHTML = '<div class="ctx-title">这一格：</div>';
    items.forEach(it => {
      const b = document.createElement('button');
      b.type = 'button';
      b.textContent = it.label;
      if (it.danger) b.className = 'danger';
      b.addEventListener('click', () => {
        hideCtxMenu();
        try { it.run(); } catch (err) { console.warn(err); }
      });
      el.appendChild(b);
    });
    el.style.display = 'block';
    el.style.left = Math.max(8, Math.min(clientX, window.innerWidth - 224)) + 'px';
    // 菜单项会越来越多，按真实高度夹住，别掉到屏幕外面
    const mh = el.offsetHeight || 320;
    el.style.top = Math.max(8, Math.min(clientY, window.innerHeight - mh - 12)) + 'px';
  }
  window.addEventListener('pointerdown', (ev) => {
    const el = getCtxMenu();
    if (el && el.style.display === 'block' && !el.contains(ev.target)) hideCtxMenu();
  }, true);
  window.addEventListener('keydown', (ev) => { if (ev.key === 'Escape') hideCtxMenu(); });

  world.addEventListener('contextmenu', (ev) => {
    const p = screenToHab(ev);
    // 没在编辑：右键点某一块 = 直接进这一块的编辑，再弹菜单
    if (!habitat.weaveEdit || !habitat.weaveEdit.agentId) {
      const hit0 = habitat.agents.find(z => z.kind === 'weave' &&
        Math.abs(z.x - p.x) <= z.w / 2 && Math.abs(z.y - p.y) <= z.h / 2);
      if (!hit0) return;
      ev.preventDefault();
      if (window.__weaveHooks && window.__weaveHooks.enter) window.__weaveHooks.enter(hit0.id);
    } else {
      ev.preventDefault();
      const a0 = habitat.agents.find(z => z.kind === 'weave' &&
        Math.abs(z.x - p.x) <= z.w / 2 && Math.abs(z.y - p.y) <= z.h / 2);
      if (!a0) { hideCtxMenu(); return; }
      if (a0.id !== habitat.weaveEdit.agentId && window.__weaveHooks && window.__weaveHooks.enter) {
        window.__weaveHooks.enter(a0.id);
      }
    }
    const a = weaveEditAgent();
    const e = habitat.weaveEdit;
    if (!a || !e) return;
    // 让 e.ix/e.iy 对准右键点所在的格
    const ci = weaveCellAt(a, p);
    e.ix = ci.ix; e.iy = ci.iy;
    const lx = ci.lx, ly = ci.ly;
    // 右键压在哪个可删的东西上：不立刻删，先把"删什么"做成菜单项
    const v = view();
    const tol = 16 / v.s;
    const delKinds = { islandMove: 3, islandR: 3, notchMove: 3, notchR: 3, notchV: 3, wallV: 2, pathV: 2, outlineV: 2, outlineMid: 1 };
    let hit = null, hd = Infinity, hw = 0;
    weaveHandles(a, e.ix, e.iy).forEach(h => {
      if (!delKinds[h.kind]) return;
      const d = Math.hypot(h.x - p.x, h.y - p.y);
      if (d > tol) return;
      const wgt = delKinds[h.kind];
      if (wgt > hw || (wgt === hw && d < hd)) { hw = wgt; hd = d; hit = h; }
    });
    const deleteWholeNotch = () => {
      pushUndo();
      const sh = ensureShapeOverride(a, e.ix, e.iy);
      delete sh.notchPts;
      delete sh.notch;
      if (a.cache && a.cache.delete) a.cache.delete(e.ix + ',' + e.iy);
      weaveCellContent(a, e.ix, e.iy);
      syncEditNote();
      toast('这一格的缺口整个删掉了。', 'ok');
    };
    const deleteIsland = (i) => {
      pushUndo();
      const sh = ensureShapeOverride(a, e.ix, e.iy);
      if (sh.islands && sh.islands[i]) {
        sh.islands.splice(i, 1);
        if (a.cache && a.cache.delete) a.cache.delete(e.ix + ',' + e.iy);
        weaveCellContent(a, e.ix, e.iy);
        syncEditNote();
        toast('这个孔删掉了。', 'ok');
      }
    };
    const hitItems = [];
    if (hit) {
      if (hit.kind === 'notchV') {
        hitItems.push({ label: '删除这个锚点', danger: true, run: () => { deleteWeaveHandleVertex(hit); } });
        hitItems.push({ label: '删除整个缺口', danger: true, run: deleteWholeNotch });
      } else if (hit.kind === 'notchMove' || hit.kind === 'notchR') {
        hitItems.push({ label: '删除整个缺口', danger: true, run: deleteWholeNotch });
      } else if (hit.kind === 'islandMove' || hit.kind === 'islandR') {
        hitItems.push({ label: '删除这个孔', danger: true, run: () => deleteIsland(hit.i) });
      } else {
        hitItems.push({ label: '删除这个锚点', danger: true, run: () => { deleteWeaveHandleVertex(hit); } });
      }
    }
    showCtxMenu(ev.clientX, ev.clientY, hitItems.concat([
      { label: '添加孔洞（放在这一点）', run: () => {
          pushUndo();
          const sh = ensureShapeOverride(a, e.ix, e.iy);
          if (!sh.islands || !sh.islands.length) sh.islands = [{ cx: 0, cy: 0, r: Math.min(a.w, a.h) * 0.26 }];
          sh.islands[0].cx = lx; sh.islands[0].cy = ly;
          if (a.cache && a.cache.delete) a.cache.delete(e.ix + ',' + e.iy);
          weaveCellContent(a, e.ix, e.iy); syncEditNote();
          toast('孔已开在你点的地方，拖青圈可改大小。', 'ok');
        } },
      { label: '添加缺口（放在这一点）', run: () => {
          pushUndo();
          const sh = ensureShapeOverride(a, e.ix, e.iy);
          // 立刻给一个看得见的缺口，再让你拖点改形（不是"点了没反应"）
          const rr = Math.max(40, Math.min(a.w, a.h) * 0.2);
          const pts0 = [];
          for (let i = 0; i < 6; i++) {
            const ang = (Math.PI * 2 / 6) * i - Math.PI / 2;
            pts0.push({ x: lx + Math.cos(ang) * rr * 1.08, y: ly + Math.sin(ang) * rr });
          }
          sh.notchPts = pts0;
          if (sh.notch) delete sh.notch;
          if (a.cache && a.cache.delete) a.cache.delete(e.ix + ',' + e.iy);
          weaveCellContent(a, e.ix, e.iy);
          setWeaveTool('notch');
          syncEditNote();
          toast('缺口已经放在你点的地方：拖白点改形状，点线上就加锚点，右键可删。', 'ok');
        } },
      { label: '重画缺口（点几下围一圈）', run: () => {
          pushUndo();
          const sh = ensureShapeOverride(a, e.ix, e.iy);
          delete sh.notchPts; delete sh.notch;
          if (a.cache && a.cache.delete) a.cache.delete(e.ix + ',' + e.iy);
          weaveCellContent(a, e.ix, e.iy);
          setWeaveTool('notch');
          e.mode = 'notch'; e.drafts = {};
          syncEditNote();
          hint('在格内连点几下围出形状，双击收尾（至少 3 点）。');
        } },
      { label: '添加壁（从这里起笔）', run: () => {
          setWeaveTool('wall');
          e.mode = 'wall';
          const dr = weaveEditDraft(e, e.ix + ',' + e.iy);
          dr.push({ x: lx, y: ly });
          syncEditNote();
          hint('接着点，双击收尾。壁是曲线，只挡蚕不显示在成品里。');
        } },
      { label: '添加丝路（从这里起笔）', run: () => {
          setWeaveTool('path');
          e.mode = 'path';
          const dr = weaveEditDraft(e, e.ix + ',' + e.iy);
          dr.push({ x: lx, y: ly });
          syncEditNote();
          hint('接着点，双击收尾。蚕会顺着这条线走。');
        } },
      { label: '重设整块外框（点几下围一圈）', run: () => {
          setWeaveTool('outline');
          e.mode = 'outline';
          e.outlinePts = [{ x: p.x, y: p.y }];
          syncEditNote();
          hint('绕着这一块点一圈，双击收尾，整块外形就换成你画的了。');
        } },
      { label: '清掉这一格的形状（孔/缺口/壁/丝路）', danger: true, run: () => {
          pushUndo();
          clearWeaveCellCustom(a, e.ix, e.iy);
          syncEditNote();
          toast('这一格回到默认形状。', 'ok');
        } },
      { label: '删除这一块织网单元（整块消失）', danger: true, run: () => {
          if (window.__weaveHooks && window.__weaveHooks.deleteUnit) window.__weaveHooks.deleteUnit(a.id);
        } },
      { label: '退出编辑', run: () => { if (window.__weaveHooks && window.__weaveHooks.exit) window.__weaveHooks.exit(); } },
    ]));
  });

  world.addEventListener('pointermove', (ev) => {
    const d = habitat.drag;
    if (!d) {
      // 不在拖拽时：光标停在手柄上就高亮 + 顺手提示"拖这里改什么"
      const e = habitat.weaveEdit;
      if (e && e.agentId) {
        const a = habitat.agents.find(x => x.id === e.agentId);
        if (a && a.kind === 'weave') {
          const p = screenToHab(ev);
          const v = view();
          const tol = (e.tool === 'notch') ? 18 / v.s : 12 / v.s;
          const hs = weaveHandles(a, e.ix, e.iy);
          let best = null, bd = tol;
          hs.forEach(h => {
            const dd = Math.hypot(h.x - p.x, h.y - p.y);
            if (dd < bd) { bd = dd; best = h; }
          });
          habitat.hoverHandle = best;
          world.style.cursor = best ? 'grab' : '';
        }
      } else if (habitat.hoverHandle) {
        habitat.hoverHandle = null;
        world.style.cursor = '';
      }
      return;
    }
    if (d.kind === 'pan') {
      habViewport.panX = d.panX + ev.clientX - d.x;
      habViewport.panY = d.panY + ev.clientY - d.y;
      return;
    }
    if (d.kind === 'weaveHandle') {
      applyWeaveHandleDrag(d.handle, screenToHab(ev));
      syncEditNote();
      return;
    }
    const p = screenToHab(ev);
    const agent = habitat.agents.find(a => a.id === d.id);
    if (!agent) return;
    if (!blocked(p.x, p.y)) {
      if (agent.kind === 'route') { agent.offX = p.x; agent.offY = p.y; applyRouteTransform(agent); }
      else { agent.x = p.x; agent.y = p.y; }
    }
  });

  world.addEventListener('dblclick', () => {
    if (habitat.newOutline) { finishOutlineUnit(); return; }
    if (habitat.weaveEdit && habitat.weaveEdit.agentId) finishWeaveEditLine();
  });

  world.addEventListener('pointerup', () => {
    const d = habitat.drag;
    if (!d) return;
    if (d.kind === 'pan') {
      habitat.drag = null;
      world.classList.remove('panning');
      return;
    }
    if (d.kind === 'weaveHandle') {
      habitat.drag = null;
      syncRoutePanel();
      return;
    }
    if (d.kind !== 'agent') return;
    habitat.drag = null;
    const agent = habitat.agents.find(a => a.id === d.id);
    if (!agent) return;
    agent.mode = d.modeBefore === 'run' ? 'paused' : (d.modeBefore === 'bench' ? 'idle' : d.modeBefore);
    if (agent.mode === 'bench') agent.mode = 'idle';
    const moved = Math.hypot(agent.x - d.x0, agent.y - d.y0) > 2;
    if (moved) hint('已移动「' + (agent.kind === 'route' ? '蚕 ' + agent.wormId : agent.id) + '」；右侧滑杆可精确微调。');
    renderList();
  });

  function updateGhost(ev, agent) {
    if (!ghost) return;
    if (!agent) { ghost.style.display = 'none'; return; }
    const label = agent.kind === 'route' ? '蚕 ' + agent.wormId : agent.id;
    const rect = world.getBoundingClientRect();
    const inside = ev.clientX >= rect.left && ev.clientX <= rect.right && ev.clientY >= rect.top && ev.clientY <= rect.bottom;
    const ok = inside && !blocked(screenToHab(ev).x, screenToHab(ev).y);
    ghost.textContent = ok ? '松手放到「' + label + '」处' : (inside ? '这里被桑叶或边界挡住' : '拖到场地里松手');
    ghost.className = ok ? 'canDrop' : (inside ? 'noDrop' : '');
    ghost.style.display = 'block';
    ghost.style.left = ev.clientX + 'px';
    ghost.style.top = ev.clientY + 'px';
    world.classList.toggle('drop-ready', ok);
    world.classList.toggle('drop-fail', inside && !ok);
  }

  function clearGhost() {
    if (ghost) { ghost.style.display = 'none'; ghost.className = ''; }
    world.classList.remove('drop-ready', 'drop-fail');
  }

  document.getElementById('habAgents').addEventListener('pointerdown', (ev) => {
    const btn = ev.target.closest('.mini');
    if (!btn) return;
    ev.preventDefault();
    ev.stopPropagation();
    const card = btn.closest('.agent-card');
    const agent = card ? habitat.agents.find(a => a.id === card.dataset.id) : null;
    if (!agent) return;
    if (btn.dataset.act === 'body') agent.hideBody = !agent.hideBody;
    else agent.hideSilk = !agent.hideSilk;
    renderList();
  }, true);

  document.getElementById('habAgents').addEventListener('pointerdown', (ev) => {
    const card = ev.target.closest('.agent-card');
    if (!card) return;
    const agent = habitat.agents.find(a => a.id === card.dataset.id);
    if (!agent) return;
    selectAgent(agent.id);
    habitat.drag = { kind: 'card', id: agent.id };
    hint('按住拖动到场地内松手，即可把这一个体放到该处。');
    updateGhost(ev, agent);
    if (world.setPointerCapture) world.setPointerCapture(ev.pointerId);
  });

  window.addEventListener('pointermove', (ev) => {
    const d = habitat.drag;
    if (!d || d.kind !== 'card') return;
    const agent = habitat.agents.find(a => a.id === d.id);
    updateGhost(ev, agent);
  });

  window.addEventListener('pointerup', (ev) => {
    const d = habitat.drag;
    if (!d || d.kind !== 'card') return;
    habitat.drag = null;
    clearGhost();
    const agent = habitat.agents.find(a => a.id === d.id);
    if (!agent) return;
    const label = agent.kind === 'route' ? '蚕 ' + agent.wormId : agent.id;
    const rect = world.getBoundingClientRect();
    if (ev.clientX < rect.left || ev.clientX > rect.right || ev.clientY < rect.top || ev.clientY > rect.bottom) {
      hint('未放置：请在场地范围内松手。');
      toast('没有放到场地里，「' + label + '」保持原位。', 'err');
      return;
    }
    const p = screenToHab(ev);
    if (blocked(p.x, p.y)) {
      toast('放不进去：该处超出场地边界，换个位置。', 'err');
      hint('该位置不可放置，请换一处。');
      return;
    }
    if (agent.kind === 'route') {
      agent.offX = p.x;
      agent.offY = p.y;
      applyRouteTransform(agent);
      agent.mode = 'idle';
      // 拖进某一格里：直接归这一格（只在格内爬、丝迹裁在格内）
      const hitUnit = habitat.agents.find(u => u.kind === 'weave'
        && p.x > u.x - u.w / 2 && p.x < u.x + u.w / 2
        && p.y > u.y - u.h / 2 && p.y < u.y + u.h / 2);
      if (hitUnit) {
        agent.scope = 'cell';
        agent.homeUnitId = hitUnit.id;
        hitUnit.measuredWorm = agent.wormId != null ? agent.wormId : hitUnit.measuredWorm;
        hitUnit.wormParty = false;
        agent.travel = 0;
        agent.silk = [];      // 从你放下它的这一点重新开始留丝
        toast('「' + label + '」已放进「' + hitUnit.id + '」：从你放下的位置开始爬，只在这一格里。', 'ok');
        hint('拖进格子的蚕按格子大小收住笔迹、丝迹裁在格内；同一种蚕还能用在别的格。');
      } else {
        toast('「' + label + '」已放到该处。', 'ok');
        hint('已放置实测个体；右侧滑杆可继续微调位置、旋转与缩放。');
      }
    } else {
      placeAgent(agent, p.x, p.y);
      toast('「' + label + '」已放入场地。', 'ok');
      hint('已放入。选中后可用右侧滑杆微调。');
    }
    renderList();
    syncRoutePanel();
  });

  document.getElementById('habTemp').addEventListener('input', (e) => { habitat.tempC = parseFloat(e.target.value); });
  document.getElementById('habHum').addEventListener('input', (e) => { habitat.humidity = parseFloat(e.target.value); });
  document.querySelectorAll('[data-shape]').forEach(btn => {
    btn.addEventListener('click', () => {
      habitat.shape = btn.dataset.shape;
      document.querySelectorAll('[data-shape]').forEach(b => b.classList.toggle('active', b === btn));
      habitat.agents.forEach(a => {
        if (a.mode !== 'bench' && blocked(a.x, a.y)) a.mode = 'paused';
      });
    });
  });
  // 桑叶障碍已移除（用户要求删掉桑叶功能）

  function chosen() { return habitat.agents.find(a => a.id === habitat.selected); }

  /* ===== 织网形状编辑：人工创建 / 调整壁与路径 ===== */
  function weaveCellAt(agent, p) {
    const ix = Math.floor((p.x - agent.x) / agent.w + 0.5);
    const iy = Math.floor((p.y - agent.y) / agent.h + 0.5);
    return {
      ix, iy,
      lx: p.x - (agent.x + ix * agent.w),
      ly: p.y - (agent.y + iy * agent.h),
    };
  }

  function weaveEditAgent() {
    const e = habitat.weaveEdit;
    if (!e || !e.agentId) return null;
    const a = habitat.agents.find(x => x.id === e.agentId);
    return a && a.kind === 'weave' ? a : null;
  }

  function weaveEditDraft(e, key) {
    if (!e.drafts) e.drafts = {};
    if (!e.drafts[key]) e.drafts[key] = [];
    return e.drafts[key];
  }

  function syncEditNoteText() {
    const el = document.getElementById('habWeaveEditNote');
    if (!el) return;
    const e = habitat.weaveEdit;
    if (!e || !e.agentId) { el.textContent = '还没进入编辑。先选一块织网单元，点「编辑这一格」。'; return; }
    const tool = e.tool || 'shape';
    if (tool === 'outline') {
      el.textContent = '正在改外框 · 已点 ' + ((e.outlinePts || []).length) + ' 个顶点。双击封闭，就按这个多边形重设整块。';
      return;
    }
    if (tool === 'wall' || tool === 'path') {
      const n = (e.drafts && e.drafts[e.ix + ',' + e.iy] || []).length;
      el.textContent = '正在' + (tool === 'wall' ? '加壁' : '加丝路') + ' · 已点 ' + n + ' 个顶点。每点一下加一个点，双击收尾。';
      return;
    }
    if (tool === 'hole') { el.textContent = '正在改孔洞 · 拖青色实点挪位置、拖青色圈改大小；直接点格内空白也能把孔挪过去。'; return; }
    if (tool === 'notch') { el.textContent = '正在改缺口 · 拖白点＝挪锚点；点在这条缺口的线上＝就地加一个锚点（加完直接能拖）；拖边中间的小方点＝加锚点；右键压到锚点＝删这个锚点/删整个缺口。'; return; }
    el.textContent = '正在改形状 · 拖橙色方点改整块大小、橙色十字挪整块；青色点挪孔、青色圈改孔径。';
  }

  function syncEditNote() { syncEditNoteText(); syncEditHud(); }

  const WT_HINT = {
    shape: '拖四角＝改整块大小 · 拖四条边中点＝只改宽或只改高 · 拖中间十字＝整块挪位 · 拖青点/青圈＝挪孔/改孔径',
    hole: '拖青点＝挪孔 · 拖青圈＝改孔径 · 点格内空白＝把孔挪到那里 · 没有孔时点一下会新建一个孔',
    notch: '拖白点改缺口形状 · 点在线上＝就地加锚点 · 右键＝删点/删整个缺口 · 想重新围一圈：右键菜单「重画缺口」',
    wall: '在格内连点几下画一条壁，双击收尾 · 白点可拖 · Alt+点删顶点',
    path: '在格内连点几下画一条丝路（蚕会沿它走），双击收尾 · 白点可拖 · Alt+点删顶点',
    outline: '连点画出单元外框，双击封闭 · 白点可拖 · Alt+点删顶点',
  };
  const WT_NAME = { shape: '整体形状', hole: '孔洞', notch: '缺口', wall: '壁', path: '丝路', outline: '外框' };

  function weaveEditLiveInfo() {
    const a = weaveEditAgent();
    const e = habitat.weaveEdit;
    if (!a || !e) return '';
    const key = e.ix + ',' + e.iy;
    const sh = (a.custom && a.custom.shapes && a.custom.shapes[key]) || null;
    const islands = (sh && sh.islands) || [];
    const d = habitat.drag;
    if (d && d.kind === 'weaveHandle') {
      const k = d.handle.kind;
      if ((k === 'islandR' || k === 'islandMove') && islands[d.handle.i]) {
        const isl = islands[d.handle.i];
        const rr = Math.round(isl.r * 2);
        return '孔心 (' + Math.round(isl.cx) + ', ' + Math.round(isl.cy) + ') · 直径 ' + rr + ' px';
      }
      if (k === 'notchR' || k === 'notchMove') {
        return '缺口 直径 ' + Math.round((sh && sh.notch ? sh.notch.r : 0) * 2) + ' px';
      }
      if (k === 'unitCorner') return '整块 ' + Math.round(a.w) + ' × ' + Math.round(a.h) + ' px';
      if (k === 'unitMove') return '整块中心 (' + Math.round(a.x) + ', ' + Math.round(a.y) + ')';
      if (k === 'wallV' || k === 'pathV') return '拖动' + (k === 'wallV' ? '壁' : '丝路') + '顶点';
      if (k === 'outlineV') return '拖动外框顶点';
    }
    if (islands.length) return '本格 ' + islands.length + ' 个孔 · 最大 Ø ' + Math.round(Math.max(...islands.map(o => o.r)) * 2) + ' px';
    return '';
  }

  function syncEditHud() {
    const el = document.getElementById('habEditHud');
    if (!el) return;
    const e = habitat.weaveEdit;
    const a = weaveEditAgent();
    if (!e || !a) { el.hidden = true; el.innerHTML = ''; return; }
    const tool = e.tool || 'shape';
    const idx = habitat.agents.filter(x => x.kind === 'weave').findIndex(x => x.id === a.id) + 1;
    const live = weaveEditLiveInfo();
    el.hidden = false;
    el.innerHTML =
      '<span class="hud-tag">编辑中 · 第 ' + idx + ' 块</span>' +
      '<span>工具：' + (WT_NAME[tool] || tool) + '</span>' +
      (live ? '<span class="hud-mono">' + live + '</span>' : '') +
      '<span>' + (WT_HINT[tool] || '') + '</span>' +
      '<span class="hud-note">虚线框和手柄只是编辑辅助，不会出现在成品图或导出的视频里</span>';
  }

  function finishWeaveEditLine() {
    const a = weaveEditAgent();
    const e = habitat.weaveEdit;
    if (!a || !e) { syncEditNote(); return; }
    // 外框轮廓：点完顶点双击封闭，直接把单元改成这个多边形
    if (e.mode === 'outline') {
      const pts = (e.outlinePts || []).slice();
      if (pts.length < 3) { toast('外框至少 3 个顶点。', 'err'); return; }
      pushUndo();
      a.outline = pts.map(p => ({ x: p.x - a.x, y: p.y - a.y }));
      a.shape = 'island';
      if (a.cache && a.cache.clear) a.cache.clear();
      buildWeave(a);
      e.outlinePts = [];
      syncRoutePanel();
      syncEditNote();
      toast('已按 ' + pts.length + ' 个顶点重设单元外框。', 'ok');
      return;
    }
    const key = e.ix + ',' + e.iy;
    const draft = weaveEditDraft(e, key);
    if (e.mode === 'notch') {
      // 缺口：自己点一圈，至少 3 点才算成形（不是只能画圆）
      if (draft.length < 3) { toast('缺口至少要 3 个点，再多点几下就可成形。', 'err'); return; }
      pushUndo();
      const sh = ensureShapeOverride(a, e.ix, e.iy);
      sh.notchPts = draft.map(q => ({ x: q.x, y: q.y }));
      if (sh.notch) delete sh.notch;
      draft.length = 0;
      if (a.cache && a.cache.delete) a.cache.delete(key);
      weaveCellContent(a, e.ix, e.iy);
      a.sample = a.sample || {};
      syncRoutePanel();
      syncEditNote();
      toast('缺口已按你点的 ' + sh.notchPts.length + ' 个点成形（想加/改点，拖边中点或点顶点）。', 'ok');
      return;
    }
    if (!draft.length) { syncEditNote(); return; }
    if (draft.length < 2) { toast('至少两个点才能成线。', 'err'); return; }
    pushUndo();
    a.custom = a.custom || { walls: {}, paths: {}, shapes: {} };
    const bucket = e.mode === 'wall' ? a.custom.walls : a.custom.paths;
    (bucket[key] = bucket[key] || []).push({ pts: draft.slice(), closed: e.mode === 'wall' });
    draft.length = 0;
    if (a.cache && a.cache.delete) a.cache.delete(key);
    weaveCellContent(a, e.ix, e.iy);
    a.sample = a.sample || {};
    if (a.sample.custom != null) a.sample.custom += 1;
    syncRoutePanel();
    syncEditNote();
    toast('已记下这条' + (e.mode === 'wall' ? '壁' : '丝路') + '（格 ' + e.ix + ',' + e.iy + '）。', 'ok');
  }

  function clearWeaveCellCustom() {
    const a = weaveEditAgent();
    const e = habitat.weaveEdit;
    if (!a || !e) return;
    pushUndo();
    const key = e.ix + ',' + e.iy;
    if (a.custom && a.custom.walls) delete a.custom.walls[key];
    if (a.custom && a.custom.paths) delete a.custom.paths[key];
    if (a.custom && a.custom.shapes) delete a.custom.shapes[key];
    if (e.drafts && e.drafts[key]) e.drafts[key].length = 0;
    if (a.cache && a.cache.delete) a.cache.delete(key);
    weaveCellContent(a, e.ix, e.iy);
    syncRoutePanel();
    syncEditNote();
    toast('已清掉格 (' + e.ix + ',' + e.iy + ') 的自定义壁、丝路与孔洞。', 'ok');
  }

  /* ===== 多边形式手柄：单元缩放 / 移动、圆孔与缺口、壁与丝路顶点 ===== */
  function ensureShapeOverride(a, ix, iy) {
    const key = ix + ',' + iy;
    a.custom = a.custom || { walls: {}, paths: {}, shapes: {} };
    if (!a.custom.shapes) a.custom.shapes = {};
    if (!a.custom.shapes[key]) {
      const spec = weaveCellContent(a, ix, iy).cell;
      a.custom.shapes[key] = {
        notch: spec.notch ? { ...spec.notch } : null,
        islands: (spec.islands || []).map(o => ({ ...o })),
      };
    }
    return a.custom.shapes[key];
  }

  const WEAVE_HANDLE_LABEL = {
    unitCorner: '拖：改整块大小',
    unitEdge: '拖：只改这一边',
    unitMove: '拖：整块挪位置',
    islandMove: '拖：挪孔洞',
    islandR: '拖：改孔洞大小',
    notchMove: '拖：挪缺口',
    notchR: '拖：改缺口大小',
    wallV: '拖：改壁顶点（Alt+点删）',
    pathV: '拖：改丝路顶点（Alt+点删）',
    outlineV: '拖：改外框顶点（Alt+点删）',
    outlineMid: '拖：从这条边拉出一个新角点',
  };

  function weaveHandles(a, ix, iy) {
    const key = ix + ',' + iy;
    const c = weaveCellContent(a, ix, iy);
    const ox = a.x + ix * a.w, oy = a.y + iy * a.h;
    const tool = (habitat.weaveEdit && habitat.weaveEdit.tool) || 'shape';
    const want = (k) => {
      // 角点 / 边中点 / 整块挪动 是「随时都能用」的手柄，不分工具
      if (k === 'unitCorner' || k === 'unitEdge' || k === 'unitMove' || k === 'outlineMid') return true;
      if (tool === 'shape') return true;
      if (tool === 'hole') return k === 'islandMove' || k === 'islandR' || k === 'unitCorner' || k === 'unitMove';
      if (tool === 'notch') return k === 'notchMove' || k === 'notchR' || k === 'notchV' || k === 'notchMid' || k === 'unitCorner' || k === 'unitMove';
      if (tool === 'wall') return k === 'wallV' || k === 'unitCorner' || k === 'unitMove';
      if (tool === 'path') return k === 'pathV' || k === 'unitCorner' || k === 'unitMove';
      if (tool === 'outline') return k === 'outlineV' || k === 'unitCorner' || k === 'unitMove';
      return true;
    };
    const hs = [];
    const add = (h) => { if (want(h.kind)) { h.label = WEAVE_HANDLE_LABEL[h.kind] || ''; hs.push(h); } };
    [[-1, -1], [1, -1], [-1, 1], [1, 1]].forEach(([sx, sy]) => {
      add({ kind: 'unitCorner', sx, sy, x: ox + sx * a.w / 2, y: oy + sy * a.h / 2 });
    });
    // 四个边中点：只拖这一边，另一侧固定（像建模软件拉包围盒）
    add({ kind: 'unitEdge', edge: 'l', x: ox - a.w / 2, y: oy });
    add({ kind: 'unitEdge', edge: 'r', x: ox + a.w / 2, y: oy });
    add({ kind: 'unitEdge', edge: 't', x: ox, y: oy - a.h / 2 });
    add({ kind: 'unitEdge', edge: 'b', x: ox, y: oy + a.h / 2 });
    add({ kind: 'unitMove', x: a.x, y: a.y });
    (c.cell.islands || []).forEach((isl, i) => {
      add({ kind: 'islandMove', i, x: ox + isl.cx, y: oy + isl.cy });
      add({ kind: 'islandR', i, x: ox + isl.cx + isl.r, y: oy + isl.cy });
    });
    if (c.cell.notch) {
      add({ kind: 'notchMove', x: ox + c.cell.notch.cx, y: oy + c.cell.notch.cy });
      add({ kind: 'notchR', x: ox + c.cell.notch.cx + c.cell.notch.r, y: oy + c.cell.notch.cy });
    }
    // 手画的缺口：每个顶点一个点，每条边的中点可以拖出一个新顶点
    if (Array.isArray(c.cell.notchPts) && c.cell.notchPts.length >= 3) {
      const np = c.cell.notchPts;
      np.forEach((pt, vi) => add({ kind: 'notchV', vi, x: ox + pt.x, y: oy + pt.y }));
      for (let vi = 0; vi < np.length; vi++) {
        const p1 = np[vi], p2 = np[(vi + 1) % np.length];
        add({ kind: 'notchMid', vi, x: ox + (p1.x + p2.x) / 2, y: oy + (p1.y + p2.y) / 2 });
      }
    }
    const bw = (a.custom && a.custom.walls && a.custom.walls[key]) || [];
    const bp = (a.custom && a.custom.paths && a.custom.paths[key]) || [];
    bw.forEach((line, wi) => (line.pts || line).forEach((pt, vi) => {
      add({ kind: 'wallV', wi, vi, x: ox + pt.x, y: oy + pt.y });
    }));
    bp.forEach((line, pi) => (line.pts || line).forEach((pt, vi) => {
      add({ kind: 'pathV', pi, vi, x: ox + pt.x, y: oy + pt.y });
    }));
    // 自定义外框轮廓顶点：白点可拖，Alt+点可删
    if (Array.isArray(a.outline)) {
      a.outline.forEach((pt, vi) => add({ kind: 'outlineV', vi, x: ox + pt.x, y: oy + pt.y }));
      // 每条边的中点：拖一下就地拉出一个新角点（像钢笔工具加点）
      for (let vi = 0; vi < a.outline.length; vi++) {
        const p1 = a.outline[vi], p2 = a.outline[(vi + 1) % a.outline.length];
        add({ kind: 'outlineMid', vi, x: ox + (p1.x + p2.x) / 2, y: oy + (p1.y + p2.y) / 2 });
      }
    }
    return hs;
  }

  function applyWeaveHandleDrag(h, p) {
    const a = weaveEditAgent();
    const e = habitat.weaveEdit;
    if (!a || !e) return;
    if (a.locked) return;
    const key = e.ix + ',' + e.iy;
    const ix = e.ix, iy = e.iy;
    const ox = a.x + ix * a.w, oy = a.y + iy * a.h;
    if (h.kind === 'unitMove') {
      a.x = p.x;
      a.y = p.y;
      return;
    }
    if (h.kind === 'unitEdge') {
      // 只动被拖的这一边，对面那条边钉死
      if (h.edge === 'l' || h.edge === 'r') {
        const left = ox - a.w / 2, right = ox + a.w / 2;
        const nw = Math.max(80, Math.min(1200, h.edge === 'l' ? right - p.x : p.x - left));
        const nox = h.edge === 'l' ? right - nw / 2 : left + nw / 2;
        a.w = nw;
        a.x = nox - ix * nw;
      } else {
        const top = oy - a.h / 2, bot = oy + a.h / 2;
        const nh = Math.max(80, Math.min(1200, h.edge === 't' ? bot - p.y : p.y - top));
        const noy = h.edge === 't' ? bot - nh / 2 : top + nh / 2;
        a.h = nh;
        a.y = noy - iy * nh;
      }
      a.cache = new Map();
      buildWeave(a);
      return;
    }
    if (h.kind === 'unitCorner') {
      // 对角固定，拖动角改宽高（像建模软件拉框）
      const fixedX = a.x + ix * a.w - h.sx * a.w / 2;
      const fixedY = a.y + iy * a.h - h.sy * a.h / 2;
      a.w = Math.max(80, Math.min(1200, Math.abs(p.x - fixedX)));
      a.h = Math.max(80, Math.min(1200, Math.abs(p.y - fixedY)));
      a.x = fixedX + h.sx * a.w / 2 - ix * a.w;
      a.y = fixedY + h.sy * a.h / 2 - iy * a.h;
      a.cache = new Map();
      buildWeave(a);
      return;
    }
    const sh = ensureShapeOverride(a, ix, iy);
    if (h.kind === 'islandMove') {
      const isl = sh.islands[h.i];
      if (!isl) return;
      isl.cx = p.x - ox;
      isl.cy = p.y - oy;
    } else if (h.kind === 'islandR') {
      const isl = sh.islands[h.i];
      if (!isl) return;
      // 孔洞大小不限：只保证不把整格吃干净（留 1% 边），要多大拉多大
      isl.r = Math.max(6, Math.min(Math.min(a.w, a.h) * 0.99, Math.hypot(p.x - ox - isl.cx, p.y - oy - isl.cy)));
    } else if (h.kind === 'notchMove' || h.kind === 'notchR') {
      if (!sh.notch) return;
      if (h.kind === 'notchMove') {
        sh.notch.cx = p.x - ox;
        sh.notch.cy = p.y - oy;
      } else {
        sh.notch.r = Math.max(6, Math.hypot(p.x - ox - sh.notch.cx, p.y - oy - sh.notch.cy));
      }
    } else if (h.kind === 'notchV') {
      if (!sh.notchPts || !sh.notchPts[h.vi]) return;
      sh.notchPts[h.vi] = { x: p.x - ox, y: p.y - oy };
    } else if (h.kind === 'notchMid') {
      if (!sh.notchPts) return;
      if (h.newIdx == null) {
        sh.notchPts.splice(h.vi + 1, 0, { x: p.x - ox, y: p.y - oy });
        h.newIdx = h.vi + 1;
      } else {
        sh.notchPts[h.newIdx] = { x: p.x - ox, y: p.y - oy };
      }
    } else if (h.kind === 'outlineV') {
      if (!Array.isArray(a.outline) || !a.outline[h.vi]) return;
      a.outline[h.vi].x = p.x - ox;
      a.outline[h.vi].y = p.y - oy;
      if (a.cache && a.cache.clear) a.cache.clear();
      buildWeave(a);
      return;
    } else if (h.kind === 'outlineMid') {
      // 第一次拖动就插入一个新角点，之后这个手柄一直拖这个新点
      if (!Array.isArray(a.outline)) return;
      if (h.newIdx == null) {
        a.outline.splice(h.vi + 1, 0, { x: p.x - ox, y: p.y - oy });
        h.newIdx = h.vi + 1;
      } else {
        a.outline[h.newIdx] = { x: p.x - ox, y: p.y - oy };
      }
      if (a.cache && a.cache.clear) a.cache.clear();
      buildWeave(a);
      return;
    } else if (h.kind === 'wallV' || h.kind === 'pathV') {
      const bucket = h.kind === 'wallV' ? a.custom.walls : a.custom.paths;
      const line = (bucket[key] || [])[h.wi != null ? h.wi : h.pi];
      if (!line) return;
      const pts = line.pts || line;
      if (!pts[h.vi]) return;
      pts[h.vi].x = p.x - ox;
      pts[h.vi].y = p.y - oy;
    } else return;
    if (a.cache && a.cache.delete) a.cache.delete(key);
    weaveCellContent(a, ix, iy);
  }

  function deleteWeaveHandleVertex(h) {
    const a = weaveEditAgent();
    const e = habitat.weaveEdit;
    if (!a || !e) return false;
    if (h.kind === 'outlineV') {
      if (!Array.isArray(a.outline) || a.outline.length <= 3) {
        toast('外框至少保留 3 个顶点。', 'err');
        return true;
      }
      pushUndo();
      a.outline.splice(h.vi, 1);
      if (a.cache && a.cache.clear) a.cache.clear();
      buildWeave(a);
      syncRoutePanel();
      return true;
    }
    if (h.kind === 'notchV') {
      const key2 = e.ix + ',' + e.iy;
      const sh = ensureShapeOverride(a, e.ix, e.iy);
      if (!sh.notchPts) return false;
      pushUndo();
      if (sh.notchPts.length <= 3) delete sh.notchPts;
      else sh.notchPts.splice(h.vi, 1);
      if (a.cache && a.cache.delete) a.cache.delete(key2);
      weaveCellContent(a, e.ix, e.iy);
      syncRoutePanel();
      syncEditNote();
      toast(sh.notchPts ? '已删掉这个顶点。' : '缺口少于三个点就整个删掉了。', 'ok');
      return true;
    }
    if (h.kind !== 'wallV' && h.kind !== 'pathV') return false;
    const key = e.ix + ',' + e.iy;
    const bucket = h.kind === 'wallV' ? a.custom.walls : a.custom.paths;
    const line = (bucket[key] || [])[h.wi != null ? h.wi : h.pi];
    if (!line) return false;
    const pts = line.pts || line;
    const wi = h.wi != null ? h.wi : h.pi;
    if (pts.length <= 2) delete bucket[key][wi];
    else pts.splice(h.vi, 1);
    if (!bucket[key] || !bucket[key].length) delete bucket[key];
    if (a.cache && a.cache.delete) a.cache.delete(key);
    weaveCellContent(a, e.ix, e.iy);
    syncRoutePanel();
    toast('已删除一个顶点。', 'ok');
    return true;
  }

  function drawWeaveHandles(ctx, a, v) {
    const e = habitat.weaveEdit;
    if (!e || e.agentId !== a.id) return;
    const hs = weaveHandles(a, e.ix, e.iy);
    ctx.save();
    ctx.globalCompositeOperation = 'source-over';
    ctx.lineWidth = 1;
    renderHoverLabel(ctx, hs, v);
    hs.forEach(h => {
      const px = v.px(h.x), py = v.py(h.y);
      const hov = habitat.hoverHandle && habitat.hoverHandle.kind === h.kind &&
        Math.abs(habitat.hoverHandle.x - h.x) < 1e-6 && Math.abs(habitat.hoverHandle.y - h.y) < 1e-6;
      if (h.kind === 'unitCorner') {
        ctx.fillStyle = '#f0b45a';
        ctx.fillRect(px - (hov ? 5 : 4), py - (hov ? 5 : 4), hov ? 10 : 8, hov ? 10 : 8);
      } else if (h.kind === 'unitEdge') {
        // 边中点画成短粗条：一看就知道"拉这条边"
        ctx.fillStyle = '#f0b45a';
        const L = hov ? 16 : 13, T = hov ? 7 : 6;
        if (h.edge === 'l' || h.edge === 'r') ctx.fillRect(px - T / 2, py - L / 2, T, L);
        else ctx.fillRect(px - L / 2, py - T / 2, L, T);
      } else if (h.kind === 'unitMove') {
        ctx.strokeStyle = '#f0b45a';
        ctx.lineWidth = hov ? 2 : 1;
        ctx.beginPath();
        ctx.arc(px, py, 7, 0, Math.PI * 2);
        ctx.moveTo(px - 10, py); ctx.lineTo(px + 10, py);
        ctx.moveTo(px, py - 10); ctx.lineTo(px, py + 10);
        ctx.stroke();
        ctx.lineWidth = 1;
      } else if (h.kind === 'islandMove' || h.kind === 'notchMove') {
        ctx.fillStyle = '#79cbb6';
        ctx.beginPath();
        ctx.arc(px, py, hov ? 6 : 4.5, 0, Math.PI * 2);
        ctx.fill();
      } else if (h.kind === 'islandR' || h.kind === 'notchR') {
        ctx.strokeStyle = '#79cbb6';
        ctx.fillStyle = '#0b1210';
        ctx.beginPath();
        ctx.arc(px, py, hov ? 6 : 4.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
      } else if (h.kind === 'notchV') {
        const sz = hov ? 11 : 8.5;
        ctx.fillStyle = '#e8eee9';
        ctx.fillRect(px - sz / 2, py - sz / 2, sz, sz);
        ctx.strokeStyle = 'rgba(121,203,182,0.9)';
        ctx.strokeRect(px - sz / 2, py - sz / 2, sz, sz);
      } else if (h.kind === 'notchMid') {
        ctx.strokeStyle = hov ? 'rgba(232,238,233,0.95)' : 'rgba(232,238,233,0.55)';
        ctx.strokeRect(px - 4, py - 4, 8, 8);
      } else if (h.kind === 'outlineMid') {
        ctx.strokeStyle = 'rgba(232,238,233,0.85)';
        ctx.lineWidth = 1;
        ctx.strokeRect(px - 3.5, py - 3.5, 7, 7);
      } else {
        ctx.fillStyle = '#e8eee9';
        ctx.fillRect(px - 3, py - 3, 6, 6);
      }
    });
    // 正在拖角/边的时候，在块上方直接报尺寸，边拖边看得见
    const dg = habitat.drag;
    if (dg && dg.kind === 'weaveHandle' && (dg.handle.kind === 'unitCorner' || dg.handle.kind === 'unitEdge')) {
      const txt = '宽 ' + Math.round(a.w) + ' × 高 ' + Math.round(a.h) + ' 像素';
      ctx.font = '12px "Microsoft YaHei", system-ui, sans-serif';
      ctx.textBaseline = 'middle';
      const tw = ctx.measureText(txt).width;
      const bx = v.px(a.x) - tw / 2 - 8, by = v.py(a.y - a.h / 2) - 26;
      ctx.fillStyle = 'rgba(10,16,14,0.88)';
      ctx.fillRect(bx, by, tw + 16, 20);
      ctx.strokeStyle = 'rgba(240,180,90,0.75)';
      ctx.lineWidth = 1;
      ctx.strokeRect(bx, by, tw + 16, 20);
      ctx.fillStyle = '#f4e6cc';
      ctx.fillText(txt, bx + 8, by + 10);
    }
    ctx.restore();
  }
  function renderHoverLabel(ctx, hs, v) {
    const h = habitat.hoverHandle;
    if (!h || !h.label) return;
    const px = v.px(h.x), py = v.py(h.y);
    ctx.save();
    ctx.font = '11px "Microsoft YaHei", system-ui, sans-serif';
    ctx.textBaseline = 'middle';
    const tw = ctx.measureText(h.label).width;
    const bw = tw + 12, bh = 18;
    let bx = px + 12, by = py - 22;
    bx = Math.min(bx, ctx.canvas.width - bw - 4);
    by = Math.max(4, by);
    ctx.fillStyle = 'rgba(10,14,12,0.92)';
    ctx.strokeStyle = '#f0b45a';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.rect(bx, by, bw, bh);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = '#f5d3a2';
    ctx.fillText(h.label, bx + 6, by + bh / 2);
    ctx.restore();
  }
  // 画布上的小标签（深底 + 描边），用于半径、尺寸这类"直接读数"
  function drawChip(ctx, px, py, text, color) {
    ctx.save();
    ctx.font = '11px "Microsoft YaHei", system-ui, sans-serif';
    ctx.textBaseline = 'middle';
    const tw = ctx.measureText(text).width, bw = tw + 10, bh = 17;
    let bx = px + 10, by = py - bh - 6;
    bx = Math.min(bx, ctx.canvas.width - bw - 6);
    by = Math.max(6, Math.min(by, ctx.canvas.height - bh - 6));
    ctx.fillStyle = 'rgba(8,12,11,0.92)';
    ctx.fillRect(bx, by, bw, bh);
    ctx.strokeStyle = color; ctx.lineWidth = 1; ctx.strokeRect(bx, by, bw, bh);
    ctx.fillStyle = color;
    ctx.fillText(text, bx + 5, by + bh / 2);
    ctx.restore();
  }

  // 编辑中的"实时预览"：虚线框、孔的圆和半径读数、正在拖的那条壁/丝路。
  // 这些只画在蚕室画布上，从不写进 agent 数据，所以导出（场景 / 曲线 / 视频）里不会出现。
  function drawEditLivePreview(ctx, a, v) {
    const e = habitat.weaveEdit;
    if (!e || e.agentId !== a.id) return;
    const ox = a.x + e.ix * a.w, oy = a.y + e.iy * a.h;
    const c = weaveCellContent(a, e.ix, e.iy);
    const key = e.ix + ',' + e.iy;
    const sh = (a.custom && a.custom.shapes && a.custom.shapes[key]) || null;
    const islands = (sh && sh.islands) || (c.cell && c.cell.islands) || [];
    const notch = (sh && sh.notch) || (c.cell && c.cell.notch) || null;
    ctx.save();
    ctx.lineCap = 'butt';
    ctx.setLineDash([5, 4]);
    ctx.strokeStyle = 'rgba(240,180,90,0.85)';
    ctx.lineWidth = 1.5;
    // 正在编辑的这一格
    ctx.strokeRect(v.px(ox - a.w / 2), v.py(oy - a.h / 2), a.w * v.s, a.h * v.s);
    ctx.setLineDash([]);
    drawChip(ctx, v.px(ox - a.w / 2), v.py(oy - a.h / 2), '编辑：第 ' +
      (habitat.agents.filter(x => x.kind === 'weave').findIndex(x => x.id === a.id) + 1) + ' 块', '#F0B45A');
    // 孔：虚线圆 + 圆心十字 + 半径读数（拖哪个孔就高亮哪个）
    islands.forEach((isl, i) => {
      const cx = v.px(ox + isl.cx), cy = v.py(oy + isl.cy), rr = Math.max(1, isl.r * v.s);
      const dragging = habitat.drag && habitat.drag.kind === 'weaveHandle' && habitat.drag.handle.i === i;
      ctx.setLineDash([6, 4]);
      ctx.strokeStyle = dragging ? 'rgba(185,230,218,0.95)' : 'rgba(121,203,182,0.55)';
      ctx.beginPath();
      ctx.arc(cx, cy, rr, 0, Math.PI * 2);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.strokeStyle = 'rgba(121,203,182,0.75)';
      ctx.beginPath();
      ctx.moveTo(cx - 5, cy); ctx.lineTo(cx + 5, cy);
      ctx.moveTo(cx, cy - 5); ctx.lineTo(cx, cy + 5);
      ctx.stroke();
      if (dragging || i === 0) {
        ctx.beginPath();
        ctx.moveTo(cx, cy); ctx.lineTo(cx + rr, cy);
        ctx.stroke();
        drawChip(ctx, cx, cy - rr, 'Ø ' + Math.round(isl.r * 2) + ' px', '#79CBB6');
      }
    });
    if (notch) {
      const cx = v.px(ox + notch.cx), cy = v.py(oy + notch.cy), rr = Math.max(1, notch.r * v.s);
      ctx.setLineDash([4, 5]);
      ctx.strokeStyle = 'rgba(240,180,90,0.6)';
      ctx.beginPath();
      ctx.arc(cx, cy, rr, 0, Math.PI * 2);
      ctx.stroke();
      ctx.setLineDash([]);
    }
    // 壁 / 丝路：正在拖的那条整体点亮，让人知道"正在改的是这条"
    const d = habitat.drag;
    const hk = d && d.kind === 'weaveHandle' ? d.handle.kind : '';
    const bucketW = (a.custom && a.custom.walls && a.custom.walls[key]) || [];
    const bucketP = (a.custom && a.custom.paths && a.custom.paths[key]) || [];
    const hlW = (hk === 'wallV') ? d.handle.wi : null;
    const hlP = (hk === 'pathV') ? d.handle.pi : null;
    bucketW.forEach((line, wi) => {
      const src = line.pts || line;
      const pts = weaveSmooth(src, line.closed, Math.max(2, Math.min(a.w, a.h) / 42));
      ctx.strokeStyle = wi === hlW ? 'rgba(120,210,255,0.9)' : 'rgba(232,238,233,0.75)';
      ctx.lineWidth = wi === hlW ? 2 : 1.2;
      ctx.beginPath();
      pts.forEach((q, k) => {
        const px = v.px(ox + q.x), py = v.py(oy + q.y);
        if (k === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      });
      ctx.stroke();
    });
    bucketP.forEach((line, pi) => {
      const src = line.pts || line;
      const pts = weaveSmooth(src, line.closed, Math.max(2, Math.min(a.w, a.h) / 42));
      ctx.strokeStyle = pi === hlP ? 'rgba(120,255,180,0.9)' : 'rgba(140,220,170,0.55)';
      ctx.lineWidth = pi === hlP ? 2 : 1.2;
      ctx.setLineDash([7, 4]);
      ctx.beginPath();
      pts.forEach((q, k) => {
        const px = v.px(ox + q.x), py = v.py(oy + q.y);
        if (k === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      });
      ctx.stroke();
      ctx.setLineDash([]);
    });
    // 手画的缺口（闭合多边形）：编辑时用虚线把这一圈显出来
    const npC = (sh && sh.notchPts) || (c.cell && c.cell.notchPts) || null;
    const npCurve = weaveNotchCurve(npC);
    if (Array.isArray(npCurve) && npCurve.length >= 3) {
      ctx.strokeStyle = 'rgba(121,203,182,0.7)';
      ctx.lineWidth = 1.4;
      ctx.setLineDash([6, 4]);
      ctx.beginPath();
      npCurve.forEach((q, k) => {
        const px = v.px(ox + q.x), py = v.py(oy + q.y);
        if (k === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      });
      ctx.closePath();
      ctx.stroke();
      ctx.setLineDash([]);
    }
    // 正在画、还没收尾的点（加壁/加丝路/缺口/外框）
    const draft = (e.drafts && e.drafts[key]) || [];
    if (draft.length) {
      // 缺口在"画"的时候就已经是光滑曲线（跟收尾后一致），不是先折线后变曲线
      const draftLine = (e.mode === 'notch' && draft.length >= 3) ? weaveNotchCurve(draft) : draft;
      ctx.strokeStyle = 'rgba(120,210,255,0.8)';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([4, 3]);
      ctx.beginPath();
      draftLine.forEach((q, k) => {
        const px = v.px(ox + q.x), py = v.py(oy + q.y);
        if (k === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      });
      if (e.mode === 'notch' && draft.length >= 3) ctx.closePath();
      ctx.stroke();
      draft.forEach((q) => {
        ctx.fillStyle = 'rgba(120,210,255,0.85)';
        ctx.fillRect(v.px(ox + q.x) - 2.5, v.py(oy + q.y) - 2.5, 5, 5);
      });
      ctx.setLineDash([]);
    }
    if (Array.isArray(e.outlinePts) && e.outlinePts.length && e.mode === 'outline') {
      ctx.strokeStyle = 'rgba(120,210,255,0.85)';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([4, 3]);
      ctx.beginPath();
      e.outlinePts.forEach((q, k) => {
        const px = v.px(q.x), py = v.py(q.y);
        if (k === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      });
      ctx.stroke();
      ctx.setLineDash([]);
    }
    ctx.restore();
  }

  document.getElementById('habAddWeave').addEventListener('click', addWeaveAgent);
  const addOutlineBtn = document.getElementById('habAddOutline');
  if (addOutlineBtn) addOutlineBtn.addEventListener('click', startOutlineUnit);
  const addMosaicBtn = document.getElementById('habAddMosaic');
  if (addMosaicBtn) addMosaicBtn.addEventListener('click', addWeaveMosaic);
  window.addEventListener('keydown', (ev) => {
    if (ev.key !== 'Escape') return;
    if (habitat.newOutline) { habitat.newOutline = null; hint('已取消轮廓绘制。'); }
    if (habitat.weaveEdit && habitat.weaveEdit.mode === 'outline') { habitat.weaveEdit.outlinePts = []; syncEditNote(); }
  });
  document.getElementById('habAddRandom').addEventListener('click', () => {
    pushUndo();
    makeRandomDemo();
    renderList();
  });
  document.getElementById('habHide').addEventListener('click', () => { const a = chosen(); if (a) { a.bodyVisible = false; renderList(); } });
  document.getElementById('habShow').addEventListener('click', () => { const a = chosen(); if (a) { a.bodyVisible = true; renderList(); } });
  document.getElementById('habDropSilk').addEventListener('click', () => {
    const a = chosen();
    if (!a || a.mode === 'bench') return;
    if (a.kind === 'weave') { toast('织网单元没有可保留的丝；如需重织，点「重新织」。', 'err'); return; }
    pushUndo();
    if (a.kind === 'route') { a.route = []; a.kind = 'random'; }
    else if (a.silk.length > 1) habitat.orphans.push(a.silk.slice());
    a.mode = 'bench'; a.silk = []; a.bodyVisible = true;
    renderList();
  });
  document.getElementById('habDropAll').addEventListener('click', () => {
    const a = chosen();
    if (!a || a.mode === 'bench') return;
    pushUndo();
    if (a.kind === 'route') { a.route = []; a.kind = 'random'; }
    a.mode = 'bench'; a.silk = []; a.bodyVisible = true;
    renderList();
  });
  document.getElementById('habUndo').addEventListener('click', () => { undoStep(); });
  const habRedoBtn = document.getElementById('habRedo');
  if (habRedoBtn) habRedoBtn.addEventListener('click', () => { redoStep(); });
  // 快捷键：Ctrl+Z 撤销，Ctrl+Shift+Z / Ctrl+Y 重做。输入框里不抢键。
  window.addEventListener('keydown', (ev) => {
    const tag = (ev.target && ev.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select' || ev.target.isContentEditable) return;
    if (!(ev.ctrlKey || ev.metaKey)) return;
    const k = (ev.key || '').toLowerCase();
    if (k === 'z' && !ev.shiftKey) { ev.preventDefault(); undoStep(); }
    else if ((k === 'z' && ev.shiftKey) || k === 'y') { ev.preventDefault(); redoStep(); }
  });
  document.getElementById('habStart').addEventListener('click', () => {
    const ready = habitat.agents.filter(a =>
      a.mode !== 'bench' &&
      a.mode !== 'drag' &&
      (a.kind !== 'route' || (a.route && a.route.length >= 2))
    );
    if (!ready.length) {
      toast('请先将蚕拖入场地，再点击开始。', 'err');
      hint('目前没有已放入场地、可以运动的个体。');
      return;
    }
    ready.forEach(a => {
      if (a.kind === 'route') {
        a.follow = true;
        if (!Number.isFinite(a.u)) a.u = 0;
      }
      if (a.kind === 'weave') {
        if (a.u >= 1) a.u = 0;
        if (!a.cache || !a.cache.size) buildWeave(a);
      }
      a.mode = 'run';
    });
    renderList();
    toast('已启动 ' + ready.length + ' 只蚕。', 'ok');
    hint('实测蚕正在沿测量轨迹运动；可在右侧调整每只蚕的速度倍率。');
  });
  document.getElementById('habPause').addEventListener('click', () => {
    habitat.agents.forEach(a => { if (a.mode === 'run') a.mode = 'paused'; });
    renderList();
  });
  document.getElementById('habResume').addEventListener('click', () => {
    habitat.agents.forEach(a => { if (a.mode === 'paused') a.mode = 'run'; });
    renderList();
  });
  document.getElementById('habSave').addEventListener('click', () => {
    const doc = {
      type: 'silkworm-habitat/v1',
      modelVersion: MODEL,
      disclaimer: '温湿度映射为演示模型，不是已验证的生理规律',
      temperatureC: habitat.tempC,
      humidity: habitat.humidity,
      seed: habitat.seed,
      simTime: habitat.simTime,
      shape: habitat.shape,
      obstacles: habitat.obstacles,
      agents: habitat.agents.map(a => ({
        id: a.id, mode: a.mode, bodyVisible: a.bodyVisible,
        x: a.x, y: a.y, heading: a.heading, silk: a.silk,
        kind: a.kind, wormId: a.wormId, route: a.route,
        offX: a.offX, offY: a.offY, rot: a.rot, scale: a.scale,
        follow: a.follow, u: a.u, color: a.color,
        scope: a.scope || 'field', homeUnitId: a.homeUnitId || null,
        weave: a.kind === 'weave' ? {
          w: a.w, h: a.h, coverage: a.coverage, shape: a.shape,
          worms: a.worms, seed: a.seed, duration: a.duration, u: a.u, wallAff: a.wallAff,
          tileField: !!a.tileField,
          tone: Number.isFinite(a.tone) ? a.tone : 0.85,
          gap: Number.isFinite(a.gap) ? a.gap : 6,
          strata: Math.max(1, Math.min(3, a.strata || 2)),
          outline: (Array.isArray(a.outline) && a.outline.length >= 3)
            ? a.outline.map(p => ({ x: Math.round(p.x * 10) / 10, y: Math.round(p.y * 10) / 10 }))
            : null,
          profile: a.profile || null,
          custom: a.custom || { walls: {}, paths: {}, shapes: {} },
        } : undefined,
        speedScale: Number.isFinite(a.speedScale) ? a.speedScale : 1,
      })),
      orphanSilk: habitat.orphans,
      referenceReadOnly: habitat.reference,
    };
    const blob = new Blob([JSON.stringify(doc, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'habitat-' + Date.now() + '.json';
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1500);
    syncAutoStat('已存工程文件 ' + link.download);
  });
  // ===== 载入工程（场地场景）/ 自动保存 / 下次打开自动恢复 =====
  const AUTO_KEY = 'silkworm-habitat-autosave/v1';
  let autoSavedAt = 0;
  function syncAutoStat(msg) {
    const el = document.getElementById('habAutoStat');
    if (!el) return;
    if (msg) { el.textContent = msg; return; }
    if (!autoSavedAt) { el.textContent = '自动保存：每 3 秒存一次到本机浏览器，关掉网页也不会丢。'; return; }
    const d = new Date(autoSavedAt);
    el.textContent = '自动保存：' + ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2) +
      ':' + ('0' + d.getSeconds()).slice(-2) + ' 已存（关掉网页下次自动接着）。';
  }
  function autoSaveNow() {
    try {
      const doc = exportHabitat();
      if (!doc) return;
      localStorage.setItem(AUTO_KEY, JSON.stringify({ t: Date.now(), doc }));
      autoSavedAt = Date.now();
      syncAutoStat();
    } catch (err) {
      const el = document.getElementById('habAutoStat');
      if (el) el.textContent = '自动保存失败（本机浏览器存储满了）：请用「保存工程（.json）」手动存一份。';
      try { clearInterval(autoTimer); } catch (_) {}
    }
  }
  const autoTimer = setInterval(autoSaveNow, 3000);
  window.addEventListener('beforeunload', autoSaveNow);
  document.addEventListener('visibilitychange', () => { if (document.hidden) autoSaveNow(); });
  document.getElementById('habLoad').addEventListener('click', () => {
    const inp = document.getElementById('habSceneFile');
    if (inp) { inp.value = ''; inp.click(); }
  });
  document.getElementById('habSceneFile').addEventListener('change', (ev) => {
    const f = ev.target.files && ev.target.files[0];
    if (!f) return;
    const rd = new FileReader();
    rd.onload = () => {
      let doc = null;
      try { doc = JSON.parse(rd.result); } catch (err) {
        toast('这个文件不是有效的工程 JSON：' + err.message, 'err'); return;
      }
      const type = doc && (doc.type || '');
      if (!/silkworm-habitat/i.test(type)) {
        toast('这是「' + (type || '未知') + '」文件，不是场地工程。请用「保存工程（.json）」存出来的那份。', 'err');
        return;
      }
      try {
        importHabitat(doc);
        habitat.agents.forEach(a => { if (a.kind === 'weave') { a.cache = new Map(); buildWeave(a); } });
        renderList();
        syncEditNote();
        toast('工程已载入：' + habitat.agents.filter(a => a.kind === 'weave').length + ' 个织网单元、' +
          habitat.agents.filter(a => a.kind === 'route').length + ' 只蚕。', 'ok');
      } catch (err) {
        toast('载入失败：' + (err && err.message ? err.message : String(err)), 'err');
      }
    };
    rd.readAsText(f, 'utf-8');
  });
  setTimeout(() => {
    try {
      const raw = localStorage.getItem(AUTO_KEY);
      if (!raw) return;
      const pack = JSON.parse(raw);
      if (!pack || !pack.doc) return;
      const ageH = (Date.now() - (pack.t || 0)) / 3600000;
      if (ageH > 24 * 7) return;
      importHabitat(pack.doc);
      habitat.agents.forEach(a => { if (a.kind === 'weave') { a.cache = new Map(); buildWeave(a); } });
      renderList();
      autoSavedAt = pack.t;
      const d = new Date(pack.t);
      toast('已恢复上次编辑的场地（' + (d.getMonth() + 1) + '月' + d.getDate() + '日 ' +
        ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2) + '）。', 'ok');
      syncAutoStat();
    } catch (err) { /* 损坏就当作没有 */ }
  }, 500);
  document.getElementById('habImportTraj').addEventListener('click', importMeasuredTrajectories);
  document.getElementById('habRef').addEventListener('click', () => {
    const srcs = measuredSource();
    const t0 = srcs.find(t => (t.points || []).length > 1);
    const src = t0 ? t0.points.filter(p => p && Number.isFinite(p.x) && Number.isFinite(p.y)) : [];
    if (!src.length) { toast('没有可铺底的实测轨迹。', 'err'); return; }
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    src.forEach(p => { minX = Math.min(minX, p.x); minY = Math.min(minY, p.y); maxX = Math.max(maxX, p.x); maxY = Math.max(maxY, p.y); });
    const a = arenaSpec();
    const span = Math.max(maxX - minX, maxY - minY) || 1;
    const target = (a.kind === 'circle' ? a.r * 1.4 : Math.min(a.hw, a.hh) * 1.4);
    habitat.reference = src.map(p => ({
      x: ((p.x - (minX + maxX) / 2) / span) * target,
      y: ((p.y - (minY + maxY) / 2) / span) * target,
    }));
    toast('已铺入蚕 ' + (t0.wormId != null ? t0.wormId : 1) + ' 的只读底图。', 'ok');
  });
  document.getElementById('habClearRef').addEventListener('click', () => { habitat.reference = null; toast('已去掉底图。', 'ok'); });
  const stage = document.querySelector('.hab-stage');
  const narrow = () => window.matchMedia('(max-width: 860px)').matches;
  const panelOpen = { left: true, right: true };

  function applyPanelState() {
    const left = document.getElementById('habLeft');
    const right = document.getElementById('habRight');
    const leftBtn = document.getElementById('habOpenLeft');
    const rightBtn = document.getElementById('habOpenRight');
    if (narrow()) {
      stage.classList.remove('left-off', 'right-off');
      left.classList.toggle('open', panelOpen.left);
      right.classList.toggle('open', panelOpen.right);
    } else {
      left.classList.remove('open');
      right.classList.remove('open');
      stage.classList.toggle('left-off', !panelOpen.left);
      stage.classList.toggle('right-off', !panelOpen.right);
    }
    const lOpen = panelOpen.left;
    const rOpen = panelOpen.right;
    leftBtn.textContent = lOpen ? '收起环境' : '展开环境';
    rightBtn.textContent = rOpen ? '收起个体' : '展开个体';
    leftBtn.classList.toggle('on', lOpen);
    rightBtn.classList.toggle('on', rOpen);
    leftBtn.setAttribute('aria-pressed', String(!lOpen));
    rightBtn.setAttribute('aria-pressed', String(!rOpen));
  }

  function togglePanel(which) {
    panelOpen[which] = !panelOpen[which];
    applyPanelState();
    const name = which === 'left' ? '环境' : '个体';
    hint(name + '面板已' + (panelOpen[which] ? '展开' : '收起') + '。');
    toast(name + '面板已' + (panelOpen[which] ? '展开' : '收起') + '（再点一次可切换）。', 'ok');
    setTimeout(() => repaintStaticLayers(), 80);
  }

  document.getElementById('habOpenLeft').addEventListener('click', () => togglePanel('left'));
  document.getElementById('habOpenRight').addEventListener('click', () => togglePanel('right'));
  window.addEventListener('resize', applyPanelState);
  applyPanelState();

  /* ===== 无限画布：滚轮缩放 / 平移 / 适应场地 ===== */
  world.addEventListener('wheel', (ev) => {
    const rect = world.getBoundingClientRect();
    const sx = (ev.clientX - rect.left) * (world.width / rect.width);
    const sy = (ev.clientY - rect.top) * (world.height / rect.height);
    const factor = Math.exp(-ev.deltaY * 0.001);
    zoomAt(sx, sy, factor);
    ev.preventDefault();
  }, { passive: false });

  document.getElementById('habZoomIn').addEventListener('click', () => {
    zoomAt(world.width / 2, world.height / 2, 1.2);
  });
  document.getElementById('habZoomOut').addEventListener('click', () => {
    zoomAt(world.width / 2, world.height / 2, 1 / 1.2);
  });
  document.getElementById('habFitView').addEventListener('click', () => {
    resetHabView();
    toast('已恢复到 100% 并居中。', 'ok');
  });
  document.getElementById('habPanToggle').addEventListener('click', (ev) => {
    habViewport.panMode = !habViewport.panMode;
    ev.currentTarget.classList.toggle('active', habViewport.panMode);
    ev.currentTarget.classList.toggle('on', habViewport.panMode);
    world.classList.toggle('pan-mode', habViewport.panMode);
    hint(habViewport.panMode ? '平移模式：按住拖动可移动画布，滚轮缩放。' : '已退出平移模式。');
  });
  updateHabZoomLabel();

  /* ===== 场地高度：按窗口自适应 =====
     目标：两侧栏各自上下滚，中间画布一屏看全，不需要滚整个页面。
     滑条现在是"高度上限"——默认放到最大，实际高度取窗口剩余高度。 */
  const canvasHeightInput = document.getElementById('habCanvasHeight');
  if (canvasHeightInput) {
    const fitStageHeight = () => {
      const cap = Math.max(460, Math.min(1400, parseInt(canvasHeightInput.value, 10) || 1400));
      const bar = document.querySelector('.hab-top');
      const timeBar = document.querySelector('.hab-time');
      const barH = bar ? bar.getBoundingClientRect().height : 56;
      const timeH = timeBar ? timeBar.getBoundingClientRect().height : 44;
      // 顶部条 + 时间条 + 两条边线都算进去，剩下的正好给舞台：整块正好一屏，开始/暂停永远在屏幕里
      const avail = Math.max(420, window.innerHeight - barH - timeH - 4);
      const h = Math.round(Math.min(cap, avail));
      document.getElementById('habitat').style.setProperty('--hab-stage-height', h + 'px');
      const valEl = document.getElementById('habCanvasHeightVal');
      if (valEl) valEl.textContent = h + 'px';
      repaintStaticLayers();
    };
    canvasHeightInput.addEventListener('input', fitStageHeight);
    window.addEventListener('resize', fitStageHeight);
    fitStageHeight();
    // 悬停在两侧栏里滚轮就滚侧栏（滚到头再交还给页面），别把整页带着跑
    ['habLeft', 'habRight'].forEach(id => {
      const el = document.getElementById(id);
      if (!el) return;
      el.addEventListener('wheel', (ev) => {
        const canScroll = el.scrollHeight > el.clientHeight + 1;
        if (!canScroll) return;
        const atTop = el.scrollTop <= 0 && ev.deltaY < 0;
        const atBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 1 && ev.deltaY > 0;
        if (atTop || atBottom) return;      // 到头了让页面接管
        el.scrollTop += ev.deltaY;
        ev.preventDefault();
      }, { passive: false });
    });
  }
  if (window.ResizeObserver) {
    const ro = new ResizeObserver(() => repaintStaticLayers());
    ro.observe(wrap);
  }

  /* ===== 运动预览宽度拖动 + 放大 ===== */
  function bindPreviewResizer() {
    const panes = document.querySelector('.panes');
    const handle = document.getElementById('previewSplitter');
    const frame = document.getElementById('previewFrame');
    if (!panes || !handle || !frame) return;

    let active = false;

    function setWidth(clientX) {
      const rect = panes.getBoundingClientRect();
      const maxWidth = Math.max(360, Math.min(1100, rect.width - 320 - handle.offsetWidth));
      const desired = rect.right - clientX - handle.offsetWidth / 2;
      const width = Math.max(360, Math.min(maxWidth, desired));
      document.documentElement.style.setProperty('--preview-width', width + 'px');
    }

    handle.addEventListener('pointerdown', (ev) => {
      if (narrow()) return;
      active = true;
      handle.setPointerCapture(ev.pointerId);
      document.body.classList.add('resizing-preview');
      ev.preventDefault();
    });
    handle.addEventListener('pointermove', (ev) => { if (active) setWidth(ev.clientX); });
    const stop = () => { active = false; document.body.classList.remove('resizing-preview'); };
    handle.addEventListener('pointerup', stop);
    handle.addEventListener('pointercancel', stop);
    handle.addEventListener('dblclick', () => {
      document.documentElement.style.setProperty('--preview-width', '48%');
    });
    handle.addEventListener('keydown', (ev) => {
      if (ev.key !== 'ArrowLeft' && ev.key !== 'ArrowRight') return;
      const current = frame.getBoundingClientRect().width;
      const next = current + (ev.key === 'ArrowLeft' ? -32 : 32);
      const rect = panes.getBoundingClientRect();
      const width = Math.max(360, Math.min(1100, rect.width - 328, next));
      document.documentElement.style.setProperty('--preview-width', width + 'px');
      ev.preventDefault();
    });
  }
  bindPreviewResizer();
  const cueEl = document.getElementById('scrollCue');
  if (cueEl) cueEl.addEventListener('click', () => {
    const h = document.getElementById('habitat');
    if (h) h.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  /* 滚到蚕室时自动再同步一次，避免描图后忘了手动点同步 */
  let lastSyncAt = 0;
  const enterObs = new IntersectionObserver((entries) => {
    if (!entries[0] || !entries[0].isIntersecting) return;
    const now = Date.now();
    if (now - lastSyncAt < 800) return;
    lastSyncAt = now;
    try {
      const n = syncMeasured();
      if (n) hint('已自动同步 ' + n + ' 条实测轨迹到蚕室。');
    } catch (_) { }
  }, { threshold: 0.2 });
  const habSection = document.getElementById('habitat');
  if (habSection && window.IntersectionObserver) enterObs.observe(habSection);

  function exportHabitat() {
    return {
      modelVersion: MODEL,
      disclaimer: '温湿度映射为演示模型，不是已验证的生理规律',
      temperatureC: habitat.tempC,
      humidity: habitat.humidity,
      seed: habitat.seed,
      simTime: habitat.simTime,
      shape: habitat.shape,
      tool: habitat.tool,
      selected: habitat.selected,
      selectedLeaf: habitat.selectedLeaf,
      layerGroups: (window.__layerStore && window.__layerStore.dump) ? window.__layerStore.dump() : null,
      obstacles: habitat.obstacles,
      orphanSilk: habitat.orphans,
      reference: habitat.reference,
      agents: habitat.agents.map(a => ({
        id: a.id,
        mode: a.mode,
        bodyVisible: a.bodyVisible,
        x: a.x,
        y: a.y,
        heading: a.heading,
        phase: a.phase,
        turnSign: a.turnSign,
        silk: a.silk,
        kind: a.kind,
        wormId: a.wormId,
        route: a.route,
        offX: a.offX,
        offY: a.offY,
        rot: a.rot,
        scale: a.scale,
        follow: a.follow,
        u: a.u,
        color: a.color,
        scope: a.scope || 'field',
        homeUnitId: a.homeUnitId || null,
        weave: a.kind === 'weave' ? {
          w: a.w, h: a.h, coverage: a.coverage, shape: a.shape,
          worms: a.worms, seed: a.seed, duration: a.duration, u: a.u, wallAff: a.wallAff,
          tileField: !!a.tileField,
          tone: Number.isFinite(a.tone) ? a.tone : 0.85,
          gap: Number.isFinite(a.gap) ? a.gap : 6,
          strata: Math.max(1, Math.min(3, a.strata || 2)),
          outline: (Array.isArray(a.outline) && a.outline.length >= 3)
            ? a.outline.map(p => ({ x: Math.round(p.x * 10) / 10, y: Math.round(p.y * 10) / 10 }))
            : null,
          profile: a.profile || null,
          custom: a.custom || { walls: {}, paths: {}, shapes: {} },
        } : undefined,
        speedScale: Number.isFinite(a.speedScale) ? a.speedScale : 1,
      })),
    };
  }

  /* ============ 母版导出（P3） ============ */

  function ledResolve() {
    const res = (document.getElementById('habLedRes') || {}).value || '2419x1360';
    const m = /^(\d+)\s*[xX×]\s*(\d+)$/.exec(res) || [0, 2419, 1360];
    const frames = Math.max(1, Math.min(3600, parseInt((document.getElementById('habLedFrames') || {}).value, 10) || 900));
    const fps = Math.max(12, Math.min(60, parseInt((document.getElementById('habLedFps') || {}).value, 10) || 30));
    return { w: +m[1], h: +m[2], frames, fps };
  }

  // 场景 = 母版渲染的输入：所有织网单元参数 + 取景 + 时间轴
  function ledScene() {
    const r = ledResolve();
    const b = ledBounds();
    const bw = Math.max(1, b.x1 - b.x0), bh = Math.max(1, b.y1 - b.y0);
    // 母版取景按目标像素算：整片块群占画面 92%，四周留安全边（LED 柜体拼缝）
    const s = Math.min(r.w * 0.92 / bw, r.h * 0.92 / bh);
    const weaveAll = habitat.agents.filter(a => a.kind === 'weave');
    const weaveShown = weaveAll.filter(a => !(a.hideSilk || habitat.hideSilkAll));
    const units = (weaveShown.length ? weaveShown : weaveAll).map((a, i) => ({
      order: i,
      x: +a.x.toFixed(2), y: +a.y.toFixed(2),
      w: +a.w.toFixed(2), h: +a.h.toFixed(2),
      coverage: Number.isFinite(a.coverage) ? a.coverage : 0.55,
      shape: a.shape || 'island',
      worms: a.worms || 6,
      seed: a.seed >>> 0,
      tone: Number.isFinite(a.tone) ? a.tone : 0.85,
      gap: Number.isFinite(a.gap) ? a.gap : 6,
      strata: Math.max(1, Math.min(3, a.strata || 2)),
      outline: (Array.isArray(a.outline) && a.outline.length >= 3)
        ? a.outline.map(p => ({ x: +p.x.toFixed(2), y: +p.y.toFixed(2) })) : null,
      custom: a.custom || { walls: {}, paths: {}, shapes: {} },
    }));
    return {
      schema: 'silkworm-led-scene/v1',
      createdAt: new Date().toISOString(),
      px: { w: r.w, h: r.h },
      fps: r.fps,
      frames: r.frames,
      // 取景：预览画布里 1 世界单位 = scale 像素，画布中心对准 center（世界坐标）
      scale: +s.toFixed(6),
      center: { x: +((b.x0 + b.x1) / 2).toFixed(3), y: +((b.y0 + b.y1) / 2).toFixed(3) },
      source: {
        silkPaths: 'measured',
        note: '丝迹形状来自实测样本回放；块位置/孔位/亮度梯度为假设（assumption），不进论文图为实测',
      },
      units,
    };
  }

  function ledBounds() {
    const all = habitat.agents.filter(a => a.kind === 'weave');
    const shown = all.filter(a => !(a.hideSilk || habitat.hideSilkAll));
    const units = shown.length ? shown : all;
    if (!units.length) return { x0: -200, y0: -200, x1: 200, y1: 200 };
    const xs = [], ys = [];
    units.forEach(a => {
      xs.push(a.x - a.w / 2, a.x + a.w / 2);
      ys.push(a.y - a.h / 2, a.y + a.h / 2);
    });
    return { x0: Math.min(...xs), y0: Math.min(...ys), x1: Math.max(...xs), y1: Math.max(...ys) };
  }

  // 曲线 JSON：每个单元的实际丝线点列（世界坐标，属性带 seed / 覆盖 / 分层）
  function ledCurves() {
    const units = [];
    habitat.agents.filter(a => a.kind === 'weave').forEach((a, i) => {
      const content = weaveCellContent(a, 0, 0);
      const cum = weavePathCum(content);
      let acc = 0;
      const curves = content.paths.map(p => {
        const len = p.pts.reduce((s, q, k) => (k ? s + Math.hypot(q.x - p.pts[k - 1].x, q.y - p.pts[k - 1].y) : 0), 0);
        const one = {
          u0: +(acc / cum.total).toFixed(5),
          length: +len.toFixed(2),
          band: p.b != null ? p.b : null,
          alpha: p.a != null ? +p.a.toFixed(3) : null,
          pts: p.pts.map(q => [+(q.x + a.x).toFixed(2), +(q.y + a.y).toFixed(2)]),
        };
        acc += len;
        return one;
      });
      units.push({
        id: a.id, order: i, x: +a.x.toFixed(2), y: +a.y.toFixed(2),
        w: a.w, h: a.h, seed: a.seed >>> 0,
        coverage: a.coverage, strata: a.strata, tone: a.tone,
        totalLength: +cum.total.toFixed(2),
        curves,
      });
    });
    return {
      schema: 'silkworm-weave-curves/v1',
      unit: 'world px（画布局部单位，1 单位 = 1 预览像素；需要 mm 请在描图器里按标定换算）',
      source: { silkPaths: 'measured', note: '形状来自实测丝迹回放' },
      units,
    };
  }

  function ledGeometryPolys(a) {
    const content = weaveCellContent(a, 0, 0);
    const polys = [];
    const cell = content.cell || {};
    if (cell.outline && cell.outline.length >= 3) {
      polys.push({ kind: 'outline', closed: true, pts: cell.outline.map(p => ({ x: p.x + a.x, y: p.y + a.y })) });
    } else {
      polys.push({
        kind: 'outline', closed: true, pts: [
          { x: a.x - a.w / 2, y: a.y - a.h / 2 }, { x: a.x + a.w / 2, y: a.y - a.h / 2 },
          { x: a.x + a.w / 2, y: a.y + a.h / 2 }, { x: a.x - a.w / 2, y: a.y + a.h / 2 },
        ],
      });
    }
    (cell.islands || []).forEach(isl => {
      const pts = [];
      const N = 48;
      for (let k = 0; k < N; k++) {
        const t = Math.PI * 2 * k / N;
        pts.push({ x: a.x + isl.cx + Math.cos(t) * isl.r, y: a.y + isl.cy + Math.sin(t) * isl.r });
      }
      polys.push({ kind: 'hole', closed: true, pts, r: isl.r });
    });
    if (cell.notch) {
      polys.push({
        kind: 'notch', closed: false, pts: [
          { x: a.x + cell.notch.x, y: a.y + cell.notch.y - (cell.notch.r || 0) },
          { x: a.x + cell.notch.x, y: a.y + cell.notch.y },
        ],
      });
    }
    content.walls.forEach(line => {
      if (line.length > 1) polys.push({ kind: 'wall', closed: false, pts: line.map(p => ({ x: p.x + a.x, y: p.y + a.y })) });
    });
    content.customWalls.forEach(cw => {
      const src = cw.pts || cw;
      if (src.length > 1) polys.push({ kind: 'manualWall', closed: !!cw.closed, pts: src.map(p => ({ x: p.x + a.x, y: p.y + a.y })) });
    });
    return polys;
  }

  function ledSvg() {
    const b = ledBounds();
    const pad = 24;
    const w = b.x1 - b.x0 + pad * 2, h = b.y1 - b.y0 + pad * 2;
    const lines = [];
    lines.push('<?xml version="1.0" encoding="UTF-8"?>');
    lines.push('<svg xmlns="http://www.w3.org/2000/svg" width="' + Math.round(w) + '" height="' + Math.round(h) +
      '" viewBox="' + (b.x0 - pad).toFixed(2) + ' ' + (b.y0 - pad).toFixed(2) + ' ' + w.toFixed(2) + ' ' + h.toFixed(2) + '">');
    lines.push('<g fill="none" stroke="#e6e8ec" stroke-width="1">');
    habitat.agents.filter(a => a.kind === 'weave').forEach(a => {
      ledGeometryPolys(a).forEach(p => {
        if (p.pts.length < 2) return;
        const d = p.pts.map((q, k) => (k ? 'L' : 'M') + q.x.toFixed(2) + ' ' + q.y.toFixed(2)).join(' ');
        lines.push('  <path id="' + a.id + '-' + p.kind + '" d="' + d + (p.closed ? ' Z' : '') +
          '" stroke-width="' + (p.kind === 'hole' ? 0.6 : 1.2) + '" opacity="' + (p.kind === 'wall' ? 0.5 : 0.9) + '"/>');
      });
    });
    lines.push('</g>');
    lines.push('</svg>');
    return lines.join('\n');
  }

  function ledDxf() {
    const out = [];
    out.push('0', 'SECTION', '2', 'HEADER', '0', 'ENDSEC');
    out.push('0', 'SECTION', '2', 'ENTITIES');
    habitat.agents.filter(a => a.kind === 'weave').forEach(a => {
      ledGeometryPolys(a).forEach(p => {
        if (p.pts.length < 2) return;
        out.push('0', 'LWPOLYLINE', '8', p.kind, '90', String(p.pts.length), '70', p.closed ? '1' : '0');
        p.pts.forEach(q => {
          out.push('10', q.x.toFixed(3), '20', (-q.y).toFixed(3));   // DXF Y 轴向上，画布 Y 向下
        });
      });
    });
    out.push('0', 'ENDSEC', '0', 'EOF');
    return out.join('\n');
  }

  function ledDownload(name, text, mime) {
    const blob = new Blob([text], { type: mime || 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 4000);
  }

  function ledRenderCommand() {
    const r = ledResolve();
    return 'powershell -ExecutionPolicy Bypass -File scripts\\render_led_frames.ps1 -Html docs\\index.html ' +
      '-Scene led-scene.json -Native ' + r.w + 'x' + r.h + ' -Frames ' + r.frames + ' -Fps ' + r.fps +
      ' -OutDir "G:\\led-render\\frames" -Encode';
  }

  function bindLedPanel() {
    const on = (id, fn) => { const el = document.getElementById(id); if (el) el.addEventListener('click', fn); };
    on('habLedScene', () => {
      if (!habitat.agents.some(a => a.kind === 'weave')) { toast('还没有织网单元可导出。', 'err'); return; }
      ledDownload('led-scene.json', JSON.stringify(ledScene(), null, 2));
      toast('已导出 led-scene.json（母版渲染的输入）。', 'ok');
      hint('把 led-scene.json 和 docs/index.html 放同一目录，然后点「复制母版渲染命令」按提示跑。');
    });
    on('habLedCurves', () => {
      if (!habitat.agents.some(a => a.kind === 'weave')) { toast('还没有织网单元可导出。', 'err'); return; }
      ledDownload('weave-curves.json', JSON.stringify(ledCurves()));
      toast('已导出 weave-curves.json（Blender / TD 重建用）。', 'ok');
    });
    on('habLedGeom', () => {
      ledDownload('weave-cells.svg', ledSvg(), 'image/svg+xml');
      toast('已导出 weave-cells.svg（外框 / 圆孔 / 壁）。', 'ok');
    });
    on('habLedDxf', () => {
      ledDownload('weave-cells.dxf', ledDxf(), 'application/dxf');
      toast('已导出 weave-cells.dxf（Rhino / CAD 用）。', 'ok');
    });
    on('habLedCmd', () => {
      const cmd = ledRenderCommand();
      const done = () => { toast('命令已复制；先导出 led-scene.json 放在仓库根目录。', 'ok'); hint(cmd); };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(cmd).then(done, () => { hint(cmd); toast('复制被浏览器拒绝，命令已显示在下方提示条。', 'err'); });
      } else { hint(cmd); toast('命令已显示在提示条，手动复制。', 'err'); }
    });
    on('habVidRecord', () => { ledRecordWebVideo(); });
    on('habImgExport', () => { ledExportImage(); });
    const vidResSel = document.getElementById('habVidRes');
    const vidCustomRow = document.getElementById('habVidCustomRow');
    const vidWInput = document.getElementById('habVidW');
    const vidHInput = document.getElementById('habVidH');
    const vidRatioLabel = document.getElementById('habVidRatio');
    function syncVidResUI() {
      const custom = vidResSel && vidResSel.value === 'custom';
      if (vidCustomRow) vidCustomRow.style.display = custom ? 'block' : 'none';
      const d = habVidDims();
      if (vidRatioLabel) vidRatioLabel.textContent = habVidRatioOf(d.W, d.H) + ' · ' + d.W + '×' + d.H;
      const note = document.getElementById('habVidRatioNote');
      if (note) {
        const r = d.W / d.H;
        note.textContent = Math.abs(r - 4 / 3) < 0.02
          ? '屏体是 4:3（约 3.14 m × 2.36 m），当前比例正好，上屏不会加黑边。'
          : '当前比例不是 4:3。上屏会左右加黑边或被拉伸——要上屏请选 2048×1536 或 2093×1573。';
      }
    }
    if (vidResSel) vidResSel.addEventListener('change', syncVidResUI);
    if (vidWInput) vidWInput.addEventListener('input', syncVidResUI);
    if (vidHInput) vidHInput.addEventListener('input', syncVidResUI);
    syncVidResUI();
  }

  /* ============ 母版 native 渲染模式（?native=1） ============ */

  function ledB64Json(s) {
    const b64 = s.replace(/-/g, '+').replace(/_/g, '/');
    const bin = atob(b64 + '='.repeat((4 - b64.length % 4) % 4));
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return JSON.parse(new TextDecoder('utf-8').decode(bytes));
  }

  function ledAgentFromUnit(u) {
    return {
      id: 'led-' + u.order, kind: 'weave', mode: 'idle', bodyVisible: true,
      x: u.x, y: u.y, w: u.w, h: u.h,
      coverage: Number.isFinite(u.coverage) ? u.coverage : 0.55,
      scaleK: Number.isFinite(u.scaleK) ? u.scaleK : 0.9,
      shape: u.shape || 'island',
      worms: Number.isFinite(u.worms) ? u.worms : 6,
      wallAff: 0.6,
      seed: (u.seed >>> 0),
      tone: Number.isFinite(u.tone) ? u.tone : 0.85,
      gap: Number.isFinite(u.gap) ? u.gap : 8,
      strata: Math.max(1, Math.min(3, u.strata || 2)),
      outline: (Array.isArray(u.outline) && u.outline.length >= 3) ? u.outline : null,
      u: 0, duration: 30, speedScale: 1, tileField: false,
      silk: [], heading: 0, walls: [], paths: [],
      custom: u.custom || { walls: {}, paths: {}, shapes: {} },
      cache: null, sample: null,
    };
  }

  // 母版/网页录制共用的取景：把块群外接框按 94% 装进屏体，换分辨率构图不变形
  function ledFrameView(scene, W, H) {
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    scene.units.forEach(u => {
      minX = Math.min(minX, u.x - u.w / 2);
      maxX = Math.max(maxX, u.x + u.w / 2);
      minY = Math.min(minY, u.y - u.h / 2);
      maxY = Math.max(maxY, u.y + u.h / 2);
    });
    const bw = Math.max(1, maxX - minX), bh = Math.max(1, maxY - minY);
    const s = Math.min(W * 0.94 / bw, H * 0.94 / bh);
    const cxp = (minX + maxX) / 2;
    const cyp = (minY + maxY) / 2;
    return {
      w: W, h: H, s: s,
      cx: W / 2 - cxp * s,
      cy: H / 2 - cyp * s,
      px: x => W / 2 - cxp * s + x * s,
      py: y => H / 2 - cyp * s + y * s,
    };
  }

  // 合成一帧（离屏逐帧渲染和网页端录制都走这一条路径，避免两套画法不一致）
  // cache：可选的数组，按单元序号缓存建好的 agent；录制时复用，省掉每帧重建
  function ledComposeFrame(g, scene, T, isLoop, W, H, cache) {
    habitat.composing = true;          // 成品帧里不画编辑用的壁/手柄
    try {
    g.save();
    g.globalAlpha = 1;
    g.globalCompositeOperation = 'source-over';
    g.fillStyle = '#000';
    g.fillRect(0, 0, W, H);
    const v = ledFrameView(scene, W, H);
    const nUnits = Math.max(1, scene.units.length);
    const growFrac = 0.42, holdFrac = 0.88;
    // 收丝不回落到 0：块永远保留 62% 的丝量，否则循环里会出现"整块纯黑"的空洞，
    // 远看就是墙上少了几块砖。0.62 仍能看出"这一块刚被重新织过"的稀密变化。
    const uFloor = 0.62;
    scene.units.forEach((u, i) => {
      let agent = cache && cache[i];
      if (!agent) {
        agent = ledAgentFromUnit(u);
        buildWeave(agent);
        if (cache) cache[i] = agent;
      }
      if (isLoop) {
        // 相位用黄金比散开（0.618…），而不是 order/N —— 否则整行块会同时起落，看起来像"整排闪"
        const ord = u.order != null ? u.order : i;
        const ph = ((ord + 0.5) * 0.61803398875) % 1;
        const p = (T + ph) % 1;
        let lvl;
        if (p < growFrac) lvl = p / growFrac;
        else if (p < holdFrac) lvl = 1;
        else lvl = Math.max(0, 1 - (p - holdFrac) / (1 - holdFrac));
        agent.u = uFloor + (1 - uFloor) * lvl;
      } else {
        // 每块错开起织，避免整片同时亮起；顺序由 order 决定
        const delay = ((u.order != null ? u.order : i) % 7) * 0.045;
        agent.u = Math.max(0, Math.min(1, (T - delay) / (1 - delay || 1)));
      }
      drawWeave(g, agent, v);
    });
    g.restore();
    } finally {
      habitat.composing = false;
    }
  }

  function ledRenderNative() {
    const params = new URLSearchParams(location.search);
    const scene = window.__LED_SCENE || (params.get('scene') ? ledB64Json(params.get('scene')) : null);
    if (!scene || !Array.isArray(scene.units)) return false;
    // 分辨率优先级：URL 的 w/h（渲染脚本 -Native 传入）> 场景 px > 默认 2419×1360
    const qw = parseInt(params.get('w'), 10), qh = parseInt(params.get('h'), 10);
    const W = qw > 0 ? qw : (scene.px && scene.px.w ? scene.px.w : 2419);
    const H = qh > 0 ? qh : (scene.px && scene.px.h ? scene.px.h : 1360);
    const total = Math.max(1, parseInt(params.get('total'), 10) || (scene.frames || 900));
    const frame = Math.max(0, Math.min(total, parseInt(params.get('frame'), 10) || 0));
    // 循环片：周期正好是 total 帧，T = frame/total（第 total 帧才等价第 0 帧，
    // 所以序列里不会出现"末帧=首帧"的重复卡顿）；非循环片仍是 0→1 单程。
    const isLoop = scene.loop === true;
    const T = isLoop ? (frame / total) : (total <= 1 ? 1 : frame / (total - 1));

    document.body.innerHTML = '';
    document.body.style.cssText = 'margin:0;padding:0;background:#000;overflow:hidden;';
    const cv = document.createElement('canvas');
    cv.width = W; cv.height = H;
    cv.style.cssText = 'display:block;width:' + W + 'px;height:' + H + 'px;';
    document.body.appendChild(cv);
    const g = cv.getContext('2d');
    ledComposeFrame(g, scene, T, isLoop, W, H, null);
    return true;
  }

  // ===== 网页端直接出片：把同一套合成逻辑录成 WebM，不用回本地跑脚本 =====
  function ledVideoStatus(text) {
    const el = document.getElementById('habVidStatus');
    if (el) el.textContent = text;
  }

  function habVidRatioOf(w, h) {
    if (!w || !h) return '';
    const r = w / h;
    const near = [[4 / 3, '4:3'], [16 / 9, '16:9'], [21 / 9, '21:9'], [1, '1:1'], [3 / 2, '3:2'], [16 / 10, '16:10']]
      .find(([v]) => Math.abs(r - v) < 0.02);
    return near ? near[1] : (Math.round(r * 100) / 100) + ':1';
  }

  function habVidDims() {
    const sel = document.getElementById('habVidRes');
    const v = sel ? sel.value : '1920x1440';
    let W, H;
    if (v === 'custom') {
      const wi = document.getElementById('habVidW'), hi = document.getElementById('habVidH');
      W = parseInt(wi && wi.value, 10) || 2048;
      H = parseInt(hi && hi.value, 10) || 1536;
    } else {
      const parts = v.split('x');
      W = parseInt(parts[0], 10) || 1920;
      H = parseInt(parts[1], 10) || 1440;
    }
    // 夹在合理范围（4K 以内，避免显存/内存爆掉）；保留用户选的具体数值，不擅自改
    W = Math.max(320, Math.min(3840, W));
    H = Math.max(240, Math.min(2880, H));
    return { W, H };
  }

  function ledExportImage() {
    if (!habitat.agents.some(a => a.kind === 'weave')) {
      toast('还没有织网单元，先放一块再导出图片。', 'err');
      return;
    }
    const dims = habVidDims();
    const W = dims.W, H = dims.H;
    const scene = ledScene();
    scene.loop = false;
    const frames = Math.max(1, scene.frames || 900);
    const fps = Math.max(1, scene.fps || 30);
    const span = frames / fps;
    const T = Math.max(0, Math.min(1, (habitat.simTime || 0) / span));
    const cv = document.createElement('canvas');
    cv.width = W; cv.height = H;
    const g = cv.getContext('2d', { alpha: false });
    try {
      ledComposeFrame(g, scene, T, false, W, H, []);
    } catch (err) {
      const msg = '导出失败：' + (err && err.message ? err.message : String(err));
      const st = document.getElementById('habImgStatus');
      if (st) st.textContent = msg;
      toast(msg, 'err');
      return;
    }
    const name = 'weave_still_' + W + 'x' + H + '_' + Math.round(T * span) + 's.png';
    cv.toBlob((blob) => {
      const st = document.getElementById('habImgStatus');
      if (!blob) {
        if (st) st.textContent = '导出失败：这张图没生成出来，换个分辨率再试。';
        toast('导出失败：没有图片数据。', 'err');
        return;
      }
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = name;
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(url), 6000);
      const msg = '已导出 ' + name + '（' + W + '×' + H + '，' + (blob.size / 1048576).toFixed(1) + ' MB）';
      if (st) st.textContent = msg;
      toast('图片已导出：' + name, 'ok');
    }, 'image/png');
  }

  async function ledRecordWebVideo() {
    const btn = document.getElementById('habVidRecord');
    if (!habitat.agents.some(a => a.kind === 'weave')) {
      toast('还没有织网单元，先放一块再录。', 'err');
      return;
    }
    if (typeof MediaRecorder === 'undefined') {
      toast('这个浏览器不支持网页端录制（MediaRecorder 不可用）。', 'err');
      return;
    }
    const resSel = document.getElementById('habVidRes');
    const secSel = document.getElementById('habVidSec');
    const fpsSel = document.getElementById('habVidFps');
    const dims = habVidDims();
    const W = dims.W, H = dims.H;
    const secs = Math.max(2, parseInt(secSel ? secSel.value : '10', 10) || 10);
    const fps = Math.max(12, parseInt(fpsSel ? fpsSel.value : '30', 10) || 30);
    const total = Math.round(secs * fps);
    const bitSel = document.getElementById('habVidBit');
    const mbps = Math.max(4, Math.min(60, parseFloat(bitSel ? bitSel.value : '16') || 16));
    const bit = Math.round(mbps * 1e6);
    // 长片 / 母版分辨率：边录边写盘（File System Access），不把整段压在内存里
    let fileWriter = null, outName = 'weave_web_' + W + 'x' + H + '_' + secs + 's.webm';
    if ((secs > 30 || W * H > 2.2e6) && typeof window.showSaveFilePicker === 'function') {
      try {
        const handle = await window.showSaveFilePicker({
          suggestedName: outName,
          types: [{ description: 'WebM 视频', accept: { 'video/webm': ['.webm'] } }],
        });
        fileWriter = await handle.createWritable();
      } catch (err) { fileWriter = null; }   // 取消选择 → 退回内存方式
    }

    if (btn) { btn.disabled = true; btn.textContent = '录制中…'; }
    let rec = null;
    try {
      const scene = ledScene();
      scene.loop = true;               // 网页导出默认出循环片
      scene.frames = total;
      const cv = document.createElement('canvas');
      cv.width = W; cv.height = H;
      const g = cv.getContext('2d', { alpha: false });
      const cache = [];
      ledComposeFrame(g, scene, 0, true, W, H, cache);   // 先把 42 块建好，后面每帧只重画
      const mime = ['video/webm;codecs=vp9', 'video/webm;codecs=vp8', 'video/webm']
        .find(m => { try { return MediaRecorder.isTypeSupported(m); } catch (_) { return false; } }) || '';
      const stream = cv.captureStream(fps);
      rec = new MediaRecorder(stream, { mimeType: mime || undefined, videoBitsPerSecond: bit });
      const chunks = [];
      let writeChain = Promise.resolve();
      let composedFrames = 0;
      rec.ondataavailable = (ev) => {
        if (!ev.data || !ev.data.size) return;
        if (fileWriter) {
          const piece = ev.data;
          writeChain = writeChain.then(() => fileWriter.write(piece)).catch(() => {});
        } else chunks.push(ev.data);
      };
      const stopped = new Promise(resolve => { rec.onstop = resolve; });
      rec.start();

      const t0 = performance.now();
      let lastFrame = -1;
      await new Promise(resolve => {
        const step = () => {
          const el = (performance.now() - t0) / 1000;
          const f = Math.min(total, Math.floor(el * fps));
          if (f !== lastFrame) {
            ledComposeFrame(g, scene, f / total, true, W, H, cache);
            lastFrame = f;
            composedFrames++;
          }
          ledVideoStatus('录制中 ' + Math.min(100, Math.round(el / secs * 100)) + '% · 第 ' +
            Math.max(0, lastFrame) + '/' + total + ' 帧' + (W * H > 2.2e6 ? '（高分辨率，可能掉帧）' : ''));
          if (el >= secs) { resolve(); return; }
          requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
      });
      await new Promise(r => setTimeout(r, 120));   // 让最后一帧进流
      rec.stop();
      await stopped;
      if (fileWriter) {
        await writeChain;
        await fileWriter.close();
        const drop = Math.max(0, total - composedFrames);
        ledVideoStatus('已导出 ' + outName + '（' + W + '×' + H + ' / ' + fps + ' fps / ' + secs + ' 秒 / ' +
          mbps + ' Mbps）。实际绘制 ' + composedFrames + '/' + total + ' 帧' +
          (drop ? '，掉了 ' + drop + ' 帧：把分辨率或帧率降一档，或改成 30 fps。' : '，没有掉帧。'));
        toast('网页端视频已保存：' + outName, 'ok');
        return;
      }
      const blob = new Blob(chunks, { type: 'video/webm' });
      if (!blob.size) { toast('录制没有产出数据，换个分辨率再试。', 'err'); ledVideoStatus('录制失败：没有数据。'); return; }
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = outName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(url), 6000);
      const drop = Math.max(0, total - composedFrames);
      ledVideoStatus('已导出 ' + a.download + '（' + (blob.size / 1048576).toFixed(1) + ' MB，' +
        W + '×' + H + ' / ' + fps + ' fps / ' + secs + ' 秒 / ' + mbps + ' Mbps）。实际绘制 ' +
        composedFrames + '/' + total + ' 帧' + (drop ? '，掉了 ' + drop + ' 帧：把分辨率或帧率降一档。' : '，没有掉帧。'));
      toast('网页端视频已导出：' + a.download, 'ok');
    } catch (err) {
      ledVideoStatus('录制失败：' + (err && err.message ? err.message : String(err)));
      toast('网页端录制失败：' + (err && err.message ? err.message : String(err)), 'err');
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = '录制并下载视频（WebM）'; }
    }
  }

  function importHabitat(data) {
    if (!data) return;
    if (data.layerGroups && window.__layerStore && window.__layerStore.load) {
      setTimeout(() => window.__layerStore.load(data.layerGroups), 0);
    }
    if (Number.isFinite(data.temperatureC)) {
      habitat.tempC = data.temperatureC;
      document.getElementById('habTemp').value = data.temperatureC;
    }
    if (Number.isFinite(data.humidity)) {
      habitat.humidity = data.humidity;
      document.getElementById('habHum').value = data.humidity;
    }
    if (data.seed != null) habitat.seed = data.seed;
    if (Number.isFinite(data.simTime)) habitat.simTime = data.simTime;
    if (data.shape) {
      habitat.shape = data.shape;
      document.querySelectorAll('[data-shape]').forEach(b => b.classList.toggle('active', b.dataset.shape === data.shape));
    }
    habitat.tool = 'worm';
    habitat.obstacles = [];
    habitat.orphans = Array.isArray(data.orphanSilk) ? data.orphanSilk : [];
    habitat.reference = data.reference || null;
    habitat.selected = data.selected || null;
    habitat.selectedLeaf = data.selectedLeaf || null;
    if (Array.isArray(data.agents)) {
      habitat.agents = data.agents.map(a => {
        const agent = {
          id: a.id,
          kind: a.kind || 'random',
          wormId: a.wormId != null ? a.wormId : null,
          mode: a.mode || 'bench',
          bodyVisible: a.bodyVisible !== false,
          x: a.x || 0,
          y: a.y || 0,
          heading: a.heading || 0,
          phase: a.phase || 0,
          turnSign: a.turnSign || 1,
          silk: Array.isArray(a.silk) ? a.silk : [],
          route: Array.isArray(a.route) ? a.route : [],
          offX: Number.isFinite(a.offX) ? a.offX : 0,
          offY: Number.isFinite(a.offY) ? a.offY : 0,
          rot: Number.isFinite(a.rot) ? a.rot : 0,
          scale: Number.isFinite(a.scale) ? a.scale : 1,
          follow: !!a.follow,
          u: Number.isFinite(a.u) ? a.u : 0,
          color: a.color || '#d4c4a8',
          scope: a.scope === 'cell' ? 'cell' : 'field',
          homeUnitId: typeof a.homeUnitId === 'string' ? a.homeUnitId : null,
          speedScale: Number.isFinite(a.speedScale) ? Math.max(0.1, Math.min(3, a.speedScale)) : 1,
          pauseUntil: 0,
        };
        if (a.weave && typeof a.weave === 'object') {
          const wv = a.weave;
          agent.w = Number.isFinite(wv.w) ? Math.max(80, Math.min(340, wv.w)) : 200;
          agent.h = Number.isFinite(wv.h) ? Math.max(80, Math.min(340, wv.h)) : 200;
          agent.coverage = Number.isFinite(wv.coverage) ? wv.coverage : 0.55;
          agent.shape = wv.shape || 'island';
          agent.worms = Number.isFinite(wv.worms) ? wv.worms : 6;
          agent.seed = Number.isFinite(wv.seed) ? wv.seed : 1;
          agent.duration = Number.isFinite(wv.duration) ? wv.duration : 22;
          agent.wallAff = Number.isFinite(wv.wallAff) ? wv.wallAff : 0.6;
          agent.profile = (wv.profile && typeof wv.profile === 'object') ? wv.profile : null;
          agent.custom = (wv.custom && typeof wv.custom === 'object')
            ? { walls: wv.custom.walls || {}, paths: wv.custom.paths || {}, shapes: wv.custom.shapes || {} }
            : { walls: {}, paths: {}, shapes: {} };
          agent.tileField = !!wv.tileField;
          agent.tone = Number.isFinite(wv.tone) ? Math.max(0.4, Math.min(1.2, wv.tone)) : 0.85;
          agent.gap = Number.isFinite(wv.gap) ? Math.max(0, Math.min(40, wv.gap)) : 6;
          agent.strata = Number.isFinite(wv.strata) ? Math.max(1, Math.min(3, wv.strata)) : 2;
          agent.outline = (Array.isArray(wv.outline) && wv.outline.length >= 3)
            ? wv.outline.map(p => ({ x: p.x, y: p.y }))
            : null;
          agent.u = Number.isFinite(wv.u) ? wv.u : 0;
        }
        if (agent.kind === 'route' && agent.route.length >= 2) applyRouteTransform(agent);
        if (agent.kind === 'weave') {
          if (!agent.w) agent.w = 200;
          if (!agent.h) agent.h = 200;
          if (!agent.shape) agent.shape = 'island';
          if (!agent.seed) agent.seed = 1;
          if (!agent.custom) agent.custom = { walls: {}, paths: {} };
          buildWeave(agent);
        }
        return agent;
      });
    }
    renderList();
    renderDrive();
  }

  window.__studioHabitat = {
    export: exportHabitat, import: importHabitat, syncMeasured: syncMeasured,
    toast: toast, hint: hint,
    agents: () => habitat.agents,
    // 编辑态自检：当前在改哪一块、用什么工具、已经点了几个顶点
    weaveEditState: () => {
      const e = habitat.weaveEdit;
      if (!e) return null;
      return {
        agentId: e.agentId, ix: e.ix, iy: e.iy, mode: e.mode, tool: e.tool,
        drafts: Object.keys(e.drafts || {}).map(k => k + ':' + ((e.drafts[k] || []).length)),
      };
    },
    addWeave: addWeaveAgent,
    weaveCellContent: weaveCellContent,
    buildWeave: buildWeave,
    drawWeave: drawWeave,
    weavePathCum: weavePathCum,
    weaveCellSpecAt: weaveCellSpecAt,
    weaveThread: weaveThread,
    weaveTemplates: weaveTemplates,
    roamPoint: roamPoint,
    step: step,
    sampleRouteCentered: sampleRouteCentered,
    view: () => view(),
    ledScene: ledScene,
    ledCurves: ledCurves,
    ledSvg: ledSvg,
    ledDxf: ledDxf,
    ledRenderCommand: ledRenderCommand,
    ledComposeFrame: ledComposeFrame,
    ledExportImage: ledExportImage,
    ledRecordWebVideo: ledRecordWebVideo,
    seekTo: seekTo,
    undoStep: undoStep,
    redoStep: redoStep,
    importPointCloudDoc: importPointCloudDoc,
    assignWormToUnit: assignWormToUnit,
  };

  bindRoutePanel();
  bindLedPanel();

  // native 模式：URL 带 ?native=1 时只渲染一帧（母版出片用），不启动交互与动画
  if (new URLSearchParams(location.search).get('native') === '1' && ledRenderNative()) {
    return;
  }

  syncMeasured();
  lastMeasuredSig = measuredSignature();   // 首屏同步算一次，之后只在描图器真改了才重新同步
  renderList();
  syncHistoryUI();
  bindTimeSlider();
  function repaintStaticLayers() {
    paintStatic();
    paintDepth();
  }

  repaintStaticLayers();

  window.addEventListener(
    'resize',
    repaintStaticLayers
  );
  requestAnimationFrame(frame);
})();
