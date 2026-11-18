p = r"_backup\gen_edit_qa_r30.py"
s = open(p, encoding="utf-8").read()
s = s.replace("""    say('2 右键孔亮度 ' + b0 + ' -> ' + lum(-190, 0));""",
"""    say('2 右键孔亮度 ' + b0 + ' -> ' + lum(-190, 0) + ' 孔数=' + ((H.weaveCellContent(us[0],0,0).cell.islands||[]).length));""")
open(p, "w", encoding="utf-8").write(s)
print('ok')
