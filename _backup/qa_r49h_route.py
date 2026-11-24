# -*- coding: utf-8 -*-
"""r49h 验收：路线织造页（路径几何 / 丝线渲染 / 逐帧编码 WebM 合法性）"""
import io, os, subprocess, re, base64, json
ROOT = r'H:\tool\silkworm-trajectory'
SRC = ROOT + r'\docs\路线织造.html'
TMP = r'C:\Users\54364\AppData\Local\Temp'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
FFPROBE = r'C:\Users\54364\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffprobe.exe'
FFMPEG = FFPROBE.replace('ffprobe.exe', 'ffmpeg.exe')

src = io.open(SRC, encoding='utf-8').read()
TEST = r'''<script>
window.__errs = [];
window.addEventListener('error', function (e) { window.__errs.push(String(e.message)); });
window.addEventListener('load', function () {
  var out = document.getElementById('qaout');
  var L = [], log = function (s) { L.push(s); };
  var step = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
  setTimeout(async function () {
    try {
      var R = window.__routeWeave, S = R.S;
      log('=== ① 路径几何 ===');
      var p0 = R.paths()[0];
      log('初始路线：' + R.paths().length + ' 条，类型=' + p0.type + '，采样点=' + p0.samples.length +
          '，一圈长=' + Math.round(p0.len) + '，圈数=' + (p0.laps || 1) + '，总长=' + Math.round(R.routeLen()));
      R.addPath('line'); R.addPath('closed'); R.addPath('open');
      log('加三条后：' + R.paths().length + ' 条；类型=' +
          R.paths().map(function (p) { return p.type + '(' + p.ctrl.length + '点/' + Math.round(p.len) + ')'; }).join(' '));
      log('总长=' + Math.round(R.routeLen()) + '，自动时长=' + R.dur().toFixed(2) + ' s（速度 ' + S.speed + ' u/s）');
      // 正圆不循环 = 只算一圈
      p0.loop = false;
      log('正圆关掉循环后总长=' + Math.round(R.routeLen()) + '（应减少 ' + Math.round(p0.len * (p0.laps - 1)) + '）');
      p0.loop = true;

      log('=== ② 成片帧（只有丝 + 背景，没有蚕/手柄）===');
      log('__PNG_MID__' + R.framePng(640, 480, 0.45));
      log('__PNG_END__' + R.framePng(640, 480, 1));

      log('=== ③ 逐帧编码 ===');
      var res = await R.encodeTest(640, 480, 24, 24);
      log('编码 ' + res.frames + ' 帧，耗时 ' + res.ms + ' ms，parts=' + res.parts);
      log('jserrs=' + JSON.stringify(window.__errs));
    } catch (e) {
      log('ERR ' + e.message + '\n' + (e.stack || ''));
    }
    out.textContent = L.join('\n');
    out.setAttribute('done', '1');
  }, 500);
});
</script>
<div id="qaout" style="position:fixed;left:6px;top:6px;z-index:99999;background:#000;color:#FC8;font:12px monospace;padding:6px;white-space:pre-wrap">pending</div>'''
h = src.replace('</head>', TEST + '</head>', 1)
h = h.replace('</body>', '<script>window.__grab=1;</script></body>')
tmp = os.path.join(TMP, 'qa-r49h-route.html')
io.open(tmp, 'w', encoding='utf-8', newline='').write(h)
cmd = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
       '--disable-extensions', '--window-size=1400,900', '--virtual-time-budget=30000',
       '--dump-dom', 'file:///' + tmp.replace('\\', '/')]
r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=300)
m = re.search(r'<div id="qaout"[^>]*>([\s\S]*?)</div>', r.stdout)
txt = m.group(1) if m else '(not found)\n' + r.stdout[:2000] + '\n' + r.stderr[:2000]
mid = re.findall(r'__PNG_MID__data:image/png;base64,([A-Za-z0-9+/=]+)', txt)
endpng = re.findall(r'__PNG_END__data:image/png;base64,([A-Za-z0-9+/=]+)', txt)
txt = re.sub(r'__PNG_(MID|END)__[^\n]+', '[png omitted]', txt)
print(txt.strip())
for name, data in (('qa-r49h-route-mid.png', mid), ('qa-r49h-route-end.png', endpng)):
    if data:
        pth = os.path.join(TMP, name)
        io.open(pth, 'wb').write(base64.b64decode(data[-1]))
        print('png ->', pth, os.path.getsize(pth))
