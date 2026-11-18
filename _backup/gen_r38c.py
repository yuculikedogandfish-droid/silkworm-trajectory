import io, os
TMP=os.environ["TEMP"]
src=io.open(r"docs\index.html", encoding="utf-8").read()
JS = r"""
(async () => {
  const st=document.createElement('style'); st.textContent='body > *:not(#habitat):not(#habCtxMenu):not(script):not(style){display:none}'; document.head.appendChild(st);
  const H=window.__studioHabitat;
  const wait=(fn,ms=6000)=>new Promise((res,rej)=>{const t0=Date.now();(function p(){if(fn())return res();if(Date.now()-t0>ms)return rej('timeout');setTimeout(p,120);})();});
  await wait(()=>window.__studioHabitat);
  const mk=(x,y)=>{H.addWeave({}); const l=H.agents().filter(a=>a.kind==='weave'); const u=l[l.length-1]; u.w=260;u.h=260;u.tileField=false;u.x=x;u.y=y; u.custom={walls:{},paths:{},shapes:{'0,0':{notch:null,islands:[{cx:0,cy:0,r:80}]}}}; u.cache.clear(); H.buildWeave(u);};
  mk(-320,-160); mk(0,-160); mk(320,-160);
  const tree=document.getElementById('habLayerTree'); const log=[];
  await wait(()=>tree.querySelectorAll('input[data-pick]').length>=3);
  log.push('boxes='+tree.querySelectorAll('input[data-pick]').length);
  tree.querySelectorAll('input[data-pick]').forEach((b,i)=>{ if(i<2){ b.checked=true; b.dispatchEvent(new Event('change',{bubbles:true})); } });
  window.prompt=()=> '测试组'; window.alert=()=>{};
  document.getElementById('habLayerGroup').click();
  await wait(()=>tree.querySelectorAll('.lay-group[data-group]').length>0, 3000).catch(()=>{});
  log.push('groups='+tree.querySelectorAll('.lay-group[data-group]').length+' rows='+tree.querySelectorAll('.lay-row').length);
  log.push('LS='+((localStorage.getItem('silkworm-habitat-layer-groups/v1')||'none').slice(0,60));
  document.querySelector('.hab-rec-sum').textContent=log.join(' | ');
  if(window.__QA_EXPAND){ document.getElementById('habRecBox').open=true; }
  H.seekTo(4);
})();
"""
for tag, expand in (('r38-c', False), ('r38-d', True)):
    page = src + '<script>window.__QA_EXPAND=%s;</script><script>%s</script>' % ('true' if expand else 'false', JS)
    io.open(os.path.join(TMP, tag + '.html'), 'w', encoding='utf-8').write(page)
    print(tag)
