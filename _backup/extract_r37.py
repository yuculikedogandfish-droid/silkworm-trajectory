import io, re
src = io.open(r"_backup\patch_r37.py", encoding="utf-8").read()
m = re.search(r'JS = r"""\n(.*?)\n</body>"""', src, re.S)
body = m.group(1)
assert body.startswith("<script>") and body.rstrip().endswith("</script>"), body[:40] + " ... " + body[-40:]
io.open(r"_backup\r37_module.js", "w", encoding="utf-8").write(body)
print("module bytes", len(body))
