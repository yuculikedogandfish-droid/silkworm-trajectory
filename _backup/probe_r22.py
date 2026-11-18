# -*- coding: utf-8 -*-
"""r22 验收：格内蚕选择、丝迹裁在格内、描图器数据同步"""
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
    wv.w = 300; wv.h = 300; H.buildWeave(wv);
    H.agents().forEach(function (a) { if (a.kind === 'route') { a.x = wv.x; a.y = wv.y; } });
    var sel = document.getElementById('habWeaveWorm');
    out.push('select disabled=' + sel.disabled + ' opts=' + sel.options.length + ' [' + Array.prototype.map.call(sel.options, function (o) { return o.text; }).join(' / ') + ']');
    // 选中蚕 1
    var wvSel = H.agents().filter(function (a) { return a.kind === 'weave'; })[0];
    var route = H.agents().filter(function (a) { return a.kind === 'route'; })[0];
    sel.value = String(route.wormId);
    sel.dispatchEvent(new Event('change'));
    var r2 = H.agents().filter(function (a) { return a.kind === 'route'; })[0];
    out.push('route.scope=' + r2.scope + ' home=' + r2.homeUnitId + ' unit=' + wvSel.id);
    H.seekTo(6);
    var r3 = H.agents().filter(function (a) { return a.kind === 'route'; })[0];
    var xs = r3.silk.map(function (p) { return p.x; }), ys = r3.silk.map(function (p) { return p.y; });
    out.push('silkN=' + r3.silk.length);
    out.push('silk dx=' + (Math.max.apply(null, xs) - Math.min.apply(null, xs)).toFixed(0) +
             ' dy=' + (Math.max.apply(null, ys) - Math.min.apply(null, ys)).toFixed(0) + ' (cell ' + wvSel.w + 'x' + wvSel.h + ')');
    var inside = xs.every(function (x) { return Math.abs(x - wvSel.x) <= wvSel.w / 2; }) &&
                 ys.every(function (y) { return Math.abs(y - wvSel.y) <= wvSel.h / 2; });
    out.push('insideCell=' + inside);
    var box = document.createElement('pre');
    box.id = 'qaOut';
    box.style.cssText = 'position:fixed;left:0;top:0;z-index:99999;background:#000;color:#0f0;font:12px monospace;padding:8px;white-space:pre-wrap';
    box.textContent = out.join('\\n');
    document.body.appendChild(box);
  }, 600);
});
</script>''' % json.dumps(doc, ensure_ascii=False)

src2 = src.replace('</head>', inject + '</head>', 1)
tmp = os.path.join(TMP, 'qa-r22.html')
with io.open(tmp, 'w', encoding='utf-8', newline='') as f:
    f.write(src2)

cmd = [CHROME, '--headless=new', '--disable-gpu', '--no-first-run', '--window-size=1600,1000',
       '--virtual-time-budget=4000', '--dump-dom', 'file:///' + tmp.replace('\\', '/')]
p = subprocess.run(cmd, capture_output=True, timeout=90)
raw = p.stdout.decode('utf-8', 'replace')
i = raw.find('id="qaOut"')
print(html.unescape(raw[i:raw.find('</pre>', i)]) if i > 0 else ('none ' + p.stderr.decode('utf-8', 'replace')[:300]))
