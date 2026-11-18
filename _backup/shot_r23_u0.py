# -*- coding: utf-8 -*-
"""r23 截图：两块格各用同一种蚕，起点随机"""
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
    H.addWeave(); H.addWeave();
    var units = H.agents().filter(function (a) { return a.kind === 'weave'; });
    units[0].w = 280; units[0].h = 280; H.buildWeave(units[0]);
    units[1].w = 280; units[1].h = 280; H.buildWeave(units[1]);
    units[0].x = -160; units[0].y = 0;
    units[1].x = 170; units[1].y = 6;
    H.assignWormToUnit(units[0].id, '1');
    H.assignWormToUnit(units[1].id, '1');
    units.forEach(function(u){ u.u = 0; }); H.seekTo(5);
  }, 600);
});
</script>''' % json.dumps(doc, ensure_ascii=False)

src2 = src.replace('</head>', inject + '</head>', 1)
tmp = os.path.join(TMP, 'qa-r23-shot.html')
with io.open(tmp, 'w', encoding='utf-8', newline='') as f:
    f.write(src2)
shot = os.path.join(TMP, 'qa-r23-u0.png')
cmd = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
       '--disable-extensions', '--window-size=1600,1000', '--virtual-time-budget=3500',
       '--screenshot=' + shot, 'file:///' + tmp.replace('\\', '/')]
p = subprocess.run(cmd, capture_output=True, timeout=90)
print('shot', shot, os.path.exists(shot) and os.path.getsize(shot))

