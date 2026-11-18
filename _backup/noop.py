import io, re
p = r"_backup\gen_r37_qa.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace("json.dumps(data), 'true' if tag == 'p' else 'false', JS)", "json.dumps(data), 'true' if tag == 'p' else 'false', JS)")
# 生成两个版本：预览 / 生成
io.open(p, "w", encoding="utf-8").write(s)
print("ok")
