#!/usr/bin/env python3
import argparse
import hashlib
import io
import re
import subprocess
import tarfile
from pathlib import Path


def config_map(path):
    result = {}
    for line in Path(path).read_text().splitlines():
        m = re.match(r"(?:# )?(CONFIG_[A-Za-z0-9_]+)(?:=(.*)| is not set)$", line)
        if m:
            result[m.group(1)] = m.group(2) if m.group(2) is not None else "n"
    return result


def ar_member(path, member):
    return subprocess.check_output(["ar", "p", str(path), member])


def ipk_info(path):
    control_name = next(n.decode() for n in subprocess.check_output(["ar", "t", str(path)]).splitlines() if n.startswith(b"control.tar"))
    data_name = next(n.decode() for n in subprocess.check_output(["ar", "t", str(path)]).splitlines() if n.startswith(b"data.tar"))
    with tarfile.open(fileobj=io.BytesIO(ar_member(path, control_name)), mode="r:*") as tar:
        control = tar.extractfile("./control") or tar.extractfile("control")
        fields = {}
        for line in control.read().decode().splitlines():
            if ": " in line:
                key, value = line.split(": ", 1)
                fields[key] = value
    with tarfile.open(fileobj=io.BytesIO(ar_member(path, data_name)), mode="r:*") as tar:
        names = tar.getnames()
    return fields, names


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--ipk", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    current, baseline = config_map(args.config), config_map(args.baseline)
    expected = {"CONFIG_PACKAGE_hysteria": "y", "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_Hysteria": "y"}
    for key, value in expected.items():
        if current.get(key) != value:
            raise SystemExit(f"required config missing: {key}={value}")
    changes = sorted((key, baseline.get(key, "<absent>"), current.get(key, "<absent>"))
                     for key in set(baseline) | set(current) if baseline.get(key) != current.get(key))
    kernel_changes = [row for row in changes if row[0].startswith(("CONFIG_KERNEL_", "CONFIG_TARGET_", "CONFIG_ARCH_", "CONFIG_CPU_", "CONFIG_TOOLCHAIN_", "CONFIG_GCC_")) or row[0].startswith("CONFIG_PACKAGE_kmod-") or row[0].startswith("CONFIG_PACKAGE_iptables")]
    allowed = {"CONFIG_PACKAGE_hysteria", "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_Hysteria"}
    unexpected = [row for row in changes if row[0] not in allowed]
    if kernel_changes:
        raise SystemExit("kernel-related config changed: " + repr(kernel_changes))
    if unexpected:
        raise SystemExit("unexpected config changes: " + repr(unexpected))
    fields, names = ipk_info(Path(args.ipk))
    if fields.get("Package") != "hysteria" or fields.get("Version") != "2.12.2-1":
        raise SystemExit(f"unexpected IPK identity: {fields}")
    if "./usr/bin/hysteria" not in names and "usr/bin/hysteria" not in names:
        raise SystemExit("IPK payload does not contain /usr/bin/hysteria")
    digest = hashlib.sha256(Path(args.ipk).read_bytes()).hexdigest()
    report = ["# Phase D Hysteria audit", "", "## Config", "", "- Required symbols present", "- No kernel, kmod, iptables, target, or ABI-related config changes", "", "## IPK metadata", ""]
    for key in ("Package", "Version", "Architecture", "Depends", "Installed-Size"):
        report.append(f"- {key}: {fields.get(key, '<absent>')}")
    report += [f"- SHA256: {digest}", "- Payload: /usr/bin/hysteria"]
    (out / "IPK-AUDIT.md").write_text("\n".join(report) + "\n")
    (out / "ipk-control.txt").write_text("\n".join(f"{k}: {v}" for k, v in fields.items()) + "\n")
    (out / "config-changes.txt").write_text("\n".join(f"{k}: {old} -> {new}" for k, old, new in changes) + "\n")


if __name__ == "__main__":
    main()
