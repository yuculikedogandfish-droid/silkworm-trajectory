#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal CONNECT tunnel proxy for hosts whose DNS is poisoned.

Why: on some networks `github.com` resolves to an unreachable/blocked address
while a specific GitHub IP still works. Git itself always connects to
`github.com:443`, so we take the CONNECT request, ignore the poisoned DNS and
dial a known-good IP instead, keeping the TLS SNI / certificate check intact.

Usage:
  python gh-tunnel.py [--port 8899] [--map "github.com=140.82.113.4,api.github.com=140.82.113.6"]
Then:
  git -c http.proxy=http://127.0.0.1:8899 -c https.proxy=http://127.0.0.1:8899 push origin main
Stop with Ctrl+C (the helper PowerShell script stops it automatically).
"""
import argparse
import select
import socket
import sys
import threading

BUFSIZE = 65536


def pipe(a, b):
    try:
        while True:
            r, _, _ = select.select([a, b], [], [], 60)
            if not r:
                break
            for s in r:
                data = s.recv(BUFSIZE)
                if not data:
                    return
                (b if s is a else a).sendall(data)
    except (OSError, ValueError):
        pass


def handle(client, mapping):
    try:
        client.settimeout(20)
        head = b""
        while b"\r\n\r\n" not in head and len(head) < 8192:
            chunk = client.recv(4096)
            if not chunk:
                client.close()
                return
            head += chunk
        line = head.split(b"\r\n", 1)[0].decode("latin-1", "replace")
        parts = line.split()
        if len(parts) < 3 or parts[0].upper() != "CONNECT":
            client.sendall(b"HTTP/1.1 405 Method Not Allowed\r\n\r\n")
            client.close()
            return
        host, _, port_s = parts[1].rpartition(":")
        port = int(port_s or "443")
        target = mapping.get(host.lower(), host)
        up = socket.create_connection((target, port), timeout=20)
        client.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        client.settimeout(None)
        up.settimeout(None)
        pipe(client, up)
    except (OSError, ValueError):
        pass
    finally:
        for s in (client,):
            try:
                s.close()
            except OSError:
                pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8899)
    ap.add_argument("--map", default="github.com=140.82.113.4,api.github.com=140.82.113.6")
    a = ap.parse_args()
    mapping = {}
    for item in a.map.split(","):
        if "=" in item:
            k, v = item.split("=", 1)
            mapping[k.strip().lower()] = v.strip()
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", a.port))
    srv.listen(16)
    print("tunnel on 127.0.0.1:%d -> %s" % (a.port, mapping), flush=True)
    while True:
        c, _ = srv.accept()
        threading.Thread(target=handle, args=(c, mapping), daemon=True).start()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
