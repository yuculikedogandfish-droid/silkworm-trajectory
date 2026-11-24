from pathlib import Path
import base64, json, os, subprocess, tempfile
ROOT = Path(r'H:\tool\silkworm-trajectory')
GH = r'C:\Program Files\GitHub CLI\gh.exe'
REPO = 'repos/yuculikedogandfish-droid/silkworm-trajectory'
FILES = ['docs/index.html', 'docs/使用说明.html', 'editor/silkworm-tracer.html', 'editor/蚕轨迹描图器.html']
MSG = 'r48: conservative smooth recognition with layer correction'
work = ROOT / '_backup' / 'api_publish'
work.mkdir(exist_ok=True)

def api(method, endpoint, payload=None):
    args = [GH, 'api']
    if method != 'GET': args += ['-X', method]
    args.append(endpoint)
    fp = None
    if payload is not None:
        fp = work / ('payload.json')
        fp.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8', newline='')
        args += ['--input', str(fp)]
    r = subprocess.run(args, cwd=ROOT, text=True, encoding='utf-8', capture_output=True)
    if r.returncode:
        raise RuntimeError(r.stdout + '\n' + r.stderr)
    return json.loads(r.stdout)

remote = api('GET', REPO + '/branches/main')['commit']['sha']
print('remote main', remote)
tree_items = []
for rel in FILES:
    content = base64.b64encode((ROOT / rel).read_bytes()).decode('ascii')
    blob = api('POST', REPO + '/git/blobs', {'content': content, 'encoding': 'base64'})
    tree_items.append({'path': rel, 'mode': '100644', 'type': 'blob', 'sha': blob['sha']})
    print('blob', rel, blob['sha'])
tree = api('POST', REPO + '/git/trees', {'base_tree': remote, 'tree': tree_items})
print('tree', tree['sha'])
local_tree = subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=ROOT, text=True).strip()
print('local tree', local_tree, 'match', local_tree == tree['sha'])
commit = api('POST', REPO + '/git/commits', {'message': MSG, 'tree': tree['sha'], 'parents': [remote]})
new = commit['sha']
print('api commit', new)
api('PATCH', REPO + '/git/refs/heads/main', {'sha': new, 'force': False})
print('main updated')
api('POST', REPO + '/git/refs', {'ref': 'refs/tags/r48', 'sha': new})
print('tag r48 created')
# Recreate the same Git commit object locally so the branch can move without changing files.
a, c = commit['author'], commit['committer']
env = os.environ.copy()
for prefix, person in [('GIT_AUTHOR', a), ('GIT_COMMITTER', c)]:
    env[prefix + '_NAME'] = person['name']
    env[prefix + '_EMAIL'] = person['email']
    env[prefix + '_DATE'] = person['date']
r = subprocess.run(['git', 'commit-tree', tree['sha'], '-p', remote, '-m', MSG], cwd=ROOT, env=env, text=True, encoding='utf-8', capture_output=True)
local_new = r.stdout.strip()
print('local recreated', local_new, 'match', local_new == new)
if r.returncode == 0 and local_new == new:
    subprocess.run(['git', 'reset', '--mixed', new], cwd=ROOT, check=True)
    subprocess.run(['git', 'tag', '-d', 'r48'], cwd=ROOT, check=True, capture_output=True)
    subprocess.run(['git', 'tag', 'r48', new], cwd=ROOT, check=True)
    print('local main aligned')
print('PUBLISHED', new)
