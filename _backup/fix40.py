import io
p=r"_backup\gen_r40test.py"
s=io.open(p,encoding="utf-8").read()
drag=r"""  // 编辑态下从块体（避开手柄）拖：整组应一起走
  ev(world,'pointerdown',140,140);
  ev(world,'pointermove',170,150); ev(world,'pointermove',170,150);
  res.push('edit_drag=' + Math.round(AGENTS[0].x) + ',' + Math.round(AGENTS[1].x) + ',' + Math.round(AGENTS[0].y));
  ev(world,'pointerup',170,150);
"""
menu_block = """  var mb=tree.querySelector('[data-menu="wv-1"]'); mb.click();
  res.push('menu_items=' + (document.querySelectorAll('.lay-menu button').length));
  document.querySelector('.lay-menu button').click(); // 锁定
  res.push('locked=' + !!AGENTS[0].locked);
"""
assert drag in s and menu_block in s
s = s.replace(drag, "")
s = s.replace(menu_block, drag + menu_block)
io.open(p,"w",encoding="utf-8").write(s)
print("reordered")
