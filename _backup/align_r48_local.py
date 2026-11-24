from pathlib import Path
import json, os, subprocess
ROOT = Path(r'H:\tool\silkworm-trajectory')
GH = r'C:\Program Files\GitHub CLI\gh.exe'
REPO = 'repos/yuculikedogandfish-droid/silkworm-trajectory'
TARGET = '503154cbf29e87eb61e8f6f7f0913259a4191bd2'
PARENT = 'a2340ae4c5ae901e9ff1c789f080046f727318d8'
TREE = '36815b4953245ef6a053c0b304c0fe00d46920c8'
MSG = 'r48: conservative smooth recognition with layer correction'
BLOBS = {
 'docs/index.html':'6c0a7ae6faca3caf7e914ccd9eec532e43ed8593',
 'docs/使用说明.html':'afe53b27b0acc091ad32da2dedb2039d3b023c15',
 'editor/silkworm-tracer.html':'6c0a7ae6faca3caf7e914ccd9eec532e43ed8593',
 'editor/蚕轨迹描图器.html':'6c0a7ae6faca3caf7e914ccd9eec532e43ed8593'
}
def git(*args, env=None):
    r=subprocess.run(['git']+list(args),cwd=ROOT,env=env,text=True,encoding='utf-8',capture_output=True)
    if r.returncode: raise RuntimeError(r.stdout+'\n'+r.stderr)
    return r.stdout.strip()
r=subprocess.run([GH,'api',REPO+'/git/commits/'+TARGET],text=True,encoding='utf-8',capture_output=True)
r.check_returncode()
c=json.loads(r.stdout)
git('read-tree',PARENT)
for path,sha in BLOBS.items(): git('update-index','--add','--cacheinfo','100644,'+sha+','+path)
actual_tree=git('write-tree')
print('tree',actual_tree,'match',actual_tree==TREE)
if actual_tree!=TREE: raise SystemExit('tree mismatch; stop before branch update')
env=os.environ.copy()
for prefix,person in [('GIT_AUTHOR',c['author']),('GIT_COMMITTER',c['committer'])]:
    env[prefix+'_NAME']=person['name'];env[prefix+'_EMAIL']=person['email'];env[prefix+'_DATE']=person['date']
local=git('commit-tree',actual_tree,'-p',PARENT,'-m',MSG,env=env)
print('commit',local,'match',local==TARGET)
if local!=TARGET: raise SystemExit('commit mismatch; stop before branch update')
git('reset','--mixed',TARGET)
git('tag','-d','r48')
git('tag','r48',TARGET)
print('local aligned without rewriting deliverables')
