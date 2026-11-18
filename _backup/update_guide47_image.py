# -*- coding: utf-8 -*-
import io,re,base64
from PIL import Image
ROOT=r'H:\tool\silkworm-trajectory'
src=r'C:\Users\54364\AppData\Local\Temp\rec47h-new.png'
out=ROOT+r'\_backup\rec43\rec47_preview.png'
im=Image.open(src)
im.crop((150,180,1060,800)).save(out)
b64=base64.b64encode(io.open(out,'rb').read()).decode('ascii')
p=ROOT+r'\docs\使用说明.html'
s=io.open(p,encoding='utf-8').read()
a=s.rfind('<section',0,s.index('id="s12"'))
b=s.index('</section>',a)
part=s[a:b]
part,n=re.subn(r'data:image/png;base64,[A-Za-z0-9+/=]+','data:image/png;base64,'+b64,part,count=1)
if n!=1: raise RuntimeError('guide image not replaced')
s=s[:a]+part+s[b:]
io.open(p,'w',encoding='utf-8').write(s)
print('guide r47 image',len(b64))
