# -*- coding: utf-8 -*-
"""r49g 出片验证：WebCodecs 逐帧编码 → WebM，用 ffprobe 核对帧数/分辨率/时长"""
import io, os, subprocess, re, base64
ROOT = r'H:\tool\silkworm-trajectory'
SRC = ROOT + r'\docs\index.html'
TMP = r'C:\Users\54364\AppData\Local\Temp'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
src = io.open(SRC, encoding='utf-8').read()
TEST = r'''<script>
window.addEventListener('load', function () {
  var H = window.__studioHabitat, out = document.getElementById('qaout');
  var L = [], log = function (s) { L.push(s); };
  (async function () {
    try {
      for (var i = 0; i < 4; i++) H.addWeave();
      var U = H.agents().filter(function (a) { return a.kind === 'weave'; });
      U.forEach(function (a, j) {
        a.duration = 22; a.speedScale = 1;
        a.schedule = { order: j, manualStart: null };
        H.buildWeave(a);
      });
      log('VideoEncoder 存在=' + (typeof window.VideoEncoder === 'function') +
          '，VideoFrame 存在=' + (typeof window.VideoFrame === 'function'));
      var r = await H.encodeTest(640, 360, 24, 24, 8);
      if (!r.ok) { log('编码不可用：' + r.reason); }
      else {
        log('编码完成：' + r.frames + '/' + r.total + ' 帧，' + (r.bytes / 1024).toFixed(1) + ' KB，耗时 ' +
            r.ms + ' ms，末帧时间戳 ' + r.lastMs + ' ms');
      }
      log('__B64__' + (r.ok ? r.b64 : ''));
    } catch (e) {
      log('ERR ' + e.message + '\n' + (e.stack || ''));
    }
    out.textContent = L.join('\n');
 robust: ;
  })();
});
</script>
<div id="qaout" style="position:fixed;left:6px;top:6px;z-index:99999;background:#000;color:#FC8;font:12px monospace;padding:6px;white-space:pre-wrap">pending</div>'''
TEST = TEST.replace(" robust: ;", "")
style = '<style>body > *:not(#habitat):not(script):not(style):not(#qaout){display:none !important}</style>'
h = src.replace('<head>', '<head>', 1).replace('</head>', style + TEST + '</head>', 1)
tmp = os.path.join(TMP, 'qa-r49-enc.html')
io.open(tmp, 'w', encoding='utf-8', newline='').write(h)
cmd = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run', '--disable-extensions',
       '--window-size=1200,800', '--virtual-time-budget=25000', '--dump-dom', 'file:///' + tmp.replace('\\', '/')]
r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=240)
m = re.search(r'<div id="qaout"[^>]*>([\s\S]*?)</div>', r.stdout)
txt = (m.group(1) if m else '(not found)')
logs, b64 = txt.split('__B64__') if '__B64__' in txt else (txt, '')
print(logs.strip())
if b64.strip():
    out = os.path.join(TMP, 'qa-r49-enc.webm')
    io.open(out, 'wb').write(base64.b64decode(b64.strip()))
    print('webm ->', out, os.path.getsize(out), 'bytes')
    pr = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
                         '-show_entries', 'stream=codec_name,width,height,nb_read_frames,r_frame_rate:format=duration,size',
                         '-of', 'default=nw=1', out], capture_output=True, text=True, encoding='utf-8', timeout=120)
    print(pr.stdout.strip() or pr.stderr.strip())
