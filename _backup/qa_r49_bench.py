# -*- coding: utf-8 -*-
"""r49g 性能探针：一次成品帧的合成耗时（决定导出会不会掉帧）"""
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
  // 注意：这里全程同步执行，故意让 load 事件被拖住 —— headless 的 --dump-dom 会等到 load 完成，
  // 期间不加 --virtual-time-budget，performance.now() 才是真实时间。
  try {
    for (var i = 0; i < 9; i++) H.addWeave();
    var U = H.agents().filter(function (a) { return a.kind === 'weave'; });
    log('单元数=' + U.length);
    U.forEach(function (a, j) {
      a.duration = 22; a.speedScale = 1;
      a.schedule = { order: j, manualStart: null };
      H.buildWeave(a);
    });
    [['1280x960', 1280, 960], ['1920x1440', 1920, 1440], ['2048x1536', 2048, 1536]].forEach(function (q) {
      var r = H.benchCompose(q[1], q[2]);
      log(q[0] + '：首帧(建缓存) ' + r.build + ' ms；之后每帧 ' + JSON.stringify(r.frames) + ' ms（共 ' + r.units + ' 块）');
    });
    log('jserrs=' + JSON.stringify(window.__errs));
  } catch (e) {
    log('ERR ' + e.message + '\n' + (e.stack || ''));
  }
  out.textContent = L.join('\n');
  out.setAttribute('done', '1');
});
</script>
<div id="qaout" style="position:fixed;left:6px;top:6px;z-index:99999;background:#000;color:#FC8;font:12px monospace;padding:6px;white-space:pre-wrap">pending</div>'''
style = '<style>body > *:not(#habitat):not(script):not(style):not(#qaout){display:none !important}</style>'
h = src.replace('<head>', '<head>\n' + TAG, 1).replace('</head>', style + TEST + '</head>', 1)
tmp = os.path.join(TMP, 'qa-r49-bench.html')
io.open(tmp, 'w', encoding='utf-8', newline='').write(h)
cmd = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run', '--disable-extensions',
       '--window-size=1500,950', '--dump-dom', 'file:///' + tmp.replace('\\', '/')]
r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=240)
m = re.search(r'<div id="qaout"[^>]*>([\s\S]*?)</div>', r.stdout)
print((m.group(1) if m else '(not found)').strip())
