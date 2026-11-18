import io, os, json
TMP=os.environ["TEMP"]
store={"groups":[{"id":"g1","name":"上排三块","open":True}],"member":{"wv-1":"g1","wv-2":"g1"}}
seed = "<!doctype html><script>localStorage.setItem('silkworm-habitat-layer-groups/v1', %s);document.title='seeded';</script>" % json.dumps(json.dumps(store))
io.open(os.path.join(TMP,'seed38.html'),'w',encoding='utf-8').write(seed)
src=io.open(r"docs\index.html", encoding="utf-8").read()
JS = r"""
(async () => {
  const st=document.createElement('style'); st.textContent='body > *:not(#habitat):not(#habCtxMenu):not(script):not(style){display:none}'; document.head.appendChild(st);
  await new Promise(r=>setTimeout(r,800));
  const H=window.__studioHabitat;
  const mk=(x,y)=>{H.addWeave({}); const l=H.agents().filter(a=>a.kind==='weave'); const u=l[l.length-1]; u.w=250;u.h=250;u.tileField=false;u.x=x;u.y=y; u.custom={walls:{},paths:{},shapes:{'0,0':{notch:null,islands:[{cx:0,cy:-10,r:76}]}}}; u.cache.clear(); H.buildWeave(u);};
  mk(-260,-40); mk(0,-40); mk(260,-40);
  H.seekTo(3);
})();
"""
io.open(os.path.join(TMP,'r38-f.html'),'w',encoding='utf-8').write(src + '<script>%s</script>' % JS)
print('ok')
