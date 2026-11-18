# -*- coding: utf-8 -*-
import subprocess, json, os, tempfile
HTML = r"H:\tool\silkworm-trajectory\docs\index.html"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUT = os.path.join(tempfile.gettempdir(), "qa-r26-weave.png")
JS = r"""
(async () => {
  const H = window.__studioHabitat;
  await new Promise(r => setTimeout(r, 250));
  H.addWeave({ w: 300, h: 300 });
  H.addWeave({ w: 300, h: 300 });
  await H.importPointCloudDoc(window.__QA_CLOUD);
  const us = H.agents().filter(a => a.kind === 'weave');
  if (us[0]) { us[0].x = -180; us[0].y = 0; us[0].w = us[0].h = 300; us[0].seed = 101; us[0].cache = new Map(); }
  if (us[1]) { us[1].x = 190; us[1].y = 0; us[1].w = us[1].h = 300; us[1].seed = 303; us[1].cache = new Map(); }
  H.assignWormToUnit(us[0].id, 'all');
  H.assignWormToUnit(us[1].id, 'all');
  [us[0], us[1]].forEach(u => { if (u) { u.u = 1; } });
  await new Promise(r => setTimeout(r, 300));
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
tmp = os.path.join(tempfile.gettempdir(), "qa-r26-weave.html")
open(tmp, 'w', encoding='utf-8').write(html)
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--window-size=1600,1000",
                "--virtual-time-budget=6000", "--screenshot=" + OUT, "file:///" + tmp.replace("\\", "/")],
               timeout=90)
print("shot", OUT, os.path.getsize(OUT))
