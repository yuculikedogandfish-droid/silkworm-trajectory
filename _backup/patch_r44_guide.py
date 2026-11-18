import io
P=r"docs\index.html"
h=io.open(P,encoding="utf-8").read()
style = 'display:inline-block;background:#f0b45a;color:#241a06;font-weight:700;padding:7px 14px;border-radius:8px;text-decoration:none;white-space:nowrap;box-shadow:0 2px 10px rgba(240,180,90,.25)'
link = '<a href="使用说明.html" target="_blank" rel="noopener" style="' + style + '">使用说明（图文）</a>'

a1 = '<button type="button" class="primary" data-tip="滚到下方整屏蚕室，并把描好的蚕同步进去" onclick="gotoHabitat()">进入 Digital Habitat</button>'
assert a1 in h
h = h.replace(a1, a1 + '\n  ' + link, 1)

a2 = '    <span class="spacer"></span>\n    <button type="button" id="habOpenLeft"'
assert a2 in h
h = h.replace(a2, '    <span class="spacer"></span>\n    ' + link + '\n    <button type="button" id="habOpenLeft"', 1)
io.open(P,"w",encoding="utf-8").write(h)
print("guide links:", h.count('使用说明.html'))
