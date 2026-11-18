"""把 weave-lab.html 的 <script> 块拆成 .js 文件，供 node --check 逐个校验。

用法：python _backup\\extract_weave_js.py prototype\\weave-lab.html C:\\Temp\\weave-js
"""

import re
import sys
from pathlib import Path


def main():
    html_path = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    text = html_path.read_text(encoding="utf-8")
    blocks = re.findall(r"<script[^>]*>([\s\S]*?)</script>", text, flags=re.I)
    for i, body in enumerate(blocks):
        target = out_dir / f"script_{i}.js"
        target.write_text(body, encoding="utf-8")
        print(f"{target}  {len(body)} bytes  {body.count(chr(10)) + 1} lines")
    print(f"blocks: {len(blocks)}")


if __name__ == "__main__":
    main()
