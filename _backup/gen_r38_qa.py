import io, os
TMP=os.environ["TEMP"]
src=io.open(r"docs\index.html", encoding="utf-8").read()
JS = r"""
(async () => {
  const st=document.createElement('style'); st.textContent='body > *:not(#habitat):not(#habCtxMenu):not(script):not(style){display:none}'; document.head.appendChild(st);
  await new Promise(r=>setTimeout(r,700));
  const H=window.__studioHabitat;
  const mk=(x,y)=>{H.addWeave({}); const l=H.agents().filter(a=>a.kind==='weave'); const u=l[l.length-1]; u.w=260;u.h=260;u.tileField=false;u.x=x;u.y=y; u.custom={walls:{},paths:{},shapes:{'0,0':{notch:null,islands:[{cx:0,cy:0,r:80}]}}}; u.cache.clear(); H.buildWeave(u);};
  mk(-320,-160); mk(0,-160); mk(320,-160);
  const tree=document.getElementById('habLayerTree');
  const boxes=tree.querySelectorAll('input[data-pick]');
  boxes[0].checked=true; boxes[0].dispatchEvent(new Event('change',{bubbles:true}));
  boxes[1].checked=true; boxes[1].dispatchEvent(new Event('change',{bubbles:true}));
  window.prompt=()=> '测试组';
  document.getElementById('habLayerGroup').click();
  if(window.__QA_EXPAND){ document.getElementById('habRecBox').open=true; }
  const out=document.createElement('div'); out.style.cssText='position:fixed;left:10px;bottom:8px;z-index:99999;color:#ffd76a;font:12px monospace;background:#000c;padding:4px 6px;white-space:pre-wrap';
  (document.getElementById('habitat')||document.body).appendChild(out);
  const g=tree.querySelectorAll('.lay-group').length, r=tree.querySelectorAll('.lay-row').length;
  out.textContent='groups='+g+' rows='+r+' agents='+H.agents().filter(a=>a.kind==='weave').length;
  H.seekTo(4);
})();
"""
for tag, expand in (('r38-a', False), ('r38-b', True)):
    page = src + '<script>window.__QA_EXPAND=%s;</script><script>%s</script>' % ('true' if expand else 'false', JS)
    io.open(os.path.join(TMP, tag + '.html'), 'w', encoding='utf-8').write(page)
    print(tag)
