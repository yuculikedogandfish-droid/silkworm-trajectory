import urllib.request
u = "https://yuculikedogandfish-droid.github.io/silkworm-trajectory/"
r = urllib.request.Request(u, headers={"Cache-Control": "no-cache"})
s = urllib.request.urlopen(r, timeout=40).read().decode("utf-8", "replace")
print("len", len(s))
print("guide links", s.count("使用说明（图文）"))
print("href count", s.count('href="使用说明.html"'))
