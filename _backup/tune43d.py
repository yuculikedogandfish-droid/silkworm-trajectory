import io
p=r"_backup\r43_module.js"
s=io.open(p,encoding="utf-8").read()
old_col = """    function colRun(x, y0, y1) {
      let best = 0, cur = 0, gap = 0;
      for (let y = y0; y <= y1; y++) {
        if (dark[y * w + x]) { cur += gap + 1; gap = 0; if (cur > best) best = cur; }
        else { gap++; if (gap > 2) { cur = 0; gap = 0; } }
      }
      return best;
    }"""
new_col = """    function colRun(x, y0, y1) {
      let n = 0;
      for (let y = y0; y <= y1; y++) if (dark[y * w + x]) n++;
      return n;
    }"""
old_row = """    function rowRun(y, x0, x1) {
      let best = 0, cur = 0, gap = 0;
      for (let x = x0; x <= x1; x++) {
        if (dark[y * w + x]) { cur += gap + 1; gap = 0; if (cur > best) best = cur; }
        else { gap++; if (gap > 2) { cur = 0; gap = 0; } }
      }
      return best;
    }"""
new_row = """    function rowRun(y, x0, x1) {
      let n = 0;
      for (let x = x0; x <= x1; x++) if (dark[y * w + x]) n++;
      return n;
    }"""
assert old_col in s and old_row in s
s=s.replace(old_col,new_col,1).replace(old_row,new_row,1)
s=s.replace("        if (sc < 0.55) continue;","        if (sc < 0.42) continue;")
io.open(p,"w",encoding="utf-8").write(s)
print("density ok")
