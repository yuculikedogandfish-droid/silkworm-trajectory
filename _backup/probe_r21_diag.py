# -*- coding: utf-8 -*-
"""诊断：seek 后丝迹范围 vs 单元格范围"""
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
    H.addWeave();
    var wv = H.agents().filter(function (a) { return a.kind === 'weave'; })[0];
    wv.w = 560; wv.h = 520;
    H.seekTo(7);
    var rt = H.agents().filter(function (a) { return a.kind === 'route'; })[0];
    out.push('unit=' + wv.x + ',' + wv.y + ' ' + wv.w + 'x' + wv.h + ' u=' + wv.u.toFixed(2));
    out.push('scope=' + rt.scope + ' home=' + rt.homeUnitId + ' follow=' + rt.follow);
    var xs = rt.silk.map(function (p) { return p.x; }), ys = rt.silk.map(function (p) { return p.y; });
    out.push('silkN=' + rt.silk.length);
    out.push('silkX=' + Math.min.apply(null, xs).toFixed(0) + '..' + Math.max.apply(null, xs).toFixed(0));
    out.push('silkY=' + Math.min.apply(null, ys).toFixed(0) + '..' + Math.max.apply(null, ys).toFixed(0));
    var paths = H.weaveCellContent(wv);
    var pxMin = 1e9, pxMax = -1e9, pyMin = 1e9, pyMax = -1e9, np = 0;
    (paths.paths || []).forEach(function (p) {
      (p.pts || p).forEach(function (q) { pxMin = Math.min(pxMin, q.x); pxMax = Math.max(pxMax, q.x); pyMin = Math.min(pyMin, q.y); pyMax = Math.max(pyMax, q.y); np++; });
    });
    out.push('weavePts=' + np + ' x=' + pxMin.toFixed(0) + '..' + pxMax.toFixed(0) + ' y=' + pyMin.toFixed(0) + '..' + pyMax.toFixed(0));
    var box = document.createElement('pre');
    box.id = 'qaOut';
    box.style.cssText = 'position:fixed;left:0;top:0;z-index:99999;background:#000;color:#0f0;font:12px monospace;padding:8px';
    box.textContent = out.join('\\n');
    document.body.appendChild(box);
  }, 600);
});
</script>''' % json.dumps(doc, ensure_ascii=False)

src2 = src.replace('</head>', inject + '</head>', 1)
tmp = os.path.join(TMP, 'qa-r21-diag.html')
with io.open(tmp, 'w', encoding='utf-8', newline='') as f:
    f.write(src2)

cmd = [CHROME, '--headless=new', '--disable-gpu', '--no-first-run', '--window-size=1600,1000',
       '--virtual-time-budget=4000', '--dump-dom', 'file:///' + tmp.replace('\\', '/')]
p = subprocess.run(cmd, capture_output=True, timeout=90)
raw = p.stdout.decode('utf-8', 'replace')
i = raw.find('id="qaOut"')
if i > 0:
    j = raw.find('</pre>', i)
    print(html.unescape(raw[i:j])[:1200])
else:
    print('none', p.stderr.decode('utf-8', 'replace')[:400])
