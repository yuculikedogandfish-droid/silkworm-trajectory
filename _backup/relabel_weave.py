import io
p = 'docs/index.html'
s = io.open(p, encoding='utf-8').read()
pairs = [
    ('格网：黑底、无边界细网格；每格密织、带圆孔负空间。',
     '织网单元：一个单元就是一格（放几个就几块）；格内密织 + 大圆孔负空间，形状可手动编辑。'),
    ("' 只 · 格网 ' + weaveN + ' 个'", "' 只 · 织网单元 ' + weaveN + ' 个'"),
    ("'格网 ' + a.id : a.id", "'织网单元 ' + a.id : a.id"),
    ('>格网</span>', '>织网单元</span>'),
    ("'织网格网 ' + a.id", "'织网单元 ' + a.id"),
    ("'先选中一个织网格网，再编辑形状。'", "'先选中一个织网单元，再编辑形状。'"),
]
for a, b in pairs:
    if a not in s:
        print('MISS', a)
    s = s.replace(a, b)
io.open(p, 'w', encoding='utf-8').write(s)
print('remaining', s.count('格网'))
