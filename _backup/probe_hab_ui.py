# -*- coding: utf-8 -*-
"""只显示蚕室(#habitat)的 QA 副本，便于截图看面板"""
import io, sys

src = r'H:\tool\silkworm-trajectory\docs\index.html'
dst = r'C:\Users\54364\AppData\Local\Temp\qa-hab-only.html'
with io.open(src, 'r', encoding='utf-8') as f:
    s = f.read()
inject = (
    '<style>body > *:not(#habitat){display:none !important;}</style>'
    '<script>window.addEventListener("load", function(){'
    'try{ if(window.__studioHabitat && __studioHabitat.addWeave){ __studioHabitat.addWeave(); } }catch(e){}'
    '});</script>'
)
if '</body>' not in s:
    raise SystemExit('no </body>')
s = s.replace('</body>', inject + '</body>')
with io.open(dst, 'w', encoding='utf-8', newline='') as f:
    f.write(s)
print(dst)
