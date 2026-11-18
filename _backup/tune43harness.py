import io
mod=io.open(r"_backup\r43_module.js",encoding="utf-8").read()
for tag in ("v","h"):
    p=rf"_backup\rec43\t_{tag}.html"
    s=io.open(p,encoding="utf-8").read()
    i=s.find("/* ===== r43"); j=s.find("</script>",i)
    s=s[:i]+mod.rstrip()+s[j:]
    s=s.replace("window.__imgRec.readDataURL(IMG, function(){","window.__rec43close = (location.hash === '#r0' ? 0 : (location.hash === '#r2' ? 2 : 1));\nwindow.__imgRec.readDataURL(IMG, function(){")
    io.open(p,"w",encoding="utf-8").write(s)
print("harness updated")
