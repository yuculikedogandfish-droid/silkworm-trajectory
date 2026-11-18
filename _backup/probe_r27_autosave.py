# -*- coding: utf-8 -*-
import subprocess, os, tempfile, re, shutil
HTML = r"H:\tool\silkworm-trajectory\docs\index.html"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROF = os.path.join(tempfile.gettempdir(), "qa-autosave-prof")
RESULT = os.path.join(tempfile.gettempdir(), "qa-autosave.html")


def page(js, tag):
    with open(HTML, 'r', encoding='utf-8') as f:
        s = f.read()
    s = s.replace('</body>', '<script>%s</script></body>' % js)
    p = os.path.join(tempfile.gettempdir(), 'qa-auto-%s.html' % tag)
    open(p, 'w', encoding='utf-8').write(s)
    return p


RUN1 = r"""
setTimeout(function(){
  try {
    var H = window.__studioHabitat;
    H.addWeave({ w: 240, h: 240 });
    var u = H.agents().filter(function(a){return a.kind==='weave'})[0];
    u.x = 120; u.y = -40; u.seed = 909;
    setTimeout(function(){
      var d = document.createElement('div'); d.id = 'QAOUT';
      d.textContent = JSON.stringify({ phase: 'write', units: H.agents().filter(function(a){return a.kind==='weave'}).length,
        stat: (document.getElementById('habAutoStat')||{}).textContent,
        saved: !!localStorage.getItem('silkworm-habitat-autosave/v1') });
      document.body.appendChild(d);
    }, 3800);
  } catch(e) { var d=document.createElement('div'); d.id='QAOUT'; d.textContent=JSON.stringify({err:String(e)}); document.body.appendChild(d); }
}, 1200);
"""

RUN2 = r"""
setTimeout(function(){
  try {
    var H = window.__studioHabitat;
    var us = H.agents().filter(function(a){return a.kind==='weave'});
    var d = document.createElement('div'); d.id = 'QAOUT';
    d.textContent = JSON.stringify({ phase: 'read', units: us.length,
      pos: us[0] ? [us[0].x, us[0].y, us[0].seed] : null,
      stat: (document.getElementById('habAutoStat')||{}).textContent });
    document.body.appendChild(d);
  } catch(e) { var d=document.createElement('div'); d.id='QAOUT'; d.textContent=JSON.stringify({err:String(e)}); document.body.appendChild(d); }
}, 2600);
"""

if os.path.isdir(PROF):
    shutil.rmtree(PROF, ignore_errors=True)
os.makedirs(PROF, exist_ok=True)

for tag, js in (('w', RUN1), ('r', RUN2)):
    p = page(js, tag)
    r = subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--user-data-dir=' + PROF,
                        '--window-size=1400,900', '--virtual-time-budget=15000', '--dump-dom',
                        'file:///' + p.replace('\\', '/')], capture_output=True, text=True, timeout=120)
    m = re.search(r'id="QAOUT">(.*?)</div>', r.stdout, re.S)
    print(tag.upper(), m.group(1) if m else 'NO OUT')
