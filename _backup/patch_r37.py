# -*- coding: utf-8 -*-
"""r37：新增「上传一张图 → 自动识别排版 → 生成到场地」（纯新增，不改任何既有逻辑）"""
import io

P = r"H:\tool\silkworm-trajectory\docs\index.html"
s = io.open(P, encoding="utf-8").read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:80])
    s = s.replace(a, b)


# ---------- 1. 覆盖层画布（只画识别预览，不吃鼠标） ----------
rep("""      <canvas id="habDepth" class="depth" aria-hidden="true"></canvas>""",
"""      <canvas id="habDepth" class="depth" aria-hidden="true"></canvas>
      <canvas id="habRecOverlay" aria-hidden="true"></canvas>""")

rep("""#habCtxMenu{position:fixed;""",
"""#habRecOverlay{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:7}
#habCtxMenu{position:fixed;""")

# ---------- 2. 左栏新增一节（放在最末，默认折叠，不影响其他人操作） ----------
rep("""      <p class="hab-note" id="habImgStatus">还没导出。</p>
    </aside>""",
"""      <p class="hab-note" id="habImgStatus">还没导出。</p>
      <details id="habRecBox" class="hab-rec">
        <summary>从图片识别版式（上传一张图，自动铺块）</summary>
        <p class="hab-note">上传一张拼接好的丝片照片或设计稿：自动找出格子、几排几列、哪里缺块，以及格内的圆孔／缺口，先给你看预览，确认后再生成到场地。不影响场地里现有的东西。</p>
        <div class="row"><input type="file" id="habRecFile" accept="image/*"></div>
        <p class="hab-note" id="habRecImageNote">还没选图片。</p>
        <div class="row"><label>目标格边长</label><input type="range" id="habRecCell" min="120" max="900" step="10" value="320"><span class="hab-adj-val" id="habRecCellVal">320px</span></div>
        <div class="row"><label>识别孔洞</label><input type="checkbox" id="habRecHoles" checked><label>识别缺口</label><input type="checkbox" id="habRecNotches" checked></div>
        <div class="row"><button type="button" id="habRecRun">识别并预览</button><button type="button" id="habRecClear">清掉预览</button></div>
        <div class="row"><button type="button" id="habRecApply">生成到场地（新增）</button><button type="button" id="habRecReplace">替换现有块群</button></div>
        <p class="hab-note" id="habRecNote">只在你点按钮时才会动场地；识别本身不改任何东西。</p>
      </details>
    </aside>""")

# ---------- 3. 独立脚本（放在文件最后，只通过 window.__studioHabitat 操作） ----------
JS = r"""
<script>
/* ===== r37 图片识别（独立模块：不改任何既有函数，只新增） ===== */
(function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const ov = $('habRecOverlay');
  if (!ov) return;
  const octx = ov.getContext('2d');
  const S = () => window.__studioHabitat;
  const state = { img: null, boxes: [], holes: [], grid: null, busy: false };

  document.querySelectorAll && (function () {})();
  // 折叠区标题有点样式，保持和其它 h3 一致
  const box = $('habRecBox');
  if (box) box.style.marginTop = '14px';

  function say(t) { const el = $('habRecNote'); if (el) el.textContent = t; }
  function imgNote(t) { const el = $('habRecImageNote'); if (el) el.textContent = t; }

  function resizeOverlay() {
    const wrap = $('habWorldWrap');
    if (!wrap) return;
    const w = wrap.clientWidth, h = wrap.clientHeight;
    if (ov.width !== w || ov.height !== h) { ov.width = w; ov.height = h; }
    ov.style.width = w + 'px'; ov.style.height = h + 'px';
    const world = $('habWorld');
    if (world && world.style.left !== undefined) {
      const offX = world.offsetLeft, offY = world.offsetTop;
      ov.style.left = offX + 'px'; ov.style.top = offY + 'px';
    }
  }

  function drawOverlay() {
    const H = S();
    if (!H || !octx) return;
    resizeOverlay();
    octx.clearRect(0, 0, ov.width, ov.height);
    if (!state.boxes.length) return;
    const v = H.view();
    octx.save();
    state.boxes.forEach(b => {
      const x = v.px(b.wx - b.w / 2), y = v.py(b.wy - b.h / 2);
      const w = b.w * v.s, h = b.h * v.s;
      octx.strokeStyle = b.present ? 'rgba(121,203,182,0.95)' : 'rgba(255,120,120,0.5)';
      octx.lineWidth = 1.2;
      octx.setLineDash(b.present ? [] : [4, 4]);
      octx.strokeRect(x, y, w, h);
      if (b.present) {
        octx.fillStyle = 'rgba(121,203,182,0.06)';
        octx.fillRect(x, y, w, h);
      }
    });
    octx.setLineDash([]);
    state.holes.forEach(h => {
      const cx = v.px(h.wx), cy = v.py(h.wy), r = h.wr * v.s;
      octx.beginPath();
      octx.arc(cx, cy, r, 0, Math.PI * 2);
      octx.strokeStyle = 'rgba(232,201,138,0.9)';
      octx.lineWidth = 1.1;
      octx.stroke();
    });
    octx.restore();
  }

  function tick() { drawOverlay(); requestAnimationFrame(tick); }
  requestAnimationFrame(tick);

  // 读图 → 缩到长边 ≤1400 → 灰度数组
  function readImage(file, cb) {
    const fr = new FileReader();
    fr.onload = () => {
      const im = new Image();
      im.onload = () => {
        const maxSide = 1400;
        const k = Math.min(1, maxSide / Math.max(im.width, im.height));
        const w = Math.max(1, Math.round(im.width * k));
        const h = Math.max(1, Math.round(im.height * k));
        const cv = document.createElement('canvas');
        cv.width = w; cv.height = h;
        const cx = cv.getContext('2d');
        cx.drawImage(im, 0, 0, w, h);
        const d = cx.getImageData(0, 0, w, h).data;
        const g = new Uint8Array(w * h);
        for (let i = 0, p = 0; i < g.length; i++, p += 4) g[i] = (d[p] * 0.299 + d[p + 1] * 0.587 + d[p + 2] * 0.114) | 0;
        state.img = { w, h, g };
        cb && cb();
      };
      im.onerror = () => imgNote('这张图片读不出来，换一张 png / jpg 试试。');
      im.src = fr.result;
    };
    fr.onerror = () => imgNote('文件读取失败。');
    fr.readAsDataURL(file);
  }

  function otsu(g) {
    const hist = new Int32Array(256);
    for (let i = 0; i < g.length; i++) hist[g[i]]++;
    const total = g.length;
    let sum = 0;
    for (let t = 0; t < 256; t++) sum += t * hist[t];
    let sumB = 0, wB = 0, best = 0, thr = 128;
    for (let t = 0; t < 256; t++) {
      wB += hist[t];
      if (!wB) continue;
      const wF = total - wB;
      if (!wF) break;
      sumB += t * hist[t];
      const mB = sumB / wB, mF = (sum - sumB) / wF;
      const between = wB * wF * (mB - mF) * (mB - mF);
      if (between > best) { best = between; thr = t; }
    }
    return thr;
  }

  function seamsOf(profile, minGap, minLen) {
    // profile: 每列（或每行）的亮像素数。回廊式找"暗缝"的区间中心
    const n = profile.length;
    let mx = 0;
    for (let i = 0; i < n; i++) mx = Math.max(mx, profile[i]);
    if (!mx) return [];
    const thr = mx * 0.22;
    const out = [];
    let runStart = -1;
    for (let i = 0; i < n; i++) {
      const dark = profile[i] <= thr;
      if (dark && runStart < 0) runStart = i;
      if ((!dark || i === n - 1) && runStart >= 0) {
        const end = dark ? i : i - 1;
        const len = end - runStart + 1;
        if (len >= minGap && len <= minLen) out.push(Math.round((runStart + end) / 2));
        runStart = -1;
      }
    }
    return out;
  }

  function intervals(seams, minW, maxW) {
    const cuts = [0].concat(seams, [null]);
    const out = [];
    for (let i = 0; i < cuts.length - 1; i++) {
      const a = i === 0 ? 0 : seams[i - 1];
      const b = i === cuts.length - 2 ? null : seams[i];
      if (b == null) continue;
      const w = b - a;
      if (w >= minW && w <= maxW) out.push({ a, b });
    }
    return out;
  }

  // 主识别
  function analyse() {
    const im = state.img;
    if (!im) { say('先选一张图片。'); return; }
    const { w, h, g } = im;
    const thr = otsu(g);
    const mask = new Uint8Array(w * h);
    for (let i = 0; i < mask.length; i++) mask[i] = g[i] > thr ? 1 : 0;

    // 列 / 行投影
    const px = new Int32Array(w), py = new Int32Array(h);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) if (mask[y * w + x]) { px[x]++; py[y]++; }
    const sx = seamsOf(px, 2, Math.max(6, Math.round(w * 0.03)));
    const sy = seamsOf(py, 2, Math.max(6, Math.round(h * 0.03)));

    say('阈值 ' + thr + ' · 竖缝 ' + sx.length + ' 条 · 横缝 ' + sy.length + ' 条');

    // 组成格网：相邻缝之间是"格带"
    const cols = [], rows = [];
    for (let i = 0; i < sx.length - 1; i++) cols.push({ a: sx[i], b: sx[i + 1] });
    for (let i = 0; i < sy.length - 1; i++) rows.push({ a: sy[i], b: sy[i + 1] });
    if (!cols.length || !rows.length) { say('没找到格线（缝太淡或图太糊）。可以换一张更清晰的，或手动铺块。'); return; }

    // 每格亮面占比 → 判断这块在不在
    function cover(cx0, cx1, cy0, cy1) {
      let on = 0, tot = 0;
      for (let y = cy0; y < cy1; y += 2) for (let x = cx0; x < cx1; x += 2) { tot++; if (mask[y * w + x]) on++; }
      return tot ? on / tot : 0;
    }

    const pitchX = (function () { const d = []; for (let i = 1; i < cols.length; i++) d.push(cols[i].a - cols[i - 1].a); d.sort((a, b) => a - b); return d.length ? d[Math.floor(d.length / 2)] : 0; })();
    const pitchY = (function () { const d = []; for (let i = 1; i < rows.length; i++) d.push(rows[i].a - rows[i - 1].a); d.sort((a, b) => a - b); return d.length ? d[Math.floor(d.length / 2)] : 0; })();
    const T = Number(($('habRecCell') || {}).value || 320);
    const scale = pitchX > 0 ? T / pitchX : 1;
    const stepX = pitchX * scale, stepY = pitchY * scale;
    const midC = (cols.length - 1) / 2, midR = (rows.length - 1) / 2;

    const boxes = [], holes = [];
    const wantHoles = !!($('habRecHoles') || {}).checked;
    const wantNotch = !!($('habRecNotches') || {}).checked;
    let present = 0;

    rows.forEach((r, ri) => {
      cols.forEach((c, ci) => {
        const cov = cover(c.a + 1, c.b - 1, r.a + 1, r.b - 1);
        const on = cov > 0.38;
        if (on) present++;
        const bw = (c.b - c.a) * scale, bh = (r.b - r.a) * scale;
        const wx = (ci - midC) * stepX, wy = (ri - midR) * stepY;
        const b = { present: on, wx, wy, w: bw, h: bh, ci, ri, cx: (c.a + c.b) / 2, cy: (r.a + r.b) / 2, cw: c.b - c.a, ch: r.b - r.a, islands: [], notchPts: null };
        boxes.push(b);
        if (!on) return;

        // 格内暗区（孔洞 / 边缘咬口）：从格内 mask 里找"不属于亮面"的连通块
        if (!wantHoles && !wantNotch) return;
        const x0 = c.a + 2, x1 = c.b - 2, y0 = r.a + 2, y1 = r.b - 2;
        const W = x1 - x0, H2 = y1 - y0;
        if (W <= 2 || H2 <= 2) return;
        const dm = new Uint8Array(W * H2);
        for (let y = 0; y < H2; y++) for (let x = 0; x < W; x++) dm[y * W + x] = mask[(y0 + y) * w + (x0 + x)] ? 0 : 1;
        const seen = new Uint8Array(W * H2);
        const stack = [];
        const cellArea = W * H2;
        for (let y = 0; y < H2; y++) {
          for (let x = 0; x < W; x++) {
            const idx = y * W + x;
            if (!dm[idx] || seen[idx]) continue;
            let sx2 = 0, sy2 = 0, cnt = 0, edge = false;
            const list = [];
            stack.length = 0; stack.push(idx); seen[idx] = 1;
            while (stack.length) {
              const q = stack.pop();
              const qx = q % W, qy = (q - qx) / W;
              cnt++; sx2 += qx; sy2 += qy; list.push(q);
              if (qx === 0 || qy === 0 || qx === W - 1 || qy === H2 - 1) edge = true;
              if (list.length > cellArea) break;
              if (qx > 0 && dm[q - 1] && !seen[q - 1]) { seen[q - 1] = 1; stack.push(q - 1); }
              if (qx < W - 1 && dm[q + 1] && !seen[q + 1]) { seen[q + 1] = 1; stack.push(q + 1); }
              if (qy > 0 && dm[q - W] && !seen[q - W]) { seen[q - W] = 1; stack.push(q - W); }
              if (qy < H2 - 1 && dm[q + W] && !seen[q + W]) { seen[q + W] = 1; stack.push(q + W); }
            }
            const frac = cnt / cellArea;
            if (frac < 0.035 || frac > 0.85) continue;
            const ccx = sx2 / cnt, ccy = sy2 / cnt;
            const rr = Math.sqrt(cnt / Math.PI);
            const gw = (x0 + ccx - b.cx) * scale;
            const gh = (y0 + ccy - b.cy) * scale;
            const wrr = rr * scale;
            if (edge && wantNotch) {
              // 咬在边上的口子：同样用圆的负空间表示（画的时候会被格边裁掉，看起来就是缺口）
              b.islands.push({ cx: gw, cy: gh, r: wrr });
            } else if (!edge && wantHoles) {
              b.islands.push({ cx: gw, cy: gh, r: wrr });
            }
            if (b.islands.length >= 6) break;
          }
          if (b.islands.length >= 6) break;
        }
        b.islands.forEach(is2 => holes.push({ wx: wx + is2.cx, wy: wy + is2.cy, wr: is2.r }));
      });
    });

    state.boxes = boxes;
    state.holes = holes;
    state.grid = { cols: cols.length, rows: rows.length, present, pitchX, pitchY, scale };
    say('认出 ' + cols.length + ' 列 × ' + rows.length + ' 排，其中 ' + present + ' 块有丝、' + (boxes.length - present) + ' 个格位是空的；' +
      '圆孔／咬口 ' + holes.length + ' 个。' + '确认没问题就点「生成到场地」。');
  }

  // 生成
  function apply(replace) {
    const H = S();
    if (!H) return;
    if (!state.boxes.length) { say('先点「识别并预览」。'); return; }
    let units = H.agents().filter(a => a.kind === 'weave');
    if (replace && window.__weaveHooks && window.__weaveHooks.deleteUnit) {
      units.slice().forEach(u => window.__weaveHooks.deleteUnit(u.id));
      units = [];
    }
    let made = 0;
    state.boxes.filter(b => b.present).forEach((b, i) => {
      const before = H.agents().filter(a => a.kind === 'weave').length;
      H.addWeave({});
      const list = H.agents().filter(a => a.kind === 'weave');
      if (list.length <= before) return;
      const u = list[list.length - 1];
      u.w = Math.max(80, Math.round(b.w));
      u.h = Math.max(80, Math.round(b.h));
      u.x = Math.round(b.wx);
      u.y = Math.round(b.wy);
      u.tileField = false;
      u.shape = 'plain';
      u.seed = 1000 + i * 37;
      if (b.islands.length) {
        u.custom = u.custom || { walls: {}, paths: {}, shapes: {} };
        if (!u.custom.shapes) u.custom.shapes = {};
        u.custom.shapes['0,0'] = { notch: null, islands: b.islands.map(o => ({ cx: Math.round(o.cx), cy: Math.round(o.cy), r: Math.round(o.r) })) };
      }
      if (u.cache && u.cache.clear) u.cache.clear();
      H.buildWeave(u);
      made++;
    });
    say('已经生成 ' + made + ' 块（每块按识别到的位置与孔洞铺好）。可以直接拖白点改形状；不满意用 Ctrl+Z 或「清掉预览」后重来。');
  }

  // 事件
  const fileEl = $('habRecFile');
  if (fileEl) fileEl.addEventListener('change', () => {
    const f = fileEl.files && fileEl.files[0];
    if (!f) return;
    imgNote('读图中：' + f.name);
    readImage(f, () => {
      imgNote('已载入 ' + state.img.w + '×' + state.img.h + '（缩放后）。点「识别并预览」。');
      state.boxes = []; state.holes = [];
    });
  });
  const cellEl = $('habRecCell');
  if (cellEl) cellEl.addEventListener('input', () => {
    const el = $('habRecCellVal'); if (el) el.textContent = cellEl.value + 'px';
  });
  const runEl = $('habRecRun');
  if (runEl) runEl.addEventListener('click', () => {
    if (!state.img) { say('先选一张图片。'); return; }
    try { analyse(); } catch (e) { say('识别出错：' + e.message); }
  });
  const clearEl = $('habRecClear');
  if (clearEl) clearEl.addEventListener('click', () => {
    state.boxes = []; state.holes = []; say('预览已清掉，场地没有任何改动。');
  });
  const applyEl = $('habRecApply');
  if (applyEl) applyEl.addEventListener('click', () => { try { apply(false); } catch (e) { say('生成出错：' + e.message); } });
  const repEl = $('habRecReplace');
  if (repEl) repEl.addEventListener('click', () => {
    if (!confirm('会先删掉场地上现有的织网单元，再按识别结果铺满。确定？')) return;
    try { apply(true); } catch (e) { say('生成出错：' + e.message); }
  });
  // 给外部 QA 留一个只读入口
  window.__imgRec = { analyse, apply, state, readImage };
})();
</script>
</body>"""

rep("""</body>""", JS)

io.open(P, "w", encoding="utf-8").write(s)
print("r37 patched")
