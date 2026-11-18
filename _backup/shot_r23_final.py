import subprocess, json, os, tempfile
HTML = r"H:\tool\silkworm-trajectory\docs\index.html"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
STYLE = "body > *:not(#habitat):not(script):not(style){display:none}"
JS = r"""
(async () => {
  const H = window.__studioHabitat;
  await new Promise(r => setTimeout(r, 300));
  H.addWeave({ w: 280, h: 280 });
  H.addWeave({ w: 280, h: 280 });
  await H.importPointCloudDoc(window.__QA_CLOUD);
  const us = H.agents().filter(a => a.kind === 'weave');
  if (us[0]) { us[0].x = -160; us[0].y = 0; }
  if (us[1]) { us[1].x = 170; us[1].y = 6; }
  us.forEach(u => H.assignWormToUnit(u.id, 'all'));
  H.seekTo(5);
  const s = document.createElement('style');
  s.textContent = "%s";
  document.head.appendChild(s);
})().catch(e => { const d=document.createElement('div'); d.id='QAERR'; d.textContent=String(e); document.body.appendChild(d); });
""" % STYLE
with open(HTML, 'r', encoding='utf-8') as f:
    html = f.read()
cloud = json.load(open(r"G:\raby model\trajectories.json", encoding='utf-8'))
inject = "<script>window.__QA_CLOUD=%s;%s</script>" % (json.dumps(cloud), JS)
html = html.replace("</body>", inject + "</body>")
tmp = os.path.join(tempfile.gettempdir(), "qa-r23final.html")
open(tmp, 'w', encoding='utf-8').write(html)
out = os.path.join(tempfile.gettempdir(), "qa-r23-final.png")
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--window-size=1600,1000",
                "--virtual-time-budget=9000", "--screenshot=" + out, "file:///" + tmp.replace("\\", "/")],
               timeout=90)
print("shot", out, os.path.getsize(out))
