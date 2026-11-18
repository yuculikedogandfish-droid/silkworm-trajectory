"""用 gh CLI 调 GitHub REST API 提交（本机当前没有 git.exe）。

用法：
  python _backup\\gh_commit.py <owner/repo> <branch> --dry-run
  python _backup\\gh_commit.py <owner/repo> <branch> -m "commit message"

只提交工作区里与远端 tree 不同的文件；跳过 .git / _backup / exports。
"""

import base64
import hashlib
import json
import subprocess
import sys
from pathlib import Path

GH = r"C:\Program Files\GitHub CLI\gh.exe"
ROOT = Path(r"H:\tool\silkworm-trajectory")
SKIP_DIRS = {".git", "_backup", "exports"}
SKIP_NAMES = {".DS_Store", "Thumbs.db"}


def gh(args):
    p = subprocess.run([GH, "api"] + args, capture_output=True)
    if p.returncode != 0:
        raise SystemExit("gh api 失败: " + p.stderr.decode("utf-8", "replace")[:800])
    out = p.stdout.decode("utf-8", "replace").strip()
    return json.loads(out) if out else None


def gh_json(method, path, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    p = subprocess.run(
        [GH, "api", "--method", method, path, "--input", "-"],
        input=body, capture_output=True,
    )
    if p.returncode != 0:
        raise SystemExit(f"gh api {method} {path} 失败: " + p.stderr.decode("utf-8", "replace")[:1200])
    out = p.stdout.decode("utf-8", "replace").strip()
    return json.loads(out) if out else None


def blob_sha(data):
    h = hashlib.sha1()
    h.update(b"blob %d\0" % len(data))
    h.update(data)
    return h.hexdigest()


def local_files():
    files = {}
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT).as_posix()
        if any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts):
            continue
        if p.name in SKIP_NAMES:
            continue
        files[rel] = p
    return files


TEXT_EXT = {".md", ".html", ".json", ".js", ".mjs", ".csv", ".txt", ".py",
            ".ps1", ".svg", ".css", ".gitignore", ".yml", ".yaml"}


def normalized(p, data):
    """本地是 CRLF 检出的文件，按 git 的 LF 归一化后再算 blob。"""
    if p.suffix.lower() in TEXT_EXT or p.name == ".gitignore":
        return data.replace(b"\r\n", b"\n")
    return data


def main():
    repo, branch = sys.argv[1], sys.argv[2]
    dry = "--dry-run" in sys.argv
    msg = "P1: 织网引擎移植进蚕室（kind=weave 单格）"
    if "-m" in sys.argv:
        msg = sys.argv[sys.argv.index("-m") + 1]
    only = None
    if "--only" in sys.argv:
        i = sys.argv.index("--only") + 1
        only = [a for a in sys.argv[i:] if not a.startswith("-")]

    ref = gh([f"repos/{repo}/git/ref/heads/{branch}"])
    head = ref["object"]["sha"]
    commit = gh([f"repos/{repo}/git/commits/{head}"])
    base_tree = commit["tree"]["sha"]
    tree = gh([f"repos/{repo}/git/trees/{base_tree}?recursive=1"])
    remote = {e["path"]: e["sha"] for e in tree["tree"] if e["type"] == "blob"}

    local = local_files()
    if only:
        local = {k: v for k, v in local.items() if k in set(only)}
    changed, deleted = [], []
    for rel, p in sorted(local.items()):
        data = normalized(p, p.read_bytes())
        sha = blob_sha(data)
        if remote.get(rel) != sha:
            changed.append((rel, sha, p))
    if not only:
        for rel in remote:
            if rel not in local:
                deleted.append(rel)

    print(f"远端 head {head[:8]}  文件 {len(remote)}  本地文件 {len(local)}")
    for rel, sha, p in changed:
        mark = "新增" if rel not in remote else "修改"
        print(f"  {mark} {rel}  {p.stat().st_size} B")
    for rel in deleted:
        print(f"  删除 {rel}")

    if dry:
        print("dry-run，未提交")
        return
    if not changed and not deleted:
        print("没有变化，跳过提交")
        return

    entries = []
    for rel, sha, p in changed:
        data = normalized(p, p.read_bytes())
        b = gh_json("POST", f"repos/{repo}/git/blobs", {
            "content": base64.b64encode(data).decode("ascii"),
            "encoding": "base64",
        })
        entries.append({"path": rel, "mode": "100644", "type": "blob", "sha": b["sha"]})
    for rel in deleted:
        entries.append({"path": rel, "mode": "100644", "type": "blob", "sha": None})

    new_tree = gh_json("POST", f"repos/{repo}/git/trees", {"base_tree": base_tree, "tree": entries})
    new_commit = gh_json("POST", f"repos/{repo}/git/commits", {
        "message": msg, "tree": new_tree["sha"], "parents": [head],
    })
    gh_json("PATCH", f"repos/{repo}/git/refs/heads/{branch}", {"sha": new_commit["sha"], "force": False})
    print(f"已提交 {new_commit['sha'][:8]}  {msg}")


if __name__ == "__main__":
    main()
