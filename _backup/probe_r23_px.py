import subprocess, json, os, tempfile
HTML = r"H:\tool\silkworm-trajectory\docs\index.html"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
JS = r"""
(async () => {
  const H = window.__studioHabitat;
  await new Promise(r => setTimeout(r, 300));
  H.addWeave({ w: 280, h: 280, x: -160, y: 0 });
  H.addWeave({ w: 280, h: 280, x: 170, y: 6 });
  await H.importPointCloudDoc(window.__QA_CLOUD);
  const us = H.agents().filter(a => a.kind === 'weave');
  us.forEach(u => H.assignWormToUnit(u.id, 'all'));
  H.seekTo(5);
  await new Promise(r => setTimeout(r, 260));
  const v = H.view();
  const cvs = document.querySelector('canvas');
  const ctx = cvs.getContext('2d');
  const out = [];
  us.forEach(u => {
    const x0 = v.px(u.x - u.w/2), x1 = v.px(u.x + u.w/2);
    const y0 = v.py(u.y - u.h/2), y1 = v.py(u.y + u.h/2);
    out.push({id:u.id, rect:[Math.round(x0),Math.round(y0),Math.round(x1),Math.round(y1)]});
    // 采样格子右侧 12..40 px 竖带
    let lit = 0;
    const band = ctx.getImageData(Math.round(x1)+12, Math.round(y0), 28, Math.round(y1-y0));
    for (let i = 0; i < band.data.length; i += 4) {
      if (band.data[i] + band.data[i+1] + band.data[i+2] > 30) lit++;
    }
    out[out.length-1].rightBandLit = lit;
  });
  const d = document.createElement('pre');
  d.style.cssText = 'position:fixed;left:280px;top:60px;z-index:9;color:#0f0;font:12px monospace';
  d.textContent = JSON.stringify(out);
  document.body.appendChild(d);
})();
"""
with open(HTML, 'r', encoding='utf-8') as f:
    html = f.read()
cloud = json.load(open(r"G:\raby model\trajectories.json", encoding='utf-8'))
inject = "<script>window.__QA_CLOUD=%s;%s</script>" % (json.dumps(cloud), JS)
html = html.replace("</body>", inject + "</body>")
tmp = os.path.join(tempfile.gettempdir(), "qa-r23px.html")
open(tmp, 'w', encoding='utf-8').write(html)
out = os.path.join(tempfile.gettempdir(), "qa-r23px.png")
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--window-size=1600,1000",
                "--virtual-time-budget=9000", "--screenshot=" + out, "file:///" + tmp.replace("\\", "/")],
               timeout=90)
print("shot", out, os.path.getsize(out))
