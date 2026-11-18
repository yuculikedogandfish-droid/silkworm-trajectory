import io,re
b=io.open(r"docs\蚕轨迹描图器_使用说明.pdf","rb").read()
print("pdf bytes",len(b),"pages",len(re.findall(rb"/Type\s*/Page[^s]",b)))
