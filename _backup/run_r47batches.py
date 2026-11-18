# -*- coding: utf-8 -*-
import subprocess, tempfile, os, shutil
ROOT=r'H:\tool\silkworm-trajectory'
CHROME=r'C:\Program Files\Google\Chrome\Application\chrome.exe'
url='file:///'+(ROOT+r'\_backup\rec43\qa_r47.html').replace('\\','/')
for n in range(7):
    ud=os.path.join(tempfile.gettempdir(),'udd-r47batch'+str(n))
    shutil.rmtree(ud,ignore_errors=True)
    args=[CHROME,'--headless=new','--disable-gpu','--enable-logging=stderr','--user-data-dir='+ud,'--virtual-time-budget=7000','--window-size=1000,800','--screenshot='+os.path.join(tempfile.gettempdir(),'r47batch'+str(n)+'.png'),url+'#b'+str(n)]
    try:
        p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=25)
        txt=p.stdout.decode('utf-8','replace')
        lines=[x for x in txt.splitlines() if 'QA ' in x or 'written to file' in x]
        print('batch',n,'ok',p.returncode,' | '.join(lines[-4:]),flush=True)
    except subprocess.TimeoutExpired as e:
        print('batch',n,'TIMEOUT',flush=True)
