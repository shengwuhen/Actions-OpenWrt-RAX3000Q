#!/usr/bin/env python3
"""Audit the final RAX3000-QY factory UBI and its extracted rootfs."""

import argparse
import hashlib
import sys
from pathlib import Path


EXPECTED_IMAGE = "immortalwrt-ipq50xx-arm-cmcc_rax3000q-squashfs-nand-factory.ubi"
EXPECTED_ABI = "5.4-qsdk-11.5.0.5-1-c257fb1f68e3634fc68fbf99b141f87d"
PARTITION_BYTES = 0x06E00000
MIN_FREE_BYTES = PARTITION_BYTES // 10

REQUIRED_PACKAGES = {
    "luci-app-passwall": "26.9.9",
    "luci-i18n-passwall-zh-cn": None,
    "iptables-mod-tproxy": None,
    "iptables-mod-iprange": None,
    "iptables-mod-conntrack-extra": None,
    "kmod-ipt-tproxy": None,
    "kmod-ipt-iprange": None,
    "kmod-ipt-conntrack-extra": None,
    "kmod-ipt-raw": None,
    "ath11k-firmware-ipq5018": None,
    "ath11k-firmware-qcn6122": None,
    "ipq-wifi-cmcc_rax3000q": None,
    "kmod-ath11k": None,
    "kmod-qca-nss-dp": None,
    "kmod-qca-nss-drv": None,
    "kmod-qca-nss-drv-pppoe": None,
    "kmod-qca-nss-drv-wifi-meshmgr": None,
    "kmod-qca-nss-ecm-standard": None,
    "kmod-qca-ssdk-nohnat": None,
    "qca-nss-fw-ipq50xx-retail": None,
    "odhcp6c": None,
    "odhcpd-ipv6only": None,
}

FORBIDDEN_PACKAGES = {
    "hysteria", "hysteria2", "xray", "xray-core", "sing-box", "singbox",
    "naiveproxy", "naive", "trojan-go",
}

REQUIRED_FILES = [
    "etc/init.d/passwall",
    "usr/lib/lua/luci/controller/passwall.lua",
    "usr/share/passwall/iptables.sh",
    "usr/lib/iptables/libxt_socket.so",
    "usr/lib/iptables/libxt_TPROXY.so",
]

REQUIRED_MODULE_BASENAMES = [
    "xt_TPROXY.ko", "xt_socket.ko", "nf_tproxy_ipv4.ko",
    "nf_socket_ipv4.ko", "xt_iprange.ko", "xt_connbytes.ko",
    "iptable_raw.ko",
]

FORBIDDEN_BINARY_BASENAMES = {
    "hysteria", "hysteria2", "xray", "xray-core", "sing-box", "singbox",
    "naive", "naiveproxy", "trojan-go",
}


def fail(errors, message):
    errors.append(message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_manifest(path):
    packages = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if " - " in raw:
            name, version = raw.split(" - ", 1)
            packages[name.strip()] = version.strip()
    return packages


def parse_status(path):
    records = []
    current = {}
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines() + [""]:
        if not line:
            if current:
                records.append(current)
                current = {}
            continue
        if line[0].isspace() or ": " not in line:
            continue
        key, value = line.split(": ", 1)
        current[key] = value
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--rootfs", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--build-commit", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--size-report", required=True, type=Path)
    parser.add_argument("--file-inventory", required=True, type=Path)
    args = parser.parse_args()

    errors = []
    evidence = []
    if args.image.name != EXPECTED_IMAGE:
        fail(errors, f"unexpected image filename: {args.image.name}")

    size = args.image.stat().st_size
    free = PARTITION_BYTES - size
    free_pct = free * 100.0 / PARTITION_BYTES
    if size >= PARTITION_BYTES:
        fail(errors, "factory UBI is not smaller than the 110 MiB partition")
    if free < MIN_FREE_BYTES:
        fail(errors, "factory UBI leaves less than the mandatory 10% safety margin")

    image_sha = sha256(args.image)
    packages = parse_manifest(args.manifest)
    for package, version in REQUIRED_PACKAGES.items():
        if package not in packages:
            fail(errors, f"required image package missing: {package}")
        elif version and packages[package] != version:
            fail(errors, f"{package} version is {packages[package]}, expected {version}")

    forbidden_present = sorted(set(packages) & FORBIDDEN_PACKAGES)
    if forbidden_present:
        fail(errors, "forbidden proxy core packages present: " + ", ".join(forbidden_present))

    kernel_version = packages.get("kernel", "")
    if kernel_version != EXPECTED_ABI:
        fail(errors, f"kernel ABI is {kernel_version or 'missing'}, expected {EXPECTED_ABI}")

    config_text = args.config.read_text(encoding="utf-8", errors="replace")
    required_config = [
        "CONFIG_TARGET_ipq50xx=y",
        "CONFIG_TARGET_ipq50xx_arm=y",
        "CONFIG_TARGET_ipq50xx_arm_DEVICE_cmcc_rax3000q=y",
        "CONFIG_ATH11K_MEM_PROFILE_256M=y",
        "CONFIG_PACKAGE_luci-app-passwall=y",
        "CONFIG_PACKAGE_luci-i18n-passwall-zh-cn=y",
        "CONFIG_PACKAGE_iptables-mod-tproxy=y",
        "CONFIG_PACKAGE_iptables-mod-iprange=y",
        "CONFIG_PACKAGE_iptables-mod-conntrack-extra=y",
        "CONFIG_PACKAGE_kmod-ipt-tproxy=y",
        "CONFIG_PACKAGE_kmod-ipt-iprange=y",
        "CONFIG_PACKAGE_kmod-ipt-conntrack-extra=y",
        "CONFIG_PACKAGE_kmod-ipt-raw=y",
        "CONFIG_PACKAGE_kmod-qca-nss-drv-pppoe=y",
        "CONFIG_PACKAGE_kmod-qca-nss-ecm-standard=y",
    ]
    config_lines = set(config_text.splitlines())
    for symbol in required_config:
        if symbol not in config_lines:
            fail(errors, f"required final config missing: {symbol}")

    inventory = []
    for rel in REQUIRED_FILES:
        path = args.rootfs / rel
        inventory.append(f"{'PRESENT' if path.is_file() else 'MISSING'} /{rel}")
        if not path.is_file():
            fail(errors, f"required rootfs file missing: /{rel}")

    all_files = [path for path in args.rootfs.rglob("*") if path.is_file()]
    by_basename = {path.name: path for path in all_files}
    for basename in REQUIRED_MODULE_BASENAMES:
        path = by_basename.get(basename)
        inventory.append(
            f"{'PRESENT' if path else 'MISSING'} "
            + ("/" + path.relative_to(args.rootfs).as_posix() if path else basename)
        )
        if not path:
            fail(errors, f"required kernel module missing from rootfs: {basename}")

    forbidden_bins = []
    executable_roots = [args.rootfs / "usr/bin", args.rootfs / "usr/sbin", args.rootfs / "bin", args.rootfs / "sbin"]
    for root in executable_roots:
        if root.exists():
            for path in root.rglob("*"):
                if path.is_file() and path.name.lower() in FORBIDDEN_BINARY_BASENAMES:
                    forbidden_bins.append("/" + path.relative_to(args.rootfs).as_posix())
    if forbidden_bins:
        fail(errors, "forbidden proxy core binaries present: " + ", ".join(sorted(forbidden_bins)))

    status_records = parse_status(args.rootfs / "usr/lib/opkg/status")
    if not status_records:
        fail(errors, "rootfs opkg status is missing or empty")
    status_by_name = {record.get("Package", ""): record for record in status_records}
    abi_mismatches = []
    for record in status_records:
        name = record.get("Package", "")
        depends = record.get("Depends", "")
        if name.startswith("kmod-") and "kernel (= " in depends and EXPECTED_ABI not in depends:
            abi_mismatches.append(f"{name}: {depends}")
    if abi_mismatches:
        fail(errors, "installed kmod ABI mismatch: " + "; ".join(abi_mismatches))
    for package in (name for name in REQUIRED_PACKAGES if name.startswith("kmod-")):
        record = status_by_name.get(package)
        if not record:
            fail(errors, f"required kmod absent from rootfs opkg status: {package}")
        elif EXPECTED_ABI not in record.get("Depends", ""):
            fail(errors, f"required kmod does not declare the expected kernel ABI: {package}")

    args.size_report.write_text(
        "\n".join([
            f"UBI file: {args.image.name}",
            f"UBI bytes: {size}",
            f"UBI MiB: {size / 1048576:.6f}",
            f"Partition bytes: {PARTITION_BYTES}",
            f"Partition MiB: {PARTITION_BYTES / 1048576:.6f}",
            f"Remaining bytes: {free}",
            f"Remaining MiB: {free / 1048576:.6f}",
            f"Remaining percent: {free_pct:.2f}%",
            "Safety gate: at least 10% free",
        ]) + "\n", encoding="utf-8")
    args.file_inventory.write_text("\n".join(inventory) + "\n", encoding="utf-8")

    gate = "PASS" if not errors else "FAIL"
    report = [
        "# Phase E factory UBI audit",
        "",
        f"Gate: **{gate}**",
        "",
        f"- Build commit: `{args.build_commit}`",
        f"- Run ID: `{args.run_id}`",
        f"- Source commit: `{args.source_commit}`",
        f"- Image: `{args.image.name}`",
        f"- SHA256: `{image_sha}`",
        f"- Kernel ABI: `{kernel_version or 'missing'}`",
        f"- Size: {size} bytes ({size / 1048576:.6f} MiB)",
        f"- Free: {free} bytes ({free / 1048576:.6f} MiB, {free_pct:.2f}%)",
        f"- PassWall 26.9.9 in manifest and rootfs: {'yes' if not any('passwall' in e.lower() for e in errors) else 'no'}",
        f"- TPROXY/socket/iprange/conntrack-extra/raw userspace and kmods: {'yes' if not any(('iptables' in e.lower() or 'kernel module' in e.lower()) for e in errors) else 'no'}",
        f"- NSS/ECM/QSDK/Wi-Fi package closure: {'preserved' if not any(p in ' '.join(errors) for p in REQUIRED_PACKAGES if p.startswith(('kmod-qca', 'qca-', 'ath11k', 'ipq-wifi'))) else 'failed'}",
        f"- Forbidden core packages/binaries: {'none' if not forbidden_present and not forbidden_bins else 'present'}",
        "",
        "## Gate errors",
        "",
    ]
    report += [f"- {error}" for error in errors] or ["- None"]
    args.report.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
