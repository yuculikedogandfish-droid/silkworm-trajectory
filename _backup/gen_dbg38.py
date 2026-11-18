import io, os
TMP=os.environ["TEMP"]
src=io.open(r"docs\index.html", encoding="utf-8").read()
JS = r"""
(async () => {
  const st=document.createElement('style'); st.textContent='body > *:not(#habitat):not(#habCtxMenu):not(script):not(style){display:none}'; document.head.appendChild(st);
  await new Promise(r=>setTimeout(r,900));
  const H=window.__studioHabitat;
  H.addWeave({}); H.addWeave({});
  const tree=document.getElementById('habLayerTree');
  const log=[];
  log.push('rows0='+tree.querySelectorAll('.lay-row').length);
  const bs=tree.querySelectorAll('input[data-pick]');
  log.push('boxes='+bs.length);
  bs[0].checked=true; bs[0].dispatchEvent(new Event('change',{bubbles:true}));
  bs[1].checked=true; bs[1].dispatchEvent(new Event('change',{bubbles:true}));
  window.prompt=()=> 'G1'; window.alert=(m)=>log.push('ALERT:'+m);
  document.getElementById('habLayerGroup').click();
  log.push('LS='+(localStorage.getItem('silkworm-habitat-layer-groups/v1')||'none'));
  log.push('groups='+tree.querySelectorAll('.lay-group[data-group]').length+' rows='+tree.querySelectorAll('.lay-row').length);
  document.title = 'QA|' + log.join(' || ');
  const d=document.createElement('pre'); d.id='qaout'; d.textContent=log.join('\n'); document.body.appendChild(d);
})();
"""
page = src + '<script>%s</script>' % JS
io.open(os.path.join(TMP,'r38-dbg.html'),'w',encoding='utf-8').write(page)
print('ok')
