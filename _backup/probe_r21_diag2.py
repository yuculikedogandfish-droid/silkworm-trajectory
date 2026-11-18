# -*- coding: utf-8 -*-
"""诊断2：单元几何与丝点坐标是否一致"""
import io, json, os, subprocess, html

SRC = r'H:\tool\silkworm-trajectory\docs\index.html'
TMP = r'C:\Users\54364\AppData\Local\Temp'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
with io.open(SRC, 'r', encoding='utf-8') as f:
    src = f.read()

inject = u'''<script>
window.addEventListener('load', function () {
  setTimeout(function () {
    var out = [];
    var H = window.__studioHabitat;
    H.addWeave();
    var wv = H.agents().filter(function (a) { return a.kind === 'weave'; })[0];
    wv.w = 560; wv.h = 520; H.buildWeave(wv);
    out.push('agent w/h=' + wv.w + '/' + wv.h + ' x=' + wv.x + ' y=' + wv.y + ' shape=' + wv.shape);
    var c = H.weaveCellContent(wv, 0, 0);
    out.push('cell w/h=' + c.cell.w + '/' + c.cell.h + ' paths=' + c.paths.length + ' blank=' + c.blank);
    var p0 = c.paths[0].pts;
    out.push('p0[0]=' + p0[0].x.toFixed(1) + ',' + p0[0].y.toFixed(1) + ' p0[n]=' + p0[p0.length - 1].x.toFixed(1) + ',' + p0[p0.length - 1].y.toFixed(1));
    var mnx = 1e9, mxx = -1e9;
    c.paths.forEach(function (p) { p.pts.forEach(function (q) { mnx = Math.min(mnx, q.x); mxx = Math.max(mxx, q.x); }); });
    out.push('x=' + mnx.toFixed(0) + '..' + mxx.toFixed(0));
    out.push('sample=' + JSON.stringify(wv.sample));
    var box = document.createElement('pre');
    box.id = 'qaOut';
    box.style.cssText = 'position:fixed;left:0;top:0;z-index:99999;background:#000;color:#0f0;font:12px monospace;padding:8px';
    box.textContent = out.join('\\n');
    document.body.appendChild(box);
  }, 600);
});
</script>'''

src2 = src.replace('</head>', inject + '</head>', 1)
tmp = os.path.join(TMP, 'qa-r21-diag2.html')
with io.open(tmp, 'w', encoding='utf-8', newline='') as f:
    f.write(src2)
cmd = [CHROME, '--headless=new', '--disable-gpu', '--no-first-run', '--window-size=1600,1000',
       '--virtual-time-budget=3000', '--dump-dom', 'file:///' + tmp.replace('\\', '/')]
p = subprocess.run(cmd, capture_output=True, timeout=90)
raw = p.stdout.decode('utf-8', 'replace')
i = raw.find('id="qaOut"')
print(html.unescape(raw[i:raw.find('</pre>', i)]) if i > 0 else ('none ' + p.stderr.decode('utf-8', 'replace')[:300]))
