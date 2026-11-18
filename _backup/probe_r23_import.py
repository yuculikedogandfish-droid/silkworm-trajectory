# -*- coding: utf-8 -*-
import subprocess, json, os, tempfile, re
HTML = r"H:\tool\silkworm-trajectory\docs\index.html"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
JS = r"""
(async () => {
  const H = window.__studioHabitat;
  await new Promise(r => setTimeout(r, 250));
  H.addWeave({ w: 260, h: 260 });
  H.addWeave({ w: 260, h: 260 });
  H.addWeave({ w: 260, h: 260 });
  await H.importPointCloudDoc(window.__QA_CLOUD);
  const us = H.agents().filter(a => a.kind === 'weave');
  const pos = [[-340,0],[0,0],[340,0]];
  us.forEach((u,i) => { if (pos[i]) { u.x = pos[i][0]; u.y = pos[i][1]; } });
  us.forEach(u => H.buildWeave(u));
  // 第 1 格：全部蚕；第 2 格：全部蚕；第 3 格：只放蚕1（复用验证）
  H.assignWormToUnit(us[0].id, 'all');
  H.assignWormToUnit(us[1].id, 'all');
  H.assignWormToUnit(us[2].id, 'worm-1');
  H.seekTo(5);
  await new Promise(r => setTimeout(r, 350));

  const out = [];
  const rectOf = u => ({ x0: u.x - u.w/2, x1: u.x + u.w/2, y0: u.y - u.h/2, y1: u.y + u.h/2 });
  // 1) 丝迹：每只收进格的蚕，有多少点越出所属格
  H.agents().filter(a => a.kind === 'route' && a.scope === 'cell').forEach(a => {
    const u = us.find(u => u.id === a.homeUnitId);
    if (!u) { out.push({ ag: a.id, note: 'no unit' }); return; }
    const r = rectOf(u), k = 0.98;
    const hw = u.w/2*k, hh = u.h/2*k;
    let bad = 0, maxd = 0, n = (a.silk||[]).length;
    (a.silk||[]).forEach(p => {
      const dx = Math.max(0, Math.abs(p.x-u.x)-hw), dy = Math.max(0, Math.abs(p.y-u.y)-hh);
      const d = Math.hypot(dx,dy);
      if (d > 1e-6) { bad++; if (d > maxd) maxd = d; }
    });
    out.push({ ag: a.id, unit: u.id, silk: n, outside: bad, maxOver: +maxd.toFixed(2),
      bbox: n ? [Math.min.apply(null,a.silk.map(p=>p.x)).toFixed(1), Math.max.apply(null,a.silk.map(p=>p.x)).toFixed(1),
                 Math.min.apply(null,a.silk.map(p=>p.y)).toFixed(1), Math.max.apply(null,a.silk.map(p=>p.y)).toFixed(1)].join(',') : '' });
  });
  // 2) 织块：每格内容里有多少路径点越出格
  us.forEach(u => {
    const c = H.weaveCellContent(u, 0, 0);
    const hw = u.w/2*0.98, hh = u.h/2*0.98;
    let bad = 0, maxd = 0, pts = 0;
    (c.paths||[]).forEach(p => (p.pts||[]).forEach(q => {
      pts++;
      const dx = Math.max(0, Math.abs(q.x)-hw), dy = Math.max(0, Math.abs(q.y)-hh);
      const d = Math.hypot(dx,dy);
      if (d > 1e-6) { bad++; if (d>maxd) maxd = d; }
    }));
    out.push({ unit: u.id, bands: (c.paths||[]).length, pts: pts, outside: bad, maxOver: +maxd.toFixed(2),
      cov: (()=>{ let s=0; (c.paths||[]).forEach(p=>{ if(p.len) s+=p.len; }); return +(s/ (u.w*u.h) ).toFixed(3); })() });
  });
  const d = document.createElement('div');
  d.id = 'QAOUT';
  d.textContent = JSON.stringify(out);
  document.body.appendChild(d);
})();
"""
with open(HTML, 'r', encoding='utf-8') as f:
    html = f.read()
cloud = json.load(open(r"G:\raby model\trajectories.json", encoding='utf-8'))
inject = "<script>window.__QA_CLOUD=%s;%s</script>" % (json.dumps(cloud), JS)
html = html.replace("</body>", inject + "</body>")
tmp = os.path.join(tempfile.gettempdir(), "qa-r23i.html")
open(tmp, 'w', encoding='utf-8').write(html)
r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--window-size=1600,1000",
                    "--virtual-time-budget=9000", "--dump-dom", "file:///" + tmp.replace("\\", "/")],
                   capture_output=True, text=True, timeout=120)
m = re.search(r'id="QAOUT">(.*?)</div>', r.stdout, re.S)
if m:
    for it in json.loads(m.group(1)):
        print(it)
else:
    print("NO OUT")
