# -*- coding: utf-8 -*-
"""r21 截图：整屏蚕室（时间滑条 + 撤销重做 + 壁/丝路说明 + 实测蚕在格里）"""
import io, json, os, subprocess

SRC = r'H:\tool\silkworm-trajectory\docs\index.html'
TRAJ = r'G:\raby model\trajectories.json'
TMP = r'C:\Users\54364\AppData\Local\Temp'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

with io.open(TRAJ, 'r', encoding='utf-8') as f:
    doc = json.load(f)
with io.open(SRC, 'r', encoding='utf-8') as f:
    src = f.read()

inject = u'''<style>body > *:not(#habitat):not(script):not(style){display:none !important}</style>
<script>window.__QA_TRAJ = %s;</script>
<script>
window.addEventListener('load', function () {
  setTimeout(function () {
    var H = window.__studioHabitat;
    H.importPointCloudDoc(window.__QA_TRAJ);
    H.addWeave();
    var wv = H.agents().filter(function (a) { return a.kind === 'weave'; })[0];
    if (wv) { wv.w = 560; wv.h = 520; H.buildWeave(wv); }
    H.seekTo(7);
    var hab = document.getElementById('habitat');
    hab.scrollIntoView(true);
    window.scrollBy(0, 0);
  }, 600);
});
</script>''' % json.dumps(doc, ensure_ascii=False)

src2 = src.replace('</head>', inject + '</head>', 1)
tmp = os.path.join(TMP, 'qa-r21-shot.html')
with io.open(tmp, 'w', encoding='utf-8', newline='') as f:
    f.write(src2)

shot = os.path.join(TMP, 'qa-r21-ui.png')
cmd = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
       '--disable-extensions', '--window-size=1600,1000', '--virtual-time-budget=4000',
       '--screenshot=' + shot, 'file:///' + tmp.replace('\\', '/')]
p = subprocess.run(cmd, capture_output=True, timeout=90)
print('shot', shot, os.path.exists(shot) and os.path.getsize(shot))
if not os.path.exists(shot):
    print(p.stderr.decode('utf-8', 'replace')[:600])
