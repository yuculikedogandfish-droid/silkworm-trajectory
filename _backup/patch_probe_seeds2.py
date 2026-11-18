# -*- coding: utf-8 -*-
import io
p = r'H:\tool\silkworm-trajectory\_backup\probe_seed_table2.py'
s = io.open(p, encoding='utf-8').read()

a1 = "      var spec = h.weaveCellSpecAt ? h.weaveCellSpecAt(a, 0, 0) : null;"
b1 = "      var cc = h.weaveCellContent(a, 0, 0);\n      var spec = cc.cell || null;"
assert s.count(a1) == 1
s = s.replace(a1, b1)

a2 = "        threads: (h.weaveCellContent(a, 0, 0).paths || []).length,"
b2 = "        threads: (cc.paths || []).length,"
assert s.count(a2) == 1
s = s.replace(a2, b2)

a3 = "        points: (h.weaveCellContent(a, 0, 0).paths || []).reduce(function (t, p) { return t + p.pts.length; }, 0),"
b3 = "        points: (cc.paths || []).reduce(function (t, q) { return t + q.pts.length; }, 0),"
assert s.count(a3) == 1
s = s.replace(a3, b3)

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('patched2')
