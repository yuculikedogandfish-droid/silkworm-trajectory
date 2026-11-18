import io
p=r"_backup\r39_module.js"
s=io.open(p,encoding="utf-8").read()
old="""        ctx.drawImage(world, sx, sy, sw, sh, 0, 0, cv.width, cv.height);
        ctx.strokeStyle = 'rgba(255,255,255,0.14)';"""
new="""        ctx.drawImage(world, sx, sy, sw, sh, 0, 0, cv.width, cv.height);
        ctx.globalCompositeOperation = 'lighter';
        ctx.globalAlpha = 0.55;
        ctx.drawImage(world, sx, sy, sw, sh, 0, 0, cv.width, cv.height);
        ctx.globalAlpha = 1;
        ctx.globalCompositeOperation = 'source-over';
        ctx.strokeStyle = 'rgba(255,255,255,0.14)';"""
assert s.count(old)==1
s=s.replace(old,new)
io.open(p,"w",encoding="utf-8").write(s)
P=r"docs\index.html"
h=io.open(P,encoding="utf-8").read()
i=h.find("/* ===== r39 个体与图层合并"); st=h.rfind("<script>",0,i); en=h.find("</script>",i)
h=h[:st]+s.rstrip()+h[en+len("</script>"):]
io.open(P,"w",encoding="utf-8").write(h)
print("thumb brighten ok")
