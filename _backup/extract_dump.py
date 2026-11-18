"""从 chrome --dump-dom 的输出里取出 <pre id="dump"> 的 JSON 并写文件。

用法：python _backup\\extract_dump.py dump.html exports\\weave-curves.json
"""

import html
import json
import re
import sys
from pathlib import Path


def main():
    src = Path(sys.argv[1]).read_text(encoding="utf-8")
    m = re.search(r'<pre id="dump">(.*?)</pre>', src, flags=re.S)
    if not m:
        raise SystemExit("找不到 <pre id=\"dump\">")
    data = json.loads(html.unescape(m.group(1)))
    out = Path(sys.argv[2])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{out}  {out.stat().st_size} bytes")


if __name__ == "__main__":
    main()
