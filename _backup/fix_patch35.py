p = r"_backup\patch_r35.py"
s = open(p, encoding="utf-8").read()
old = """            let near = Infinity;
            pts2.forEach(q => { near = Math.min(near, Math.hypot(p.x - (a.x + e.ix * a.w + q.x), p.y - (a.y + e.iy * a.h + q.y))); });
            const nearPx = near / 1;
            if (bd <= 24 / view().s && near > 10 / view().s && nearPx > 10) {"""
new = """            let near = Infinity;
            pts2.forEach(q => { near = Math.min(near, Math.hypot(p.x - (ox2 + q.x), p.y - (oy2 + q.y))); });
            if (bd <= 24 / view().s && near > 10 / view().s) {"""
assert s.count(old) == 1
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("ok")
