# -*- coding: utf-8 -*-
"""r49 P0-4 验收探针：点开始进入成品预览、letterbox 比例、装饰是否消失"""
import io, os, subprocess, re

ROOT = r'H:\tool\silkworm-trajectory'
SRC = ROOT + r'\docs\index.html'
TMP = r'C:\Users\54364\AppData\Local\Temp'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

src = io.open(SRC, encoding='utf-8').read()
probe = r'''<script>window.__errs=[];window.addEventListener("error",function(e){__errs.push(e.message);});</script>'''

TEST = r'''<script>
window.addEventListener('load', function () {
  var H = window.__studioHabitat, out = document.getElementById('qaout');
  var L = [], log = function (s) { L.push(s); };
  setTimeout(function () {
    try {
      H.addWeave(); H.addWeave();
      var units = H.agents().filter(function (a) { return a.kind === 'weave'; });
      units[0].x = -110; units[0].y = 0; units[0].w = units[0].h = 190;
      units[1].x = 110; units[1].y = 0; units[1].w = units[1].h = 190;
      units.forEach(function (u) { H.buildWeave(u); });
      document.getElementById('habStart').click();
      setTimeout(function () {
        H.seekTo(20);
        setTimeout(function () {
          var cv = document.getElementById('habWorld');
          var ctx = cv.getContext('2d');
          var res = document.getElementById('habLedRes').value.split('x');
          var aspect = (+res[0]) / (+res[1]);
          function lum(x, y) { var d = ctx.getImageData(Math.round(x), Math.round(y), 1, 1).data; return (d[0] + d[1] + d[2]) / 3; }
          log('finalPreview=' + H.finalPreview());
          log('exitBtn_hidden=' + document.getElementById('habPreviewExit').hidden);
          log('letterbox_top_lum=' + lum(cv.width / 2, 3).toFixed(1) + ' center_lum=' + lum(cv.width / 2, cv.height / 2).toFixed(1));
          log('export_aspect=' + aspect.toFixed(4) + ' canvas=' + cv.width + 'x' + cv.height);
          document.getElementById('habPause').click();
          log('pause_still_preview=' + H.finalPreview());
          document.getElementById('habResume').click();
          log('resume_still_preview=' + H.finalPreview());
          log('jserrs=' + JSON.stringify(window.__errs));
          out.textContent = L.join('\n');
          out.setAttribute('done', '1');
        }, 500);
      }, 700);
    } catch (e) {
      out.textContent = 'ERR ' + e.message + '\n' + (e.stack || '');
      out.setAttribute('done', '1');
    }
  }, 700);
});
</script>
<div id="qaout" style="position:fixed;left:6px;top:6px;z-index:99999;background:#000;color:#7CFFB2;font:12px monospace;padding:6px;white-space:pre-wrap">pending</div>'''

style = '<style>body > *:not(#habitat):not(script):not(style):not(#qaout){display:none !important}</style>'
h = src.replace('<head>', '<head>\n' + probe, 1).replace('</head>', style + TEST + '</head>', 1)
tmp = os.path.join(TMP, 'qa-r49-preview.html')
io.open(tmp, 'w', encoding='utf-8', newline='').write(h)

cmd = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
       '--disable-extensions', '--window-size=1500,950', '--virtual-time-budget=7000',
       '--dump-dom', 'file:///' + tmp.replace('\\', '/')]
r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=180)
m = re.search(r'<div id="qaout"[^>]*>([\s\S]*?)</div>', r.stdout)
print((m.group(1) if m else '(not found)').strip())

shot = os.path.join(TMP, 'qa-r49-preview.png')
cmd2 = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
        '--disable-extensions', '--window-size=1500,950', '--virtual-time-budget=7000',
        '--screenshot=' + shot, 'file:///' + tmp.replace('\\', '/')]
subprocess.run(cmd2, capture_output=True, timeout=180)
print('shot', shot, os.path.exists(shot) and os.path.getsize(shot))
