# -*- coding: utf-8 -*-
import io,re,subprocess,tempfile,os,sys
NODE=r'C:\Users\54364\AppData\Local\Doubao\User Data\sandbox_runtime\bases\fa694f517e5995233c80a9a8db5212c2\node\node.exe'
files=[r'H:\tool\silkworm-trajectory\docs\index.html',r'H:\tool\silkworm-trajectory\docs\使用说明.html']
bad=[]
for path in files:
 s=io.open(path,encoding='utf-8').read(); n=0
 for m in re.finditer(r'<script\b([^>]*)>([\s\S]*?)</script>',s,re.I):
  attrs,code=m.group(1),m.group(2)
  if 'src=' in attrs.lower() or 'json' in attrs.lower() or not code.strip(): continue
  n+=1
  fd,tmp=tempfile.mkstemp(suffix='.js'); os.close(fd)
  io.open(tmp,'w',encoding='utf-8').write(code)
  p=subprocess.run([NODE,'--check',tmp],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  os.remove(tmp)
  if p.returncode: bad.append((os.path.basename(path),n,p.stdout.decode('utf-8','replace')[:800]))
 print(os.path.basename(path),'inline_scripts',n)
if bad:
 print(bad);sys.exit(1)
print('all inline JS syntax OK')
