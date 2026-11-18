p = r"_backup\gen_edit_qa_r30.py"
s = open(p, encoding="utf-8").read()
s = s.replace("document.body.appendChild(out);", "(document.getElementById('habitat') || document.body).appendChild(out);")
open(p, "w", encoding="utf-8").write(s)
print('ok')
