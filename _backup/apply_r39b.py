import io
p = r"_backup\r39_module.js"
s = io.open(p, encoding="utf-8").read()

anchor = """  if (worldEl) {
    worldEl.addEventListener('pointerdown', (e) => {"""
own = """  let own = null;
  function toWorld(ev) {
    const v = H().view();
    const rect = worldEl.getBoundingClientRect();
    const sx = (ev.clientX - rect.left) * (worldEl.width / rect.width);
    const sy = (ev.clientY - rect.top) * (worldEl.height / rect.height);
    return { x: (sx - v.cx) / v.s, y: (sy - v.cy) / v.s };
  }
  function hitWeave(p) {
    let hit = null;
    agents().forEach(a => {
      if (a.kind !== 'weave' || a.locked) return;
      if (Math.abs(p.x - a.x) <= a.w / 2 && Math.abs(p.y - a.y) <= a.h / 2) hit = a;
    });
    return hit;
  }
  function inEditMode() {
    try { const st = H().weaveEditState && H().weaveEditState(); return !!(st && st.agentId); } catch (e) { return false; }
  }
""" + anchor

s = s.replace(anchor, own, 1)

# pointerdown：既记录快照，也开始"直接拖动选中块"
old_pd = """    worldEl.addEventListener('pointerdown', (e) => {
      if (e.button !== 0) return;
      pending = { snap: baseOf(agents().map(a => a.id)), t: Date.now() };
      drag = null;
    }, true);"""
new_pd = """    worldEl.addEventListener('pointerdown', (e) => {
      if (e.button !== 0) return;
      pending = { snap: baseOf(agents().map(a => a.id)), t: Date.now() };
      drag = null; own = null;
      if (inEditMode()) return;               // 编辑态交给原生手柄
      const p = toWorld(e);
      const hit = hitWeave(p);
      if (!hit) return;
      const ids = moveSet(hit.id);
      own = { ids, base: baseOf(ids), start: p, anchor: hit.id };
    }, true);"""
assert s.count(old_pd) == 1
s = s.replace(old_pd, new_pd)

# pointermove：优先处理自己的拖动
old_pm = """    window.addEventListener('pointermove', (e) => {
      if (!pending || drag === null) {"""
new_pm = """    window.addEventListener('pointermove', (e) => {
      if (own) {
        const p = toWorld(e);
        const dx = p.x - own.start.x, dy = p.y - own.start.y;
        own.ids.forEach(id => { const a = byId(id); const b = own.base[id]; if (a && b && !a.locked) { a.x = b.x + dx; a.y = b.y + dy; } });
        const box = bboxOf(own.ids);
        if (box && !(e.ctrlKey || e.metaKey)) {
          const sn = snapDelta(box, new Set(own.ids));
          if (sn.dx || sn.dy) own.ids.forEach(id => { const a = byId(id); if (a && !a.locked) { a.x += sn.dx; a.y += sn.dy; } });
          guides = [];
          if (sn.gx != null) guides.push({ axis: 'x', at: sn.gx });
          if (sn.gy != null) guides.push({ axis: 'y', at: sn.gy });
        } else guides = [];
        return;
      }
      if (!pending || drag === null) {"""
assert s.count(old_pm) == 1
s = s.replace(old_pm, new_pm)

old_up = """    window.addEventListener('pointerup', () => { pending = null; drag = null; guides = []; }, true);"""
new_up = """    window.addEventListener('pointerup', () => { pending = null; drag = null; own = null; guides = []; sig = ''; }, true);"""
assert s.count(old_up) == 1
s = s.replace(old_up, new_up)
io.open(p, "w", encoding="utf-8").write(s)

P = r"docs\index.html"
h = io.open(P, encoding="utf-8").read()
m = "/* ===== r39 个体与图层合并"; i = h.find(m); start = h.rfind("<script>", 0, i); end = h.find("</script>", i)
h = h[:start] + s.rstrip() + h[end+len("</script>"):]
io.open(P, "w", encoding="utf-8").write(h)
print("own-drag added")
