import io, os, tempfile
TMP=tempfile.gettempdir()
src=io.open(r"docs\index.html",encoding="utf-8").read()
js=r"""<script>
window.addEventListener('load', function(){
  var st=document.createElement('style');
  st.textContent='body > *:not(#habitat):not(#habCtxMenu):not(script):not(style){display:none}';
  document.head.appendChild(st);
  var H=window.__studioHabitat;
  var mk=function(x,y){H.addWeave({}); var l=H.agents().filter(function(a){return a.kind==='weave';}); var u=l[l.length-1];
    u.w=240;u.h=240;u.tileField=false;u.x=x;u.y=y;u.worms=8;u.coverage=0.6;u.custom={walls:{},paths:{},shapes:{}};
    if(u.cache&&u.cache.clear)u.cache.clear(); H.buildWeave(u);};
  mk(-250,-60); mk(20,-60); mk(290,-60);
  window.__layerStore.load({groups:[{id:'g1',name:'上排两块',open:true}],member:{'wv-1':'g1','wv-2':'g1'},order:[]});
  H.seekTo(6);
});
</script>"""
io.open(os.path.join(TMP,'g42_sync.html'),'w',encoding='utf-8').write(src+js)
print('ok')
