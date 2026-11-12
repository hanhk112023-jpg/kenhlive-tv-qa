#!/usr/bin/env python3
"""Lay danh sach node proxy VN moi nhat tu file GitHub cong khai Au1rxx
(free-vpn-subscriptions/output/country/VN/singbox-0001.json) va build config
sing-box cho CI: mixed inbound 127.0.0.1:7891 + route final = nhom urltest
("auto") cua file goc, tu chon node VN con song.

Thay the co che YUNA cu (secret YUNA_PROXY_YAML / YUNA_SUB_URL + mihomo):
khong can secret nao nua. Neu khong tai duoc file, file khong co node VLESS,
hoac khong co nhom urltest -> exit nonzero (workflow FAIL ON AO, tuyet doi
khong chay khong proxy).

Dung: python3 harness/gh_vn_to_singbox.py /tmp/singbox_ci.json [URL_GHI_DE]
Chi dung thu vien chuan (khong can PyYAML nhu ci_sub_to_yaml.py cu).
"""
import json
import sys
import time
import urllib.request

DEFAULT_URL = ("https://raw.githubusercontent.com/Au1rxx/free-vpn-subscriptions"
               "/main/output/country/VN/singbox-0001.json")
UA = {"User-Agent": "kenhlive-tv-qa/1.0 (CI proxy setup)"}


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
                time.sleep(20)
    raise SystemExit(f"Khong tai duoc file proxy VN tu {url}: {last}")


def build(raw):
    try:
        cfg = json.loads(raw)
    except Exception as e:
        raise SystemExit(f"File proxy VN khong phai JSON hop le: {e}")
    outbounds = cfg.get("outbounds") or []
    vless = [o for o in outbounds if o.get("type") == "vless"]
    if not vless:
        raise SystemExit("File proxy VN khong co node VLESS nao")
    urltest = [o for o in outbounds if o.get("type") == "urltest"]
    if not urltest:
        raise SystemExit("File proxy VN khong co nhom urltest")
    group = urltest[0]
    tag = group.get("tag") or "auto"
    # Chi giu node VLESS trong nhom urltest; bo endpoint WireGuard (khong dung
    # trong CI) va moi tag khong phai outbound VLESS de config check khong loi.
    vless_tags = [o["tag"] for o in vless if o.get("tag")]
    group["outbounds"] = [t for t in vless_tags]
    new_cfg = {
        "log": {"level": "info", "timestamp": True},
        "inbounds": [
            {"type": "mixed", "tag": "mixed-in",
             "listen": "127.0.0.1", "listen_port": 7891},
        ],
        "outbounds": vless + [group],
        "route": {"final": tag},
    }
    return new_cfg, tag, vless


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/singbox_ci.json"
    url = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_URL
    cfg, tag, vless = build(fetch(url))
    with open(out_path, "w") as f:
        json.dump(cfg, f, indent=2)
    servers = sorted({(o.get("server"), o.get("server_port")) for o in vless})
    print(f"GH-VN proxy OK: {len(vless)} node VLESS, urltest={tag}, "
          f"servers={servers} -> {out_path}")


if __name__ == "__main__":
    main()
