# -*- coding: utf-8 -*-
"""诊断：谁在格子外留丝"""
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
    units[0].w = 280; units[0].h = 280; H.buildWeave(units[0]);
    units[1].w = 280; units[1].h = 280; H.buildWeave(units[1]);
    units[0].x = -160; units[0].y = 0;
    units[1].x = 170; units[1].y = 6;
    H.assignWormToUnit(units[0].id, '1');
    H.assignWormToUnit(units[1].id, '1');
    H.seekTo(5);
    H.agents().forEach(function (a) {
      if (a.kind !== 'route') return;
      var xs = (a.silk || []).map(function (p) { return p.x; });
      var ys = (a.silk || []).map(function (p) { return p.y; });
      out.push(a.id + ' scope=' + a.scope + ' home=' + a.homeUnitId + ' off=' + (a.offX||0).toFixed(0) + ',' + (a.offY||0).toFixed(0) +
        ' silkN=' + (a.silk||[]).length +
        (xs.length ? ' bboxX=' + Math.min.apply(null, xs).toFixed(0) + '..' + Math.max.apply(null, xs).toFixed(0) +
          ' bboxY=' + Math.min.apply(null, ys).toFixed(0) + '..' + Math.max.apply(null, ys).toFixed(0) : ''));
    });
    units.forEach(function (u) {
      out.push('unit ' + u.id + ' x=' + u.x.toFixed(0) + ' y=' + u.y.toFixed(0) + ' w=' + u.w + ' h=' + u.h);
    });
    var box = document.createElement('pre');
    box.id = 'qaOut';
    box.style.cssText = 'position:fixed;left:0;top:0;z-index:99999;background:#000;color:#0f0;font:11px monospace;padding:6px;white-space:pre-wrap';
    box.textContent = out.join('\\n');
    document.body.appendChild(box);
  }, 600);
});
</script>''' % json.dumps(doc, ensure_ascii=False)

src2 = src.replace('</head>', inject + '</head>', 1)
tmp = os.path.join(TMP, 'qa-r23-diag.html')
with io.open(tmp, 'w', encoding='utf-8', newline='') as f:
    f.write(src2)
cmd = [CHROME, '--headless=new', '--disable-gpu', '--no-first-run', '--window-size=1600,1000',
       '--virtual-time-budget=4000', '--dump-dom', 'file:///' + tmp.replace('\\', '/')]
p = subprocess.run(cmd, capture_output=True, timeout=90)
raw = p.stdout.decode('utf-8', 'replace')
i = raw.find('id="qaOut"')
print(html.unescape(raw[i:raw.find('</pre>', i)]) if i > 0 else ('none ' + p.stderr.decode('utf-8', 'replace')[:300]))
