import io, json, base64, os
TMP=os.environ["TEMP"]
src=io.open(r"docs\index.html", encoding="utf-8").read()
b64=base64.b64encode(open(r"data\projects\参考图.png","rb").read()).decode()
JS = r"""
(async () => {
  const st=document.createElement('style'); st.textContent='body > *:not(#habitat):not(#habCtxMenu):not(script):not(style){display:none}'; document.head.appendChild(st);
  await new Promise(r=>setTimeout(r,700));
  const H=window.__studioHabitat, R=window.__imgRec;
  document.getElementById('habRecCols').value=3; document.getElementById('habRecRows').value=3;
  const out=document.createElement('div'); out.style.cssText='position:fixed;left:10px;bottom:10px;z-index:99999;color:#ffd76a;font:12px monospace;background:#000c;padding:6px;white-space:pre-wrap';
  (document.getElementById('habitat')||document.body).appendChild(out); const log=[]; const say=t=>{log.push(t);out.textContent=log.join(String.fromCharCode(10));};
  const img=new Image(); await new Promise((res,rej)=>{img.onload=res;img.onerror=rej;img.src=window.__QA_IMG;});
  const k=Math.min(1,1400/Math.max(img.width,img.height)); const w=Math.round(img.width*k), h=Math.round(img.height*k);
  const cv=document.createElement('canvas'); cv.width=w; cv.height=h; const cx=cv.getContext('2d'); cx.drawImage(img,0,0,w,h);
  const d=cx.getImageData(0,0,w,h).data; const g=new Uint8Array(w*h); for(let i=0,p=0;i<g.length;i++,p+=4) g[i]=(d[p]*0.299+d[p+1]*0.587+d[p+2]*0.114)|0;
  R.state.img={w,h,g}; R.analyse();
  say('格 '+R.state.grid.cols+'x'+R.state.grid.rows+' 有丝'+R.state.grid.present+' 孔'+R.state.holes.length);
  R.apply(false);
  const us=H.agents().filter(a=>a.kind==='weave');
  say('生成 '+us.length+' 块 '+us.map(u=>Math.round(u.w)+'x'+Math.round(u.h)+'@'+Math.round(u.x)+','+Math.round(u.y)).slice(0,4).join(' '));
  say('带孔块 '+us.filter(u=>u.custom&&u.custom.shapes&&u.custom.shapes['0,0']).length);
  H.seekTo(4);
})();
"""
page = src + '<script>window.__QA_IMG=%s;</script><script>%s</script>' % (json.dumps('data:image/png;base64,'+b64), JS)
io.open(os.path.join(TMP,'r37-small.html'),'w',encoding='utf-8').write(page)
print('ok')
