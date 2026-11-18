p = r"_backup\build_guide_r34.py"
s = open(p, encoding="utf-8").read()
s = s.replace("<b>一只蚕可以同时用在不同格子</strong>", "<b>一只蚕可以同时用在不同格子</b>")
s = s.replace("<dt>丝跑出格子外面了？</td>", "<dt>丝跑出格子外面了？</dt>")
open(p, "w", encoding="utf-8").write(s)
print("fixed")
