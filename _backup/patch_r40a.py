# -*- coding: utf-8 -*-
import io

MOD = r"H:\tool\silkworm-trajectory\_backup\r39_module.js"
P = r"H:\tool\silkworm-trajectory\docs\index.html"
s = io.open(MOD, encoding="utf-8").read()

# ---- 1) 行内加缩略图与副信息 ----
old_row = """  function rowHTML(a, gid) {
    const off = hiddenOf(a);
    return '<div class="lay-row' + (off ? ' dim' : '') + (sel.has(a.id) ? ' on' : '') + '" data-agent="' + a.id + '">' +
      '<input type="checkbox" class="lay-chk" data-pick="' + a.id + '"' + (sel.has(a.id) ? ' checked' : '') + '>' +
      '<span class="lay-icon">' + iconOf(a) + '</span>' +
      '<button type="button" class="lay-name" title="选中这一层" data-focus="' + a.id + '">' + nameOf(a) + '</button>' +"""
new_row = """  function metaOf(a) {
    if (a.kind === 'weave') {
      const w = Math.round(a.w || 0), h = Math.round(a.h || 0);
      const worms = Math.round(a.worms || 0);
      return w + '×' + h + (worms ? ' · ' + worms + ' 蚕/格' : '');
    }
    if (a.kind === 'route') return (Math.round(a.scale * 100) / 100) + '× · ' + a.route.length + ' 点';
    return a.mode || '';
  }
  function rowHTML(a, gid) {
    const off = hiddenOf(a);
    return '<div class="lay-row' + (off ? ' dim' : '') + (sel.has(a.id) ? ' on' : '') + '" data-agent="' + a.id + '">' +
      '<input type="checkbox" class="lay-chk" data-pick="' + a.id + '"' + (sel.has(a.id) ? ' checked' : '') + '>' +
      '<canvas class="lay-thumb" width="40" height="40" data-thumb="' + a.id + '"></canvas>' +
      '<span class="lay-txt"><button type="button" class="lay-name" title="选中这一层" data-focus="' + a.id + '">' + iconOf(a) + ' ' + nameOf(a) + '</button>' +
      '<i class="lay-meta">' + metaOf(a) + '</i></span>' +"""
assert s.count(old_row) == 1
s = s.replace(old_row, new_row)

# 组行头也带一枚缩略图位（留白，避免错位）
s = s.replace("""        '<button type="button" class="lay-caret" data-open="' + g.id + '">' + (g.open ? '▾' : '▸') + '</button>' +""",
"""        '<button type="button" class="lay-caret" data-open="' + g.id + '">' + (g.open ? '▾' : '▸') + '</button>' +
        '<span class="lay-gicon">组</span>' +""")

# ---- 2) 缩略图绘制（直接抠主画布，所见即所得） ----
thumb = """
  /* ---------- 缩略图：从主画布裁剪 ---------- */
  function paintThumbs() {
    const world = $('habWorld');
    if (!world || !H()) return;
    const v = H().view();
    const cw = world.width, chh = world.height;
    const rect = world.getBoundingClientRect();
    const kx = cw / (rect.width || 1), ky = chh / (rect.height || 1);
    document.querySelectorAll('#habLayerTree canvas[data-thumb]').forEach(cv => {
      const a = byId(cv.getAttribute('data-thumb'));
      const ctx = cv.getContext('2d');
      ctx.clearRect(0, 0, cv.width, cv.height);
      if (!a || a.kind !== 'weave') { ctx.fillStyle = 'rgba(255,255,255,0.06)'; ctx.fillRect(0, 0, cv.width, cv.height); return; }
      const sx = v.px(a.x - a.w / 2) * kx, sy = v.py(a.y - a.h / 2) * ky;
      const sw = a.w * v.s * kx, sh = a.h * v.s * ky;
      if (sw < 2 || sh < 2) return;
      try {
        ctx.fillStyle = '#05080a';
        ctx.fillRect(0, 0, cv.width, cv.height);
        ctx.drawImage(world, sx, sy, sw, sh, 0, 0, cv.width, cv.height);
        ctx.strokeStyle = 'rgba(255,255,255,0.14)';
        ctx.strokeRect(0.5, 0.5, cv.width - 1, cv.height - 1);
      } catch (e) {}
    });
  }
  setInterval(() => { const p = $('habRight'); if (p && p.offsetParent) paintThumbs(); }, 1200);
"""
anchor2 = """  /* ---------- 与主界面同步 ---------- */"""
assert s.count(anchor2) == 1
s = s.replace(anchor2, thumb + anchor2)

# render 末尾补一次绘制
s = s.replace("""    tree.innerHTML = out.join('');
  }""", """    tree.innerHTML = out.join('');
    paintThumbs();
  }""", 1)

# ---- 3) 编辑态也能整组拖：只在压到手柄附近时才让给原生手柄 ----
old_edit = """  function inEditMode() {
    try { const st = H().weaveEditState && H().weaveEditState(); return !!(st && st.agentId); } catch (e) { return false; }
  }"""
new_edit = """  function inEditMode() {
    try { const st = H().weaveEditState && H().weaveEditState(); return !!(st && st.agentId); } catch (e) { return false; }
  }
  // 编辑态里，手柄（角/边中点/中心）附近要点就给原生手柄，别抢
  function nearHandle(a, p) {
    const v = H().view();
    const pts = [
      [a.x, a.y],
      [a.x - a.w / 2, a.y - a.h / 2], [a.x + a.w / 2, a.y - a.h / 2],
      [a.x - a.w / 2, a.y + a.h / 2], [a.x + a.w / 2, a.y + a.h / 2],
      [a.x, a.y - a.h / 2], [a.x, a.y + a.h / 2],
      [a.x - a.w / 2, a.y], [a.x + a.w / 2, a.y],
    ];
    return pts.some(q => Math.hypot(q[0] - p.x, q[1] - p.y) * v.s < 22);
  }"""
assert s.count(old_edit) == 1
s = s.replace(old_edit, new_edit)

old_pd = """      if (inEditMode()) return;               // 编辑态交给原生手柄
      const p = toWorld(e);
      const hit = hitWeave(p);
      if (!hit) return;"""
new_pd = """      const p = toWorld(e);
      const hit = hitWeave(p);
      if (!hit) return;
      if (inEditMode() && nearHandle(hit, p)) return;   // 压在手柄上：交给原生拖拽
      if (inEditMode() && sel.size < 2 && !groupOf(hit.id)) return; // 编辑单块：交给原生"""
assert s.count(old_pd) == 1
s = s.replace(old_pd, new_pd)

io.open(MOD, "w", encoding="utf-8").write(s)

# ---- 4) 注入到页面 + CSS ----
h = io.open(P, encoding="utf-8").read()
i = h.find("/* ===== r39 个体与图层合并"); st = h.rfind("<script>", 0, i); en = h.find("</script>", i)
h = h[:st] + s.rstrip() + h[en + len("</script>"):]

old_css = ".hab-rec-bar{padding:6px 14px 0}"
new_css = """
/* r40：识别条浮在画布上，不再占高度 */
#habitat { position: relative; }
.hab-rec-bar{position:absolute;left:12px;top:54px;z-index:9;width:min(620px,calc(100% - 200px));padding:0}
.hab-rec{background:rgba(10,16,18,.94);border:1px solid rgba(230,236,233,.16);border-radius:8px;box-shadow:0 8px 20px rgba(0,0,0,.45);backdrop-filter:blur(6px)}
.hab-rec>summary{padding:5px 9px;font-size:12px;gap:8px}
.hab-rec-body{max-height:52vh;overflow:auto;padding:6px 9px 10px}
/* r40：层行缩略图与副信息 */
.lay-thumb{width:26px;height:26px;flex:0 0 26px;border-radius:3px;background:#05080a;border:1px solid rgba(255,255,255,.08)}
.lay-txt{flex:1 1 auto;min-width:0;display:flex;flex-direction:column;gap:1px}
.lay-txt .lay-name{font-size:12px;line-height:1.25}
.lay-meta{font-size:10px;font-style:normal;opacity:.5;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lay-gicon{width:26px;flex:0 0 26px;text-align:center;font-size:10px;opacity:.45}"""
assert h.count(old_css) == 1
h = h.replace(old_css, new_css)
io.open(P, "w", encoding="utf-8").write(h)
print("r40 module+css ok", len(h))
