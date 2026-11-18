# -*- coding: utf-8 -*-
import subprocess, json, os, tempfile, re
HTML = r"H:\tool\silkworm-trajectory\docs\index.html"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
JS = r"""
(async () => {
  const out = [];
  const put = (o) => {
    let d = document.getElementById('QAOUT');
    if (!d) { d = document.createElement('div'); d.id = 'QAOUT'; document.body.appendChild(d); }
    d.textContent = JSON.stringify(o);
  };
  try {
    const H = window.__studioHabitat;
    if (!H) { put({ err: 'no H' }); return; }
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
    H.assignWormToUnit(us[2].id, 'worm-1');
    H.seekTo(5);
    await new Promise(r => setTimeout(r, 300));
    const hw = 260 / 2 * 0.98, hh = 260 / 2 * 0.98;
    H.agents().filter(a => a.kind === 'route' && a.scope === 'cell').forEach(a => {
      const u = us.find(x => x.id === a.homeUnitId);
      if (!u) { out.push({ ag: a.id, note: 'no-unit' }); return; }
      let bad = 0, maxd = 0, n = (a.silk || []).length;
      (a.silk || []).forEach(p => {
        const dx = Math.max(0, Math.abs(p.x - u.x) - hw), dy = Math.max(0, Math.abs(p.y - u.y) - hh);
        const d = Math.hypot(dx, dy);
        if (d > 1e-6) { bad++; if (d > maxd) maxd = d; }
      });
      out.push({ ag: a.id, unit: u.id, silkPts: n, outside: bad, maxOver: +maxd.toFixed(2) });
    });
    us.forEach(u => {
      const c = H.weaveCellContent(u, 0, 0);
      let bad = 0, maxd = 0, pts = 0;
      (c.paths || []).forEach(p => (p.pts || []).forEach(q => {
        pts++;
        const dx = Math.max(0, Math.abs(q.x) - hw), dy = Math.max(0, Math.abs(q.y) - hh);
        const d = Math.hypot(dx, dy);
        if (d > 1e-6) { bad++; if (d > maxd) maxd = d; }
      }));
      out.push({ unit: u.id, bands: (c.paths || []).length, pathPts: pts, outside: bad, maxOver: +maxd.toFixed(2) });
    });
    put(out);
  } catch (e) {
    out.push({ err: String(e), stack: (e && e.stack ? String(e.stack).split("QA")[0] : "") });
    put(out);
  }
})();
"""
with open(HTML, 'r', encoding='utf-8') as f:
    html = f.read()
cloud = json.load(open(r"G:\raby model\trajectories.json", encoding='utf-8'))
inject = "<script>window.__QA_CLOUD=%s;%s</script>" % (json.dumps(cloud), JS)
html = html.replace("</body>", inject + "</body>")
tmp = os.path.join(tempfile.gettempdir(), "qa-r23i2.html")
open(tmp, 'w', encoding='utf-8').write(html)
r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--window-size=1600,1000",
                    "--virtual-time-budget=9000", "--dump-dom", "file:///" + tmp.replace("\\", "/")],
                   capture_output=True, text=True, timeout=120)
m = re.search(r'id="QAOUT">(.*?)</div>', r.stdout, re.S)
import sys; print((m.group(1)[:1500] if m else "NO OUT"))

