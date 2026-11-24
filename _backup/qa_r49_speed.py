# -*- coding: utf-8 -*-
"""r49e 验收：默认全场速度改成 0.40×，旧工程停在 0.80× 时跟着迁移"""
import io, os, subprocess, re

ROOT = r'H:\tool\silkworm-trajectory'
SRC = ROOT + r'\docs\index.html'
TMP = r'C:\Users\54364\AppData\Local\Temp'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

src = io.open(SRC, encoding='utf-8').read()
TAG = r'''<script>window.__errs=[];window.addEventListener("error",function(e){__errs.push(e.message);});</script>'''

TEST = r'''<script>
window.addEventListener('load', function () {
  var H = window.__studioHabitat, out = document.getElementById('qaout');
  var L = [], log = function (s) { L.push(s); };
  var step = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };

  setTimeout(async function () {
    try {
      log('--- 新开局默认速度 ---');
      log('timeline().speed=' + H.timeline().speed + '（应 0.4）');
      log('左栏输入框 value=' + document.getElementById('habTlSpeed').value +
          '，左栏显示=' + (document.getElementById('habTlSpeedVal') || {}).textContent);

      log('--- 速度 -> 建议终点 ---');
      H.addWeave(); H.addWeave();
      await step(300);
      var U = H.agents().filter(function (a) { return a.kind === 'weave'; });
      U.forEach(function (a, i) { a.duration = 22; a.speedScale = 1; a.schedule = { order: i, manualStart: null }; });
      H.refreshTimeline();
      var r04 = H.timelineState();
      log('0.40×：state=' + JSON.stringify(r04) + '，建议终点=' + H.suggestedEnd() + ' s（应比 0.8 慢一倍时长）');
      document.getElementById('habTlSpeed').value = '0.8';
      document.getElementById('habTlSpeed').dispatchEvent(new Event('input', { bubbles: true }));
      await step(200);
      var r08 = H.timelineState();
      log('0.80×：建议终点=' + H.suggestedEnd() + ' s');

      log('--- 导入"停在旧默认 0.80×"的工程 ---');
      var proj = H.export();
      proj.timeline.speed = 0.8;
      H.import(proj);
      await step(250);
      log('导入后 speed=' + H.timeline().speed + '（应 0.4，旧默认视为没手动改过）');
      log('左栏输入框=' + document.getElementById('habTlSpeed').value);
      log('提示文案=' + ((document.getElementById('habToast') || {}).textContent || '').slice(0, 40));

      log('--- 手动调过的非默认值不被改 ---');
      var proj2 = H.export();
      proj2.timeline.speed = 0.5;
      H.import(proj2);
      await step(250);
      log('导入 0.5 后 speed=' + H.timeline().speed + '（应保持 0.5）');

      log('jserrs=' + JSON.stringify(window.__errs));
      out.textContent = L.join('\n');
      out.setAttribute('done', '1');
    } catch (e) {
      out.textContent = 'ERR ' + e.message + '\n' + (e.stack || '');
      out.setAttribute('done', '1');
    }
  }, 800);
});
</script>
<div id="qaout" style="position:fixed;left:6px;top:6px;z-index:99999;background:#000;color:#FC8;font:12px monospace;padding:6px;white-space:pre-wrap">pending</div>'''

style = '<style>body > *:not(#habitat):not(script):not(style):not(#qaout){display:none !important}</style>'
h = src.replace('<head>', '<head>\n' + TAG, 1).replace('</head>', style + TEST + '</head>', 1)
tmp = os.path.join(TMP, 'qa-r49-speed.html')
io.open(tmp, 'w', encoding='utf-8', newline='').write(h)

cmd = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
       '--disable-extensions', '--window-size=1500,950', '--virtual-time-budget=12000',
       '--dump-dom', 'file:///' + tmp.replace('\\', '/')]
r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=240)
m = re.search(r'<div id="qaout"[^>]*>([\s\S]*?)</div>', r.stdout)
print((m.group(1) if m else '(not found)').strip())
