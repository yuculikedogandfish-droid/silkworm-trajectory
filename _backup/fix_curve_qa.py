p = r"_backup\gen_r32_qa.py"
s = open(p, encoding="utf-8").read()
s = s.replace('CURVE = COMMON + r"""', 'CURVE = COMMON + pdjs + r"""')
s = s.replace("""    speak""", """    speak""")
open(p, "w", encoding="utf-8").write(s)
print('ok')
