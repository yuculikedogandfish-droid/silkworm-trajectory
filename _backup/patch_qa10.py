p = r"_backup\gen_edit_qa_r30.py"
s = open(p, encoding="utf-8").read()
old = """    const b0 = lum(-190, 0);
    rc(-190, 0);
    await new Promise(r => setTimeout(r, 300));"""
new = """    const isl0 = (H.weaveCellContent(us[0], 0, 0).cell.islands || [])[0];
    const hx = us[0].x + (isl0 ? isl0.cx : 0), hy = us[0].y + (isl0 ? isl0.cy : 0);
    const b0 = lum(hx, hy);
    rc(hx, hy);
    await new Promise(r => setTimeout(r, 300));"""
s = s.replace(old, new)
s = s.replace("lum(-190, 0) + ' 孔数=", "lum(hx, hy) + ' 孔心(" + Math.round(hx) + "," + Math.round(hy) + ") 孔数=")
s = s.replace("window.__weaveHooks.deleteAt({ x: -190, y: 0 })", "window.__weaveHooks.deleteAt({ x: hx, y: hy })")
open(p, "w", encoding="utf-8").write(s)
print('ok')
