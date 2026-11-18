# -*- coding: utf-8 -*-
import subprocess, os, tempfile, re
HTML = r"H:\tool\silkworm-trajectory\docs\index.html"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
JS = r"""
setTimeout(function(){
  try {
    var H = window.__studioHabitat;
    H.addWeave({ w: 240, h: 240 });
    var u = H.agents().filter(function(a){return a.kind==='weave'})[0];
    u.u = 0.8;
    document.getElementById('habVidRes').value = '854x480';
    document.getElementById('habVidSec').value = '5';
    document.getElementById('habVidFps').value = '30';
    document.getElementById('habVidBit').value = '8';
    setTimeout(function(){ document.getElementById('habVidRecord').click(); }, 500);
    setTimeout(function(){
      var d = document.createElement('div'); d.id = 'QAOUT';
      d.textContent = JSON.stringify({
        status: (document.getElementById('habVidStatus')||{}).textContent,
        btn: (document.getElementById('habVidRecord')||{}).textContent,
      });
      document.body.appendChild(d);
    }, 9000);
  } catch(e) {
    var d=document.createElement('div'); d.id='QAOUT'; d.textContent=JSON.stringify({err:String(e)});
    document.body.appendChild(d);
  }
}, 1200);
"""
with open(HTML, 'r', encoding='utf-8') as f:
    s = f.read()
s = s.replace('</body>', '<script>%s</script></body>' % JS)
p = os.path.join(tempfile.gettempdir(), 'qa-vid.html')
open(p, 'w', encoding='utf-8').write(s)
r = subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--window-size=1400,900',
                    '--virtual-time-budget=20000', '--dump-dom', 'file:///' + p.replace('\\', '/')],
                   capture_output=True, text=True, timeout=150)
m = re.search(r'id="QAOUT">(.*?)</div>', r.stdout, re.S)
print(m.group(1) if m else 'NO OUT')
