p = r"_backup\gen_edit_qa_r30.py"
s = open(p, encoding="utf-8").read()
s = s.replace("""say('ENTER called id=' + id);""", """say('ENTER id=' + id + ' @ ' + String(new Error().stack || '').split('\\n').slice(1, 4).join(' / '));""")
open(p, "w", encoding="utf-8").write(s)
print('ok')
