p = r"_backup\build_guide_r34.py"
s = open(p, encoding="utf-8").read()
old = """  fig('home', '整体界面：左边环境与观感、中间场地、右边个体与选中调整、最下面时间轴。')
  '<div class="tip">"""
new = """  fig('home', '整体界面：左边环境与观感、中间场地、右边个体与选中调整、最下面时间轴。') +
  '<div class="tip">"""
assert s.count(old) == 1
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("ok")
