#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path


def config_lines(path):
    return {
        line.strip()
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.startswith("CONFIG_") or line.startswith("# CONFIG_")
    }


def symbol(line):
    if line.startswith("# "):
        return line.split()[1]
    return line.split("=", 1)[0]


parser = argparse.ArgumentParser()
parser.add_argument("--config", required=True)
parser.add_argument("--diffconfig", required=True)
parser.add_argument("--baseline", required=True)
parser.add_argument("--report", required=True)
args = parser.parse_args()

full = config_lines(args.config)
current = config_lines(args.diffconfig)
baseline = config_lines(args.baseline)
by_symbol = {symbol(line): line for line in full}
errors = []

required_y = [
    "CONFIG_TARGET_ipq50xx",
    "CONFIG_TARGET_ipq50xx_arm",
    "CONFIG_TARGET_ipq50xx_arm_DEVICE_cmcc_rax3000q",
    "CONFIG_PACKAGE_iptables-mod-tproxy",
    "CONFIG_PACKAGE_iptables-mod-iprange",
    "CONFIG_PACKAGE_iptables-mod-conntrack-extra",
    "CONFIG_PACKAGE_kmod-ipt-tproxy",
    "CONFIG_PACKAGE_kmod-ipt-iprange",
    "CONFIG_PACKAGE_kmod-ipt-conntrack-extra",
    "CONFIG_PACKAGE_kmod-ipt-raw",
    "CONFIG_PACKAGE_luci-app-passwall",
    "CONFIG_PACKAGE_luci-app-passwall_Iptables_Transparent_Proxy",
]
for key in required_y:
    if by_symbol.get(key) != f"{key}=y":
        errors.append(f"required selection missing or not y: {key}")

required_unset = [
    "CONFIG_PACKAGE_luci-app-passwall_Nftables_Transparent_Proxy",
    "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_Geoview",
    "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_Haproxy",
    "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_Hysteria",
    "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_NaiveProxy",
    "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_Shadowsocks_Rust_Client",
    "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_Shadowsocks_Rust_Server",
    "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_ShadowsocksR_Libev_Client",
    "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_ShadowsocksR_Libev_Server",
    "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_Shadow_TLS",
    "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_Simple_Obfs",
    "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_SingBox",
    "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_V2ray_Geodata",
    "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_V2ray_Plugin",
    "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_Xray",
    "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_Xray_Plugin",
]
for key in required_unset:
    if by_symbol.get(key) != f"# {key} is not set":
        errors.append(f"forbidden PassWall option is not explicitly unset: {key}")

for fake in (
    "CONFIG_PACKAGE_iptables-mod-socket",
    "CONFIG_PACKAGE_iptables-zz-legacy",
):
    if fake in by_symbol:
        errors.append(f"nonexistent compatibility symbol survived defconfig: {fake}")

for key, line in by_symbol.items():
    if line != f"{key}=y":
        continue
    low = key.lower()
    if any(name in low for name in (
        "passwall2", "hysteria", "naiveproxy", "sing-box", "singbox",
        "xray", "trojan-go", "trojan_go", "shadow-tls", "simple-obfs",
        "v2ray-plugin", "v2ray-geodata", "v2ray-geoip", "v2ray-geosite",
        "shadowsocks-rust", "shadowsocksr-libev", "geoview", "haproxy",
    )):
        errors.append(f"forbidden unrelated proxy selection: {key}")
    if key in {
        "CONFIG_PACKAGE_firewall4", "CONFIG_PACKAGE_nftables",
        "CONFIG_PACKAGE_kmod-nft-socket", "CONFIG_PACKAGE_kmod-nft-tproxy",
        "CONFIG_PACKAGE_kmod-nft-nat",
    }:
        errors.append(f"forbidden nftables route selection: {key}")

hardware = re.compile(
    r"^CONFIG_(TARGET_ipq50xx|ATH11K_|PACKAGE_TURBOACC_|PACKAGE_autocore-arm|"
    r"PACKAGE_kmod-(qca-nss|leds-gpio|mtd-rw|tun|tcp-bbr|sched-core))"
)
for expected in sorted(baseline):
    if hardware.match(symbol(expected)) and by_symbol.get(symbol(expected)) != expected:
        errors.append(f"hardware baseline changed: {expected} -> {by_symbol.get(symbol(expected), 'missing')}")

added = sorted(current - baseline)
removed = sorted(baseline - current)
allowed_removed_symbols = {"CONFIG_PACKAGE_ip-tiny"}
unexpected = [line for line in removed if symbol(line) not in allowed_removed_symbols]
for line in unexpected:
    errors.append(f"original buildinfo selection removed or changed: {line}")

explicit_symbols = set(required_y[:6]) | set(required_unset)
categories = {1: [], 2: [], 3: [], 4: [], 5: unexpected}
for line in added:
    key = symbol(line)
    if key in explicit_symbols:
        categories[1].append(line)
    elif re.search(r"PACKAGE_(iptables|ip6tables|kmod-(ipt|nf))", key):
        categories[3].append(line)
    elif key.startswith("CONFIG_PACKAGE_"):
        categories[2].append(line)
    else:
        categories[4].append(line)
for line in removed:
    if symbol(line) in allowed_removed_symbols:
        categories[2].append(f"REMOVED (replaced by ip-full): {line}")

kmod_closure = sorted(
    line for line in full
    if line.endswith("=y") and re.match(
        r"CONFIG_PACKAGE_(kmod-(ipt|nf-|ip6tables)|ip6tables)", symbol(line)
    )
)

titles = {
    1: "1. Explicit project changes",
    2: "2. PassWall dependency changes",
    3: "3. iptables/kmod automatic dependencies",
    4: "4. Feed/package integration changes",
    5: "5. Unexpected changes",
}
report = ["# Phase B defconfig audit", "", "Gate: " + ("FAIL" if errors else "PASS"), ""]
for number in range(1, 6):
    report += [f"## {titles[number]}", ""]
    report += [f"- `{line}`" for line in categories[number]] or ["- None"]
    report.append("")
report += ["## Actual selected netfilter kmod closure", ""]
report += [f"- `{line}`" for line in kmod_closure] or ["- None"]
report += ["", "## Gate errors", ""]
report += [f"- {line}" for line in errors] or ["- None"]
Path(args.report).write_text("\n".join(report) + "\n", encoding="utf-8")
if errors:
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)
