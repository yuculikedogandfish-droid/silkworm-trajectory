# -*- coding: utf-8 -*-
import io
p = r'H:\tool\silkworm-trajectory\_backup\probe_seed_table2.py'
s = io.open(p, encoding='utf-8').read()

a1 = "    var a = A0[0];\n    a.w = a.h = 300;\n    a.coverage = 0.55;\n    a.scaleK = 0.9;"
b1 = "    var a = A0[0];\n    a.coverage = 0.55;\n    a.scaleK = 0.9;"
assert s.count(a1) == 1
s = s.replace(a1, b1)

a2 = "      a.seed = sd >>> 0;\n      a.cache = new Map();\n      h.buildWeave(a);"
b2 = "      a.w = a.h = 300;\n      a.seed = sd >>> 0;\n      a.cache = new Map();\n      h.buildWeave(a);"
assert s.count(a2) == 1
s = s.replace(a2, b2)

a3 = "        threads: a.paths.length,"
b3 = "        threads: (h.weaveCellContent(a, 0, 0).paths || []).length,"
assert s.count(a3) == 1
s = s.replace(a3, b3)

a4 = "        points: a.paths.reduce(function (t, p) { return t + p.pts.length; }, 0),"
b4 = "        points: (h.weaveCellContent(a, 0, 0).paths || []).reduce(function (t, p) { return t + p.pts.length; }, 0),"
assert s.count(a4) == 1
s = s.replace(a4, b4)

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('patched')
