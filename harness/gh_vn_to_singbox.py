#!/usr/bin/env python3
"""Lay danh sach node proxy VN tu subscription YunaGRP (hoac URL ghi de)
va build config sing-box cho CI: mixed inbound 127.0.0.1:7891 + route final = nhom
urltest tu chon node VN con song.

Doc URL tu bien moi truong YUNA_SUB_URL (hoac tham so thu 2). Neu thieu URL,
khong tai duoc file, hoac khong co node proxy VN nao -> exit nonzero
(workflow FAIL ON AO, tuyet doi khong chay khong proxy).

Dung: python3 harness/gh_vn_to_singbox.py /tmp/singbox_ci.json [URL_GHI_DE]
Chi dung thu vien chuan.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "sing-box/1.14.4"}
PROXY_TYPES = {"vmess", "vless", "trojan", "shadowsocks", "hysteria", "hysteria2", "tuic", "socks", "http"}


def ensure_singbox_flag(url):
    url = (url or "").strip()
    if not url:
        return ""
    parts = urllib.parse.urlsplit(url)
    q = urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
    if not any(k.lower() == "flag" for k, _ in q):
        q.append(("flag", "singbox"))
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, urllib.parse.urlencode(q), parts.fragment))


def fetch(url, tries=4, timeout=40):
    last = None
    for i in range(1, tries + 1):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
            if len(data) < 100:
                raise ValueError(f"file qua nho: {len(data)} byte")
            return data
        except Exception as e:  # noqa: BLE001 - retry moi loi tam thoi
            last = e
            print(f"fetch attempt {i}/{tries} failed: {e}", file=sys.stderr)
            if i < tries:
                time.sleep(15)
    raise SystemExit(f"Khong tai duoc subscription proxy VN: {last}")


def is_vn_node(outbound):
    if not isinstance(outbound, dict):
        return False
    if outbound.get("type") not in PROXY_TYPES:
        return False
    tag = str(outbound.get("tag") or "")
    upper = tag.upper()
    return ("🇻🇳" in tag) or ("VIETNAM" in upper) or ("VIET NAM" in upper) or ("HANOI" in upper) or ("HCM" in upper)


def build(raw):
    try:
        cfg = json.loads(raw)
    except Exception as e:
        raise SystemExit(f"Subscription proxy VN khong phai JSON sing-box hop le: {e}")
    outbounds = cfg.get("outbounds") or []
    vn_nodes = [o for o in outbounds if is_vn_node(o)]
    if not vn_nodes:
        raise SystemExit("Subscription khong co node proxy Viet Nam nao")
    vn_tags = [o["tag"] for o in vn_nodes if o.get("tag")]
    if not vn_tags:
        raise SystemExit("Cac node proxy Viet Nam khong co tag hop le")
    tag = "auto-vn"
    group = {
        "type": "urltest",
        "tag": tag,
        "outbounds": vn_tags,
        "url": "https://www.gstatic.com/generate_204",
        "interval": "30s",
        "tolerance": 100,
    }
    new_cfg = {
        "log": {"level": "info", "timestamp": True},
        "inbounds": [
            {"type": "mixed", "tag": "mixed-in",
             "listen": "127.0.0.1", "listen_port": 7891},
        ],
        "outbounds": vn_nodes + [group, {"type": "direct", "tag": "direct"}],
        "route": {"final": tag},
    }
    return new_cfg, tag, vn_nodes


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/singbox_ci.json"
    raw_url = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("YUNA_SUB_URL", "")
    url = ensure_singbox_flag(raw_url)
    if not url:
        raise SystemExit("Thieu YUNA_SUB_URL (secret subscription YunaGRP)")
    cfg, tag, nodes = build(fetch(url))
    with open(out_path, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    servers = sorted({(o.get("type"), o.get("server"), o.get("server_port")) for o in nodes})
    print(f"YUNA-VN proxy OK: {len(nodes)} node VN, urltest={tag}, "
          f"servers={servers} -> {out_path}")


if __name__ == "__main__":
    main()
