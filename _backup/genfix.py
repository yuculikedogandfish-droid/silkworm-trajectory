import io
p = r"_backup\gen_r37_qa.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace("""for tag, path in IMGS.items():""", """VARIANT = [(k, v, False) for k, v in IMGS.items()] + [('p', IMGS['p'], True)]
for tag, path, doapply in VARIANT:""")
s = s.replace("""        json.dumps(data), 'true' if tag == 'p' else 'false', JS)""", """        json.dumps(data), 'true' if doapply else 'false', JS)""")
s = s.replace("""    open(os.path.join(TMP, 'r37-%s.html' % tag), 'w', encoding='utf-8').write(page)
    print('r37-%s.html' % tag)""", """    name = 'r37-%s%s.html' % (tag, '' if doapply else '-pv')
    open(os.path.join(TMP, name), 'w', encoding='utf-8').write(page)
    print(name)""")
io.open(p, "w", encoding="utf-8").write(s)
print("gen updated")
