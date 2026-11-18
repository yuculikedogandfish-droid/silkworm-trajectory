import io
p=r"_backup\gen_g42.py"
s=io.open(p,encoding="utf-8").read()
s=s.replace("  window.__tick=setTimeout(arguments[0] && window.__more ? window.__more : function(){}, 0);",
            "  setTimeout(function(){ try{ if(window.__more) window.__more(); }catch(e){ document.title='ERR '+e.message; } }, 80);")
io.open(p,"w",encoding="utf-8").write(s)
print("fixed")
