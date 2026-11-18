import io, os
TMP=os.environ["TEMP"]
src=io.open(r"docs\index.html", encoding="utf-8").read()
JS = r"""
(async () => {
  const st=document.createElement('style'); st.textContent='body > *:not(#habitat):not(#habCtxMenu):not(script):not(style){display:none}'; document.head.appendChild(st);
  await new Promise(r=>setTimeout(r,800));
  const H=window.__studioHabitat;
  const mk=(x,y)=>{H.addWeave({}); const l=H.agents().filter(a=>a.kind==='weave'); const u=l[l.length-1]; u.w=250;u.h=250;u.tileField=false;u.x=x;u.y=y; u.custom={walls:{},paths:{},shapes:{'0,0':{notch:null,islands:[{cx:0,cy:-10,r:76}]}}}; u.cache.clear(); H.buildWeave(u);};
  mk(-260,-40); mk(0,-40); mk(260,-40);
  document.getElementById('habRecBox').open = true;
  document.getElementById('habRecDropText').textContent='点击选择图片，或把图片直接拖到这里';
  H.seekTo(3);
})();
"""
page = src + '<script>%s</script>' % JS
io.open(os.path.join(TMP,'r38-e.html'),'w',encoding='utf-8').write(page)
print('ok')
