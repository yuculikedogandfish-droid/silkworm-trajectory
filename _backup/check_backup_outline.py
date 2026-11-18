# -*- coding: utf-8 -*-
from pathlib import Path
import re
for name in ['index-v2-20261116-before-restructure.html', 'index-v1-20261111.html']:
    p = Path(r"H:\tool\silkworm-trajectory\_backup") / name
    s = p.read_text(encoding="utf-8")
    print('=====', name, len(s))
    for label, pat in [('<div class="workspace"', r'<div class="workspace"'),
                       ('</main>', r'</main>'),
                       ('<iframe id="previewFrame"', r'<iframe id="previewFrame"'),
                       ('</iframe>', r'></iframe>'),
                       ('<div class="transport"', r'<div class="transport"'),
                       ('<section id="habitat"', r'<section id="habitat"')]:
        print(' ', label, [m.start() for m in re.finditer(pat, s)])
