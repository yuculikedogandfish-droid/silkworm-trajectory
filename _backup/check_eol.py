import hashlib, json, subprocess
from pathlib import Path

GH = r"C:\Program Files\GitHub CLI\gh.exe"
ROOT = Path(r"H:\tool\silkworm-trajectory")


def gh(args):
    p = subprocess.run([GH, "api"] + args, capture_output=True)
    out = p.stdout.decode("utf-8", "replace").strip()
    return json.loads(out) if out else None


def blob(data):
    h = hashlib.sha1()
    h.update(b"blob %d\0" % len(data))
    h.update(data)
    return h.hexdigest()


ref = gh(["repos/yuculikedogandfish-droid/silkworm-trajectory/git/ref/heads/main"])
commit = gh(["repos/yuculikedogandfish-droid/silkworm-trajectory/git/commits/" + ref["object"]["sha"]])
tree = gh(["repos/yuculikedogandfish-droid/silkworm-trajectory/git/trees/" + commit["tree"]["sha"] + "?recursive=1"])
remote = {e["path"]: e["sha"] for e in tree["tree"] if e["type"] == "blob"}

for rel in ["CHANGELOG_OPTIMIZATION.md", "docs/SCHEMA_MIGRATION.md", "tests/geometry_tests.mjs"]:
    data = (ROOT / rel).read_bytes()
    norm = data.replace(b"\r\n", b"\n")
    print(rel)
    print("  raw ", blob(data), "match" if blob(data) == remote.get(rel) else "")
    print("  lf  ", blob(norm), "match" if blob(norm) == remote.get(rel) else "")
