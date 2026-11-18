import io, os
TMP=os.environ["TEMP"]
src=io.open(r"docs\index.html", encoding="utf-8").read()
JS = r"""
(async () => {
  const st=document.createElement('style'); st.textContent='body > *:not(#habitat):not(#habCtxMenu):not(script):not(style){display:none}'; document.head.appendChild(st);
  await new Promise(r=>setTimeout(r,800));
  const H=window.__studioHabitat;
  const mk=(x,y)=>{H.addWeave({}); const l=H.agents().filter(a=>a.kind==='weave'); const u=l[l.length-1]; u.w=260;u.h=260;u.tileField=false;u.x=x;u.y=y; u.custom={walls:{},paths:{},shapes:{'0,0':{notch:null,islands:[{cx:0,cy:0,r:80}]}}}; u.cache.clear(); H.buildWeave(u);};
  mk(-320,-160); mk(0,-160); mk(320,-160);
  const tree=document.getElementById('habLayerTree');
  const pickAll=()=>{ tree.querySelectorAll('input[data-pick]').forEach((b,i)=>{ if(i<2){ b.checked=true; b.dispatchEvent(new Event('change',{bubbles:true})); } }); };
  pickAll();
  window.prompt=()=> '测试组';
  window.alert=()=>{};
  document.getElementById('habLayerGroup').click();
  await new Promise(r=>setTimeout(r,300));
  let g=tree.querySelectorAll('.lay-group[data-group]').length;
  if(!g){ pickAll(); document.getElementById('habLayerGroup').click(); await new Promise(r=>setTimeout(r,300)); g=tree.querySelectorAll('.lay-group[data-group]').length; }
  document.getElementById('habSyncStat').textContent='groups='+g+' rows='+tree.querySelectorAll('.lay-row').length;
  if(window.__QA_EXPAND){ document.getElementById('habRecBox').open=true; }
  H.seekTo(4);
})();
"""
for tag, expand in (('r38-a', False), ('r38-b', True)):
    page = src + '<script>window.__QA_EXPAND=%s;</script><script>%s</script>' % ('true' if expand else 'false', JS)
    io.open(os.path.join(TMP, tag + '.html'), 'w', encoding='utf-8').write(page)
    print(tag)
