# -*- coding: utf-8 -*-
import subprocess, json, os, tempfile
HTML = r"H:\tool\silkworm-trajectory\docs\index.html"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUT = os.path.join(tempfile.gettempdir(), "qa-r25-edit.png")
JS = r"""
(async () => {
  const H = window.__studioHabitat;
  await new Promise(r => setTimeout(r, 250));
  H.addWeave({ w: 260, h: 260 });
  H.addWeave({ w: 260, h: 260 });
  await H.importPointCloudDoc(window.__QA_CLOUD);
  const us = H.agents().filter(a => a.kind === 'weave');
  if (us[0]) { us[0].x = -170; us[0].y = 0; }
  if (us[1]) { us[1].x = 190; us[1].y = 0; }
  H.assignWormToUnit(us[0].id, 'all');
  H.assignWormToUnit(us[1].id, 'all');
  H.seekTo(8);
  await new Promise(r => setTimeout(r, 200));
  const cv = document.getElementById('habWorld');
  const r = cv.getBoundingClientRect();
  const v = H.view();
  const kx = r.width / cv.width, ky = r.height / cv.height;
  const px = r.left + v.px(us[0].x) * kx, py = r.top + v.py(us[0].y) * ky;
  cv.dispatchEvent(new PointerEvent('pointerdown', { clientX: px, clientY: py, bubbles: true, pointerId: 1, button: 0 }));
  cv.dispatchEvent(new PointerEvent('pointerup', { clientX: px, clientY: py, bubbles: true, pointerId: 1, button: 0 }));
  await new Promise(r => setTimeout(r, 120));
  document.getElementById('habWeaveEdit').click();
  await new Promise(r => setTimeout(r, 200));
  if (us[0]) { H.assignWormToUnit(us[0].id, 'all'); }
  const s = document.createElement('style');
  s.textContent = 'body > *:not(#habitat):not(script):not(style){display:none}';
  document.head.appendChild(s);
})();
"""
with open(HTML, 'r', encoding='utf-8') as f:
    html = f.read()
cloud = json.load(open(r"G:\raby model\trajectories.json", encoding='utf-8'))
inject = "<script>window.__QA_CLOUD=%s;%s</script>" % (json.dumps(cloud), JS)
html = html.replace("</body>", inject + "</body>")
tmp = os.path.join(tempfile.gettempdir(), "qa-r25-edit.html")
open(tmp, 'w', encoding='utf-8').write(html)
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--window-size=1600,1000",
                "--virtual-time-budget=6000", "--screenshot=" + OUT, "file:///" + tmp.replace("\\", "/")],
               timeout=90)
print("shot", OUT, os.path.getsize(OUT))
