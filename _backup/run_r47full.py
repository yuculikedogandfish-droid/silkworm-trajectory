# -*- coding: utf-8 -*-
import subprocess,tempfile,os,shutil
ROOT=r'H:\tool\silkworm-trajectory'; CHROME=r'C:\Program Files\Google\Chrome\Application\chrome.exe'
ud=os.path.join(tempfile.gettempdir(),'udd-r47fullprobe');shutil.rmtree(ud,ignore_errors=True)
url='file:///'+(ROOT+r'\_backup\rec43\qa_r47.html').replace('\\','/')
args=[CHROME,'--headless=new','--disable-gpu','--enable-logging=stderr','--user-data-dir='+ud,'--virtual-time-budget=2000','--window-size=1440,1000','--screenshot='+os.path.join(tempfile.gettempdir(),'r47visual.png'),url+'#visual']
try:
 p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=35)
 txt=p.stdout.decode('utf-8','replace')
except subprocess.TimeoutExpired as e:
 txt=(e.stdout or b'').decode('utf-8','replace')
 print('TIMEOUT')
for line in txt.splitlines():
 if 'QA ' in line or 'ERR ' in line or 'written to file' in line: print(line)
