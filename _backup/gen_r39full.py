import io, os
TMP=os.environ["TEMP"]
src=io.open(r"docs\index.html",encoding="utf-8").read()
JS=r"""
(async () => {
  const st=document.createElement('style'); st.textContent='body > *:not(#habitat):not(#habCtxMenu):not(script):not(style){display:none}'; document.head.appendChild(st);
  await new Promise(r=>setTimeout(r,700));
  const H=window.__studioHabitat;
  const mk=(x,y)=>{const n=H.agents().filter(a=>a.kind==='weave').length; H.addWeave({}); const l=H.agents().filter(a=>a.kind==='weave'); const u=l[l.length-1]; u.w=250;u.h=250;u.tileField=false;u.x=x;u.y=y; u.custom={walls:{},paths:{},shapes:{'0,0':{notch:null,islands:[{cx:0,cy:-10,r:76}]}}}; if(u.cache&&u.cache.clear)u.cache.clear(); H.buildWeave(u); return u;};
  const a=mk(-260,-40), b=mk(0,-40), c=mk(260,-40);
  window.__layerStore.load({groups:[{id:'g1',name:'上排两块',open:true}],member:{'wv-1':'g1','wv-2':'g1'},order:[]});
  H.seekTo(3);
  const doc=H.export();
  document.title='R39 '+JSON.stringify({ids:[a.id,b.id,c.id], groupCount:(doc.layerGroups||{}).groups?doc.layerGroups.groups.length:-1, member:doc.layerGroups?doc.layerGroups.member:null, rows:document.querySelectorAll('#habLayerTree .lay-row').length, w:document.getElementById('habLayerTree').innerText.replace(/\n/g,' ~ ').slice(0,160)});
})();
"""
io.open(os.path.join(TMP,'r39_full.html'),'w',encoding='utf-8').write(src+'<script>%s</script>'%JS)
print('ok')
