# -*- coding: utf-8 -*-
import io, re
p = r'H:\tool\silkworm-trajectory\docs\使用说明.html'
s = io.open(p, encoding='utf-8').read()
print('section open', s.count('<section'), 'close', s.count('</section>'))
print('s13 id', s.count('id="s13"'), 'toc13', s.count('href="#s13"'))
print('r48 left', s.count('r48'))
# 粗略检查 s13 内部标签配平
i = s.find('id="s13"')
j = s.find('</section>', i)
sec = s[i:j]
for tag in ['table', 'ul', 'div', 'ol']:
    print(tag, sec.count('<' + tag), sec.count('</' + tag + '>'))
print(re.sub('<[^>]+>', '', sec)[:200])
