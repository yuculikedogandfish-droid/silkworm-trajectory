from pathlib import Path
import re
s=Path(r'H:\tool\silkworm-trajectory\docs\使用说明.html').read_text(encoding='utf-8')
a=s.index('<section class="card newpage" id="s12">')
b=s.index('</section>',a)
seg=s[a:b]
seg=re.sub(r'data:image/[^;]+;base64,[A-Za-z0-9+/=]+','[image]',seg)
print(seg)
