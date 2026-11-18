p = r"_backup\gen_r32_qa.py"
s = open(p, encoding="utf-8").read()
old = s[s.index("    open(p, 'w', encoding='utf-8').write("):s.index("    print(p)")]
new = """    open(p, 'w', encoding='utf-8').write(
        src + '<script>%s</script><script>%s</script>' % (cloud, HEAD + body))
"""
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("gen fixed")
