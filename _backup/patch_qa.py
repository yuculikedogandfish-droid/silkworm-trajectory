import re
p = r"_backup\gen_edit_qa_r30.py"
s = open(p, encoding="utf-8").read()
s = s.replace("""  const status = [];""", """  const status = [];
  const out = document.createElement('div');
  out.id = 'QAOUT';
  out.style.cssText = 'position:fixed;left:12px;bottom:64px;z-index:99999;color:#ffd76a;font:13px monospace;background:#000c;padding:6px;max-width:900px';
  document.body.appendChild(out);
  const say = (s) => { status.push(s); out.textContent = status.join(' | '); };""")
s = s.replace("status.push(", "say(")
s = s.replace("say('QA:: ' + status.join(' | '));", "")
s = s.replace("""  if (wallBtn) wallBtn.click();""", """  if (wallBtn) wallBtn.click();
  say('C2_tool=' + (wallBtn ? wallBtn.getAttribute('aria-pressed') : 'notfound'));""")
open(p, "w", encoding="utf-8").write(s)
print("patched")
