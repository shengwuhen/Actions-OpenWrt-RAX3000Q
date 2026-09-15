#!/usr/bin/env python3
import argparse
import hashlib
import io
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path


def ar_members(path):
    return subprocess.check_output(["ar", "t", str(path)], text=True).splitlines()


def ar_member(path, member):
    return subprocess.check_output(["ar", "p", str(path), member])


def tar_members(path, stem):
    member = next((name for name in ar_members(path) if name.startswith(stem + ".tar")), None)
    if not member:
        raise RuntimeError(f"no {stem} archive in {path}")
    data = ar_member(path, member)
    if member.endswith(".zst"):
        data = subprocess.check_output(["zstd", "-dc"], input=data)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as archive:
        return {item.name.lstrip("./"): archive.extractfile(item).read() if item.isfile() else b"" for item in archive.getmembers()}


def fields(raw):
    result = {}
    current = None
    for line in raw.decode("utf-8", "replace").splitlines():
        if line[:1].isspace() and current:
            result[current] += " " + line.strip()
        elif ":" in line:
            current, value = line.split(":", 1)
            result[current] = value.strip()
    return result


parser = argparse.ArgumentParser()
parser.add_argument("--bin", required=True)
parser.add_argument("--out", required=True)
args = parser.parse_args()
root = Path(args.bin)
out = Path(args.out)
ipk_out = out / "ipks"
ipk_out.mkdir(parents=True, exist_ok=True)
records = {}
errors = []
warnings = []

required = {
    "kernel", "iptables", "iptables-mod-tproxy", "iptables-mod-iprange",
    "iptables-mod-conntrack-extra", "kmod-ipt-tproxy", "kmod-ipt-iprange",
    "kmod-ipt-conntrack-extra", "kmod-ipt-raw", "luci-app-passwall",
    "chinadns-ng", "dns2socks", "ipt2socks", "microsocks", "tcping",
    "ip-full", "ipset", "dnsmasq-full", "coreutils", "curl",
}


def filename_package(path):
    return path.name.split("_", 1)[0]


def is_related_kmod(name):
    return re.match(r"kmod-(ipt-|nf-|ip6tables|iptunnel)", name) is not None


def is_critical_name(name):
    return name in required or is_related_kmod(name) or name.startswith("ip6tables")


unreadable = {}

for path in root.rglob("*.ipk"):
    filename_name = filename_package(path)
    try:
        members = tar_members(path, "control")
    except Exception as exc:
        message = f"control archive unreadable in {path.name}: {exc}"
        if is_critical_name(filename_name):
            errors.append(message)
            unreadable[filename_name] = path
        else:
            warnings.append(f"skipped unrelated IPK: {message}")
        continue
    control_name = next((name for name in members if name == "control" or name.endswith("/control")), None)
    if not control_name:
        message = f"control metadata missing in {path.name}"
        if is_critical_name(filename_name):
            errors.append(message)
            unreadable[filename_name] = path
        else:
            warnings.append(f"skipped unrelated IPK: {message}")
        continue
    metadata = fields(members[control_name])
    if "Package" in metadata:
        records[metadata["Package"]] = (path, metadata)

for name in sorted(required):
    if name not in records:
        if name not in unreadable:
            errors.append(f"required IPK missing: {name}")

selected = set(required)
queue = list(required)
while queue:
    name = queue.pop()
    if name not in records:
        continue
    depends = records[name][1].get("Depends", "")
    for dep in re.findall(r"(?:^|,\s*)([A-Za-z0-9_.+:-]+)", depends):
        if dep in unreadable and is_related_kmod(dep):
            errors.append(f"selected dependency control archive unreadable: {dep}")
        if dep in records and dep not in selected and (is_related_kmod(dep) or name.startswith("kmod-")):
            selected.add(dep)
            queue.append(dep)

for name in records:
    if is_related_kmod(name):
        selected.add(name)

abi_values = set()
rows = []
for name in sorted(selected):
    if name not in records:
        continue
    path, metadata = records[name]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    depends = metadata.get("Depends", "")
    if name.startswith("kmod-"):
        match = re.search(r"kernel \(= ([^)]+)\)", depends)
        if not match:
            errors.append(f"kernel ABI dependency missing from {name}")
        else:
            abi_values.add(match.group(1))
    rows.append((name, metadata.get("Version", ""), metadata.get("Architecture", ""), depends, metadata.get("Installed-Size", ""), digest, str(path)))
    shutil.copy2(path, ipk_out / path.name)

if len(abi_values) != 1:
    errors.append(f"expected exactly one kmod kernel ABI, got {sorted(abi_values)}")
if any("29c60ca79d7222d34f8490ffe7f3fcd0" in value for value in abi_values):
    errors.append("old run-34227755212 kernel ABI was mixed into Phase B")

def data_names(package):
    if package not in records:
        return set(), {}
    try:
        members = tar_members(records[package][0], "data")
    except Exception as exc:
        errors.append(f"{package} data archive unreadable: {exc}")
        return set(), {}
    return set(members), members

tproxy_names, _ = data_names("iptables-mod-tproxy")
for expected in ("usr/lib/iptables/libxt_socket.so", "usr/lib/iptables/libxt_TPROXY.so"):
    if expected not in tproxy_names:
        errors.append(f"iptables-mod-tproxy payload missing {expected}")

kmod_names, _ = data_names("kmod-ipt-tproxy")
for expected in ("xt_socket.ko", "xt_TPROXY.ko", "nf_tproxy_ipv4.ko", "nf_tproxy_ipv6.ko"):
    if not any(name.endswith("/" + expected) for name in kmod_names):
        errors.append(f"kmod-ipt-tproxy payload missing {expected}")

passwall_names, passwall_members = data_names("luci-app-passwall")
if "luci-app-passwall" in records:
    version = records["luci-app-passwall"][1].get("Version", "")
    if not version.startswith("26.9.9"):
        errors.append(f"unexpected PassWall version: {version}")
    depends = records["luci-app-passwall"][1].get("Depends", "").lower()
    for forbidden in ("iptables-mod-socket", "iptables-zz-legacy", "nftables", "hysteria", "xray", "sing-box"):
        if forbidden in depends:
            errors.append(f"forbidden PassWall control dependency: {forbidden}")
    app_name = next((name for name in passwall_names if name.endswith("usr/share/passwall/app.sh")), None)
    if not app_name:
        errors.append("PassWall package payload missing app.sh")
    else:
        app = passwall_members[app_name].decode("utf-8", "replace")
        if re.search(r'dep_list=[^\n]*iptables-mod-socket', app):
            errors.append("PassWall runtime hard dependency on iptables-mod-socket remains")
        if "iptables-mod-tproxy" not in app or "libxt_socket.so" not in app:
            errors.append("PassWall combined-package socket compatibility patch is absent")

report = [
    "# Phase B IPK audit", "", f"Gate: {'FAIL' if errors else 'PASS'}", "",
    "## Kernel ABI", "", "- " + (next(iter(abi_values)) if len(abi_values) == 1 else str(sorted(abi_values))), "",
    "## Package metadata", "",
    "| Package | Version | Architecture | Depends | Installed-Size | SHA256 | Source path |",
    "|---|---|---|---|---:|---|---|",
]
for row in rows:
    report.append("| " + " | ".join(value.replace("|", "\\|") for value in row) + " |")
report += ["", "## tproxy payload", ""]
report += [f"- `{name}`" for name in sorted(tproxy_names) if "libxt_" in name]
report += ["", "## kmod-ipt-tproxy payload", ""]
report += [f"- `{name}`" for name in sorted(kmod_names) if name.endswith(".ko")]
report += ["", "## PassWall validation", ""]
report += ["- Version 26.9.9", "- Combined iptables socket compatibility patch present", "- No forbidden hard dependency"] if not any("PassWall" in e for e in errors) else ["- Failed; see errors"]
report += ["", "## Errors", ""]
report += [f"- {error}" for error in errors] or ["- None"]
report += ["", "## Warnings", ""]
report += [f"- {warning}" for warning in warnings] or ["- None"]
(out / "IPK-AUDIT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
(out / "kernel-abi.txt").write_text("\n".join(sorted(abi_values)) + "\n", encoding="utf-8")
if errors:
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)
