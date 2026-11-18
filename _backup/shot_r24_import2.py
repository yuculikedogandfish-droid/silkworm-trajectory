# -*- coding: utf-8 -*-
import subprocess, json, os, tempfile
HTML = r"H:\tool\silkworm-trajectory\docs\index.html"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUT = os.path.join(tempfile.gettempdir(), "qa-r24-import.png")
JS = r"""
(async () => {
  const H = window.__studioHabitat;
  await new Promise(r => setTimeout(r, 250));
  H.addWeave({ w: 260, h: 260 });
  H.addWeave({ w: 260, h: 260 });
  H.addWeave({ w: 260, h: 260 });
  await H.importPointCloudDoc(window.__QA_CLOUD);
  const us = H.agents().filter(a => a.kind === 'weave');
  const pos = [[-340, 0], [0, 0], [340, 0]];
  us.forEach((u, i) => { if (pos[i]) { u.x = pos[i][0]; u.y = pos[i][1]; } });
  H.assignWormToUnit(us[0].id, 'all');
  H.assignWormToUnit(us[1].id, 'all');
  H.assignWormToUnit(us[2].id, '1');
  H.seekTo(16);
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
tmp = os.path.join(tempfile.gettempdir(), "qa-r24-import.html")
open(tmp, 'w', encoding='utf-8').write(html)
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--window-size=1600,1000",
                "--virtual-time-budget=12000", "--screenshot=" + OUT, "file:///" + tmp.replace("\\", "/")],
               timeout=120)
print("shot", OUT, os.path.getsize(OUT))

