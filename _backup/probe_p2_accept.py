# -*- coding: utf-8 -*-
"""P2 验收探针（同步执行，便于无头截图取到结果与真实计时）。

覆盖：60 格 3 层性能、生长中性能、同 seed 一致、覆盖单调（按渲染亮度）、
圆孔内无丝 + 洞缘密度、首帧/末帧亮度、30s 动画连续性。

用法：python _backup\probe_p2_accept.py docs\index.html C:\Temp\qa-p2.html
"""

import sys
from pathlib import Path

TMPL = r"""
<style>
  body > *:not(#habitat):not(script):not(style) { display: none !important; }
  #qaOut { position: fixed; left: 12px; top: 12px; z-index: 99999; background: #0d120f;
    color: #d9efe6; font: 12px/1.5 Consolas, monospace; padding: 10px 13px;
    white-space: pre-wrap; max-width: 97vw; max-height: 97vh; overflow: auto; }
  #qaCanvas { position: fixed; right: 10px; bottom: 10px; width: 300px; height: 300px;
    border: 1px solid #2a2f2a; }
</style>
<script>
(function () {
  function makeUnit(x, y, seed, cov, strata) {
    return {
      id: 'qa-' + seed + '-' + Math.round(x), kind: 'weave', mode: 'idle', bodyVisible: true,
      x: x, y: y, w: 200, h: 200, coverage: cov, shape: 'island', worms: 6, wallAff: 0.6,
      seed: seed, tone: 0.85, gap: 8, strata: strata || 3, outline: null, u: 0, duration: 30,
      speedScale: 1, tileField: false, silk: [], heading: 0, walls: [], paths: [],
      custom: { walls: {}, paths: {}, shapes: {} }, cache: null, sample: null
    };
  }
  function lumOf(g, x, y, w, h) {
    const d = g.getImageData(x, y, w, h).data;
    let sum = 0;
    for (let i = 0; i < d.length; i += 4) sum += d[i];
    return sum / (d.length / 4);
  }
  function run() {
    const H = window.__studioHabitat;
    const out = [];
    try { main(H, out); } catch (e) { out.push('probe error: ' + (e && e.message ? e.message : e)); }
    const pre = document.createElement('pre');
    pre.id = 'qaOut';
    pre.textContent = out.join('\n');
    document.getElementById('habitat').appendChild(pre);
  }
  function main(H, out) {
    if (!H || !H.drawWeave) { out.push('缺少 drawWeave 导出'); return; }
    const v = { w: 1000, h: 1000, s: 1.0, cx: 500, cy: 500, px: x => 500 + x, py: y => 500 + y };
    const cv = document.createElement('canvas');
    cv.width = 1000; cv.height = 1000; cv.id = 'qaCanvas';
    const g = cv.getContext('2d');

    // 1) 60 格 × 3 层，1000px 预览性能（满织，位图缓存）
    const units = [];
    for (let r = 0; r < 10; r++) for (let c = 0; c < 6; c++) {
      const a = makeUnit((c - 2.5) * 96, (r - 4.5) * 96, 20261116 + r * 6 + c, 0.6, 3);
      H.buildWeave(a); units.push(a);
    }
    units.forEach(a => { a.u = 1; });
    for (let i = 0; i < 3; i++) { g.clearRect(0, 0, 1000, 1000); units.forEach(a => H.drawWeave(g, a, v)); }
    let t0 = performance.now(), N = 12;
    for (let i = 0; i < N; i++) { g.clearRect(0, 0, 1000, 1000); units.forEach(a => H.drawWeave(g, a, v)); }
    const msFull = (performance.now() - t0) / N;
    out.push('60 格 × 3 层 @u=1（满织）: ' + msFull.toFixed(2) + ' ms/帧 → ' + (1000 / msFull).toFixed(1) + ' fps');

    const c0 = H.weaveCellContent(units[0], 0, 0);
    out.push('单格 paths=' + c0.paths.length + ' pts=' + c0.paths.reduce((s, p) => s + p.pts.length, 0) + ' walls=' + c0.walls.length);

    // 生长中（u=0.55）12 格外推 60 格
    const mid = units.slice(0, 12);
    mid.forEach(a => { a.u = 0.55; a.cache = null; H.buildWeave(a); });
    for (let i = 0; i < 2; i++) { g.clearRect(0, 0, 1000, 1000); mid.forEach(a => H.drawWeave(g, a, v)); }
    t0 = performance.now();
    for (let i = 0; i < 4; i++) { g.clearRect(0, 0, 1000, 1000); mid.forEach(a => H.drawWeave(g, a, v)); }
    const msMid12 = (performance.now() - t0) / 4;
    out.push('12 格 @u=0.55（逐笔重画）: ' + msMid12.toFixed(2) + ' ms/帧 → 60 格外推 ' +
      (msMid12 * 5).toFixed(1) + ' ms/帧（' + (1000 / (msMid12 * 5)).toFixed(1) + ' fps）');

    // 2) 同 seed 两次逐点一致
    const d1 = makeUnit(0, 0, 424242, 0.6), d2 = makeUnit(0, 0, 424242, 0.6);
    H.buildWeave(d1); H.buildWeave(d2);
    const k1 = H.weaveCellContent(d1, 0, 0), k2 = H.weaveCellContent(d2, 0, 0);
    let diffPts = 0;
    if (k1.paths.length === k2.paths.length) {
      k1.paths.forEach((p, i) => {
        const q = k2.paths[i];
        if (!q || p.pts.length !== q.pts.length) { diffPts += 999; return; }
        for (let j = 0; j < p.pts.length; j++) if (p.pts[j].x !== q.pts[j].x || p.pts[j].y !== q.pts[j].y) diffPts++;
      });
    } else diffPts += 999;
    out.push('同 seed：paths ' + k1.paths.length + '/' + k2.paths.length + '，不一致点 ' + diffPts + ' → ' + (diffPts === 0 ? '一致 OK' : '不一致 FAIL'));

    // 3) 覆盖 0.2→0.7：渲染亮度应单调
    const covs = [0.2, 0.35, 0.5, 0.65, 0.7];
    const covLum = covs.map(cv2 => {
      const a = makeUnit(0, 0, 777001, cv2, 1);
      H.buildWeave(a); a.u = 1;
      g.clearRect(0, 0, 1000, 1000);
      H.drawWeave(g, a, v);
      return lumOf(g, 400, 400, 200, 200);
    });
    const mono = covLum.every((x, i) => i === 0 || x > covLum[i - 1]);
    out.push('覆盖 0.2/0.35/0.5/0.65/0.7 亮度: ' + covLum.map(x => x.toFixed(1)).join(' → ') + ' → ' + (mono ? '单调 OK' : '非单调 FAIL'));

    // 4) 圆孔内无丝 + 洞缘更密（按面积算密度）
    const iu = makeUnit(0, 0, 9001, 0.6, 2);
    H.buildWeave(iu);
    const ic = H.weaveCellContent(iu, 0, 0);
    const isl = (ic.cell.islands || [])[0];
    if (isl) {
      let inHole = 0, total = 0, ring = 0, far = 0;
      const wCell = Math.min(ic.cell.w, ic.cell.h);
      ic.paths.forEach(p => p.pts.forEach(q => {
        total++;
        const d = Math.hypot(q.x - isl.cx, q.y - isl.cy);
        if (d < isl.r - 2) inHole++;
        else if (d < isl.r + wCell * 0.08) ring++;
        else if (d > wCell * 0.33) far++;
      }));
      const ringArea = Math.PI * ((isl.r + wCell * 0.08) ** 2 - isl.r ** 2);
      const farArea = ic.cell.w * ic.cell.h - Math.PI * (wCell * 0.33) ** 2;
      out.push('圆孔 r=' + Math.round(isl.r) + '：孔内点 ' + inHole + '/' + total +
        '；洞缘 ' + ring + ' 点/区 → ' + (ring / ringArea * 1000).toFixed(1) +
        ' vs 远区 ' + far + ' 点/区 → ' + (far / farArea * 1000).toFixed(1) + '（/1000 面积）');
    } else out.push('该块无圆孔');

    // 5) 首帧只有壁、末帧满网
    const frameLum = u => {
      const a = makeUnit(0, 0, 5150, 0.6, 2);
      a.u = u; H.buildWeave(a);
      g.clearRect(0, 0, 1000, 1000);
      H.drawWeave(g, a, v);
      return lumOf(g, 400, 400, 200, 200);
    };
    out.push('u=0 亮度 ' + frameLum(0).toFixed(1) + ' → u=1 亮度 ' + frameLum(0.999).toFixed(1));

    // 6) 30s 动画：u 单调、无回退、无跳变
    const anim = makeUnit(0, 0, 31337, 0.6, 2);
    anim.u = 0; anim.mode = 'run'; anim.duration = 30;
    H.buildWeave(anim);
    H.agents().push(anim);   // step() 只遍历 habitat.agents
    let lastU = 0, back = 0, maxJump = 0; const samples = [];
    for (let f = 0; f < 1800; f++) {
      H.step(1 / 60);
      const du = anim.u - lastU;
      if (du < -1e-9) back++;
      if (du > maxJump) maxJump = du;
      lastU = anim.u;
      if (f % 300 === 0) samples.push(anim.u.toFixed(2));
    }
    const idxA = H.agents().indexOf(anim);
    if (idxA >= 0) H.agents().splice(idxA, 1);
    out.push('30s@60fps u: ' + samples.join(' → ') + ' 终值 ' + anim.u.toFixed(2) +
      '，回退帧 ' + back + '，单帧最大增量 ' + maxJump.toFixed(4));

    document.getElementById('habitat').appendChild(cv);
  }
  window.addEventListener('load', run);
})();
</script>
"""


def main():
    src = Path(sys.argv[1]).read_text(encoding="utf-8")
    dst = Path(sys.argv[2])
    idx = src.rfind("</body>")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src[:idx] + TMPL + src[idx:], encoding="utf-8")
    print(f"{dst} {dst.stat().st_size}")


if __name__ == "__main__":
    main()
