# -*- coding: utf-8 -*-
import html
import io

p = r'H:\tool\silkworm-trajectory\docs\index.html'
with io.open(p, encoding='utf-8') as f:
    t = f.read()

orig_len = len(t)

# --- 定位 srcdoc ---
iframe_pos = t.index('iframe id="previewFrame"')
srcdoc_start = t.index('srcdoc="', iframe_pos) + len('srcdoc="')
iframe_end = t.index('"></iframe>', srcdoc_start)

# --- 蚕室 CSS：srcdoc style 内 #habitat 起至 </style> ---
s_style = t.index('<style>', srcdoc_start)
s_style_end = t.index('</style>', s_style)
hab_css_start = t.index('  #habitat {', s_style)
hab_css = t[hab_css_start:s_style_end]

# --- 蚕室 HTML：scroll-cue 起至 habitat </section> ---
hab_html_start = t.index('<p class=&quot;scroll-cue&quot;', s_style_end)
sec_open = t.index('<section id=&quot;habitat&quot;', hab_html_start)
sec_close = t.index('</section>', sec_open) + len('</section>')
hab_html = t[hab_html_start:sec_close]

# --- 蚕室脚本：含 embed 判定的 IIFE ---
marker = "if (document.body.classList.contains('embed')) return;"
mpos = t.index(marker, sec_close)
s_start = t.rindex('<script>', sec_close, mpos)
s_end = t.index('</script>', mpos) + len('</script>')
hab_script = t[s_start:s_end]

# 解码 srcdoc 实体内联
hab_css_d = html.unescape(hab_css)
hab_html_d = html.unescape(hab_html)
hab_script_d = html.unescape(hab_script)

# --- 从 srcdoc 中删除三块 ---
srcdoc_body = t[srcdoc_start:iframe_end]

def cut(src, block):
    i = src.index(block)
    return src[:i] + src[i + len(block):]

# 删除脚本、HTML（先删后面的块，避免位置漂移）
srcdoc_body = cut(srcdoc_body, hab_script)
srcdoc_body = cut(srcdoc_body, hab_html)
srcdoc_body = cut(srcdoc_body, hab_css)

# body.embed 里对 #habitat 的隐藏规则已不适用
srcdoc_body = srcdoc_body.replace(
    '  body.embed #habitat, body.embed #scrollCue { display: none; }\n', '')

new = t[:srcdoc_start] + srcdoc_body + t[iframe_end:]

# --- 蚕室 CSS 注入外层 style ---
outer_style_end = new.index('</style>')
new = new[:outer_style_end] + '\n  /* ===== Digital Habitat（外层全宽区块） ===== */\n' + hab_css_d + '\n' + new[outer_style_end:]

# --- 蚕室 HTML 注入 workspace 之后 ---
ws_close_marker = '></iframe>\n</div>'
ws_pos = new.index(ws_close_marker) + len(ws_close_marker)
new = new[:ws_pos] + '\n' + hab_html_d + '\n' + new[ws_pos:]

# --- 蚕室脚本注入外层脚本之后 ---
close_body = new.rindex('</body>')
new = new[:close_body] + hab_script_d + '\n' + new[close_body:]

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(new)

print('orig bytes:', orig_len)
print('new  bytes:', len(new))
print('hab css lines:', hab_css_d.count('\n'))
print('hab html lines:', hab_html_d.count('\n'))
print('hab script lines:', hab_script_d.count('\n'))
print('srcdoc still has habitat:', '#habitat' in new[new.index('srcdoc="'):new.index('"></iframe>')])
