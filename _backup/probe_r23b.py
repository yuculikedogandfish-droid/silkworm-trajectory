# -*- coding: utf-8 -*-
"""r23 验收B：同种蚕同时服务两格、实例独立、起点随机"""
import io, json, os, subprocess, html

SRC = r'H:\tool\silkworm-trajectory\docs\index.html'
TRAJ = r'G:\raby model\trajectories.json'
TMP = r'C:\Users\54364\AppData\Local\Temp'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

with io.open(TRAJ, 'r', encoding='utf-8') as f:
    doc = json.load(f)
with io.open(SRC, 'r', encoding='utf-8') as f:
    src = f.read()

inject = u'''<script>window.__QA_TRAJ = %s;</script>
<script>
window.addEventListener('load', function () {
  setTimeout(function () {
    var out = [];
    var H = window.__studioHabitat;
    H.importPointCloudDoc(window.__QA_TRAJ);
    H.addWeave(); H.addWeave();
    var units = H.agents().filter(function (a) { return a.kind === 'weave'; });
    units[0].w = 260; units[0].h = 260; H.buildWeave(units[0]);
    units[1].w = 260; units[1].h = 260; H.buildWeave(units[1]);
    H.assignWormToUnit(units[0].id, '1');
    H.assignWormToUnit(units[1].id, '1');
    var A = H.agents().filter(function (a) { return a.kind === 'route' && a.homeUnitId === units[0].id; });
    var B = H.agents().filter(function (a) { return a.kind === 'route' && a.homeUnitId === units[1].id; });
    out.push('A=' + A.length + ' [' + A.map(function (a) { return a.id; }) + '] start=' + A.map(function (a) { return a.offX.toFixed(0) + ',' + a.offY.toFixed(0); }));
    out.push('B=' + B.length + ' [' + B.map(function (a) { return a.id; }) + '] start=' + B.map(function (a) { return a.offX.toFixed(0) + ',' + a.offY.toFixed(0); }));
    out.push('unitA center=' + units[0].x.toFixed(0) + ',' + units[0].y.toFixed(0) + ' unitB center=' + units[1].x.toFixed(0) + ',' + units[1].y.toFixed(0));
    out.push('sourceWorms=' + H.agents().filter(function (a) { return a.kind === 'route' && a.id === 'rt-1'; }).length);
    // 起点是否随机：再给 A 指定一次，起点应变化且都在格内
    var s1 = A[0].offX;
    H.assignWormToUnit(units[0].id, '1');
    var A2 = H.agents().filter(function (a) { return a.kind === 'route' && a.homeUnitId === units[0].id; })[0];
    out.push('respawn start changed=' + (Math.abs(A2.offX - s1) > 0.5) + ' off=' + A2.offX.toFixed(0) + ',' + A2.offY.toFixed(0) +
             ' inside=' + (Math.abs(A2.offX - units[0].x) <= units[0].w * 0.35 && Math.abs(A2.offY - units[0].y) <= units[0].h * 0.35));
    H.seekTo(5);
    var sa = H.agents().filter(function (a) { return a.kind === 'route' && a.homeUnitId === units[0].id; })[0];
    var sb = H.agents().filter(function (a) { return a.kind === 'route' && a.homeUnitId === units[1].id; })[0];
    out.push('silkA=' + (sa ? sa.silk.length : '-') + ' silkB=' + (sb ? sb.silk.length : '-'));
    var box = document.createElement('pre');
    box.id = 'qaOut';
    box.style.cssText = 'position:fixed;left:0;top:0;z-index:99999;background:#000;color:#0f0;font:12px monospace;padding:8px;white-space:pre-wrap';
    box.textContent = out.join('\\n');
    document.body.appendChild(box);
  }, 600);
});
</script>''' % json.dumps(doc, ensure_ascii=False)

src2 = src.replace('</head>', inject + '</head>', 1)
tmp = os.path.join(TMP, 'qa-r23b.html')
with io.open(tmp, 'w', encoding='utf-8', newline='') as f:
    f.write(src2)
cmd = [CHROME, '--headless=new', '--disable-gpu', '--no-first-run', '--window-size=1600,1000',
       '--virtual-time-budget=4000', '--dump-dom', 'file:///' + tmp.replace('\\', '/')]
p = subprocess.run(cmd, capture_output=True, timeout=90)
raw = p.stdout.decode('utf-8', 'replace')
i = raw.find('id="qaOut"')
print(html.unescape(raw[i:raw.find('</pre>', i)]) if i > 0 else ('none ' + p.stderr.decode('utf-8', 'replace')[:300]))
