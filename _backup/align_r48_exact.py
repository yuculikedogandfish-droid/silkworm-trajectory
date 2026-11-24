import hashlib, subprocess
from pathlib import Path
TARGET='503154cbf29e87eb61e8f6f7f0913259a4191bd2'
base=('tree 36815b4953245ef6a053c0b304c0fe00d46920c8\n'
      'parent a2340ae4c5ae901e9ff1c789f080046f727318d8\n')
msg='r48: conservative smooth recognition with layer correction'
found=None
for minutes in range(-12*60,14*60+1,15):
    sign='+' if minutes>=0 else '-';v=abs(minutes);tz=sign+f'{v//60:02d}{v%60:02d}'
    for nl in ['', '\n', '\r\n']:
        body=base+(f'author yuculikedogandfish-droid <yuculikedogandfish@gmail.com> 1795037681 {tz}\n'
                   f'committer yuculikedogandfish-droid <yuculikedogandfish@gmail.com> 1795037681 {tz}\n\n'+msg+nl)
        raw=body.encode('utf-8')
        sha=hashlib.sha1(b'commit '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if sha==TARGET:
            found=(raw,tz,repr(nl));break
    if found: break
print('found',bool(found),found[1:] if found else '')
if not found: raise SystemExit(1)
root=Path(r'H:\tool\silkworm-trajectory')
def git(args,**kw):
    r=subprocess.run(['git']+args,cwd=root,capture_output=True,**kw)
    if r.returncode: raise RuntimeError(str(r.stdout)+str(r.stderr))
    return r.stdout.decode().strip()
sha=git(['hash-object','-t','commit','-w','--stdin'],input=found[0])
assert sha==TARGET
git(['reset','--mixed',TARGET]);git(['tag','-d','r48']);git(['tag','r48',TARGET])
print('local main aligned')
