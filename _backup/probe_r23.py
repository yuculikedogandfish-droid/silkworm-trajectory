# -*- coding: utf-8 -*-
"""r23 验收：同一种蚕可同时用在多格、实例互不抢占、随机起点"""
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
    var sel = document.getElementById('habWeaveWorm');
    function pick(unitId) {
      H.agents(); // noop
      var ev = new Event('change');
      // 通过点击选中个体
      var card = Array.prototype.find.call(document.querySelectorAll('#habAgents [data-id]'), function (c) { return c.dataset.id === unitId; });
      return card;
    }
    // 直接在面板里按 id 选中：用 __studioHabitat 暴露的 agents + 点击卡片
    units[0].w = 260; units[0].h = 260; H.buildWeave(units[0]);
    units[1].w = 260; units[1].h = 260; H.buildWeave(units[1]);
    units[1].x = units[0].x + 340;
    // 选中第一块
    var card0 = document.querySelector('#habAgents [data-id="' + units[0].id + '"]');
    if (card0) card0.click();
    sel.value = '1'; sel.dispatchEvent(new Event('change'));
    var inst0 = H.agents().filter(function (a) { return a.kind === 'route' && a.homeUnitId === units[0].id; });
    // 选中第二块
    var card1 = document.querySelector('#habAgents [data-id="' + units[1].id + '"]');
    if (card1) card1.click();
    sel.value = '1'; sel.dispatchEvent(new Event('change'));
    var inst1 = H.agents().filter(function (a) { return a.kind === 'route' && a.homeUnitId === units[1].id; });
    out.push('unitA instances=' + inst0.length + ' ids=' + inst0.map(function (a) { return a.id; }).join(','));
    out.push('unitB instances=' + inst1.length + ' ids=' + inst1.map(function (a) { return a.id; }).join(','));
    out.push('totalRoute=' + H.agents().filter(function (a) { return a.kind === 'route'; }).length + ' (源蚕应仍在)');
    out.push('startA=' + inst0.map(function (a) { return a.offX.toFixed(0) + ',' + a.offY.toFixed(0); }).join('|') +
             ' unitA center=' + units[0].x.toFixed(0) + ',' + units[0].y.toFixed(0));
    H.seekTo(5);
    var s0 = H.agents().filter(function (a) { return a.kind === 'route' && a.homeUnitId === units[0].id; })[0];
    var s1 = H.agents().filter(function (a) { return a.kind === 'route' && a.homeUnitId === units[1].id; })[0];
    out.push('silkA=' + (s0 ? s0.silk.length : '-') + ' silkB=' + (s1 ? s1.silk.length : '-'));
    var box = document.createElement('pre');
    box.id = 'qaOut';
    box.style.cssText = 'position:fixed;left:0;top:0;z-index:99999;background:#000;color:#0f0;font:12px monospace;padding:8px;white-space:pre-wrap';
    box.textContent = out.join('\\n');
    document.body.appendChild(box);
  }, 600);
});
</script>''' % json.dumps(doc, ensure_ascii=False)

src2 = src.replace('</head>', inject + '</head>', 1)
tmp = os.path.join(TMP, 'qa-r23.html')
with io.open(tmp, 'w', encoding='utf-8', newline='') as f:
    f.write(src2)
cmd = [CHROME, '--headless=new', '--disable-gpu', '--no-first-run', '--window-size=1600,1000',
       '--virtual-time-budget=4000', '--dump-dom', 'file:///' + tmp.replace('\\', '/')]
p = subprocess.run(cmd, capture_output=True, timeout=90)
raw = p.stdout.decode('utf-8', 'replace')
i = raw.find('id="qaOut"')
print(html.unescape(raw[i:raw.find('</pre>', i)]) if i > 0 else ('none ' + p.stderr.decode('utf-8', 'replace')[:300]))
