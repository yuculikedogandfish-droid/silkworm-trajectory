import io, base64, json
ROOT = r"H:\tool\silkworm-trajectory"
content = base64.b64encode(io.open(ROOT + r"\docs\index.html", "rb").read()).decode("ascii")
body = {
    "message": "r44: prominent guide entry links (tracer header + habitat top bar)",
    "content": content,
    "sha": "cdab20f9ce3ff45401de2bfd3167de8ee821c7d5",
    "branch": "main",
}
io.open(ROOT + r"\_backup\r44_api_body.json", "w", encoding="utf-8").write(json.dumps(body))
print("body bytes", len(json.dumps(body)))
