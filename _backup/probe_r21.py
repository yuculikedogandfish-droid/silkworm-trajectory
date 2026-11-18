# -*- coding: utf-8 -*-
"""r21 验收：布局一屏 / 时间滑条 / 点列导入 / 单蚕默认格 / 撤销重做"""
import io, json, os, subprocess, tempfile, html

SRC = r'H:\tool\silkworm-trajectory\docs\index.html'
TRAJ = r'G:\raby model\trajectories.json'
TMP = r'C:\Users\54364\AppData\Local\Temp'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

with io.open(TRAJ, 'r', encoding='utf-8') as f:
    doc = json.load(f)

with io.open(SRC, 'r', encoding='utf-8') as f:
    src = f.read()

payload = json.dumps(doc, ensure_ascii=False)
harness = u'''
<script>
window.addEventListener('load', function () {
  setTimeout(function () {
    var out = [];
    function L(k, v) { out.push(k + ': ' + v); }
    try {
      var H = window.__studioHabitat;
      var hab = document.getElementById('habitat');
      var top = document.querySelector('.hab-top');
      var stage = document.querySelector('.hab-stage');
      var time = document.querySelector('.hab-time');
      L('viewport', window.innerWidth + 'x' + window.innerHeight);
      L('habitat.h', Math.round(hab.getBoundingClientRect().height));
      L('top.h', Math.round(top.getBoundingClientRect().height));
      L('stage.h', Math.round(stage.getBoundingClientRect().height));
      L('time.h', Math.round(time.getBoundingClientRect().height));
      var sum = top.getBoundingClientRect().height + stage.getBoundingClientRect().height + time.getBoundingClientRect().height;
      L('sum<=vh', (sum <= window.innerHeight + 2) + ' (' + Math.round(sum) + ')');
      L('page.overflowY', document.documentElement.scrollHeight > window.innerHeight + 2);
      var slider = document.getElementById('habTime');
      L('slider', slider ? 'present max=' + slider.max : 'MISSING');
      L('undoBtn', document.getElementById('habUndo') ? document.getElementById('habUndo').textContent : 'MISSING');
      L('redoBtn', document.getElementById('habRedo') ? document.getElementById('habRedo').textContent : 'MISSING');
      L('terms', document.querySelectorAll('.hab-legend-terms p').length + ' lines');
      var left = document.getElementById('habLeft');
      L('side.scrollable', left.scrollHeight + '/' + left.clientHeight);

      // 1. 点列导入
      var n = H.importPointCloudDoc(window.__QA_TRAJ);
      var agents = H.agents();
      var routes = agents.filter(function (a) { return a.kind === 'route'; });
      L('import', 'added=' + n + ' routes=' + routes.length +
        ' wormId=' + (routes[0] && routes[0].wormId) +
        ' pts=' + (routes[0] && routes[0].route.length));

      // 2. 单蚕时新格默认用它的数据
      H.addWeave();
      var wv = H.agents().filter(function (a) { return a.kind === 'weave'; })[0];
      L('weave.measuredWorm', wv ? wv.measuredWorm : 'none');

      // 3. 时间滑条：跳到 8s
      H.seekTo(8);
      var wv2 = H.agents().filter(function (a) { return a.kind === 'weave'; })[0];
      var rt = H.agents().filter(function (a) { return a.kind === 'route'; })[0];
      L('seek.simTime', H.agents() && (window.__studioHabitat.agents(), document.getElementById('habClock').textContent));
      L('seek.weaveU', wv2 ? wv2.u.toFixed(2) : '-');
      L('seek.routeSilk', rt ? rt.silk.length : '-');
      L('seek.mode', wv2 ? wv2.mode : '-');

      // 4. 撤销 / 重做
      var before = H.agents().length;
      H.undoStep();
      L('undo.agents', before + ' -> ' + H.agents().length);
      H.redoStep();
      L('redo.agents', before + ' -> ' + H.agents().length);
    } catch (e) {
      out.push('ERR: ' + e.message);
    }
    var box = document.createElement('pre');
    box.id = 'qaOut';
    box.style.cssText = 'position:fixed;left:0;top:0;z-index:99999;background:#000;color:#0f0;font:12px monospace;padding:8px;white-space:pre-wrap;max-width:100%';
    box.textContent = out.join('\\n');
    document.body.appendChild(box);
  }, 800);
});
</script>
'''

inject = '<script>window.__QA_TRAJ = ' + payload + ';</script>' + harness
src2 = src.replace('</head>', inject + '</head>', 1)
tmp = os.path.join(TMP, 'qa-r21.html')
with io.open(tmp, 'w', encoding='utf-8', newline='') as f:
    f.write(src2)

dom = os.path.join(TMP, 'qa-r21-dom.txt')
cmd = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars',
       '--no-first-run', '--disable-extensions',
       '--window-size=1600,1000', '--virtual-time-budget=4000',
       '--dump-dom', 'file:///' + tmp.replace('\\', '/')]
p = subprocess.run(cmd, capture_output=True, timeout=90)
with io.open(dom, 'w', encoding='utf-8') as f:
    f.write(p.stdout.decode('utf-8', 'replace'))
raw = p.stdout.decode('utf-8', 'replace')
i = raw.find('id="qaOut"')
if i > 0:
    j = raw.find('</pre>', i)
    seg = raw[i:j]
    seg = html.unescape(seg)
    print(seg[:2000])
else:
    print('no qaOut; stderr:', p.stderr.decode('utf-8', 'replace')[:500])
print('html', tmp)
