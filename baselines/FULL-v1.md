# CMCC RAX3000-QY Full v1 Verified Baseline

## Identity

- Repository: `shengwuhen/Actions-OpenWrt-RAX3000Q`
- Firmware line: `Full v1`
- Branch at build time: `master`
- Firmware baseline commit: `3ffaf58fafb397573cca4a32ccf55ae54a6a070d`
- Immutable tag: `rax3000qy-full-v1.0.0`
- Release: `https://github.com/shengwuhen/Actions-OpenWrt-RAX3000Q/releases/tag/rax3000qy-full-v1.0.0`
- Device: `CMCC RAX3000-QY` (`cmcc_rax3000q`)
- SoC/platform: `IPQ5018 / AP-MP02.1`
- Target: `ipq50xx/arm`
- Package architecture: `arm_cortex-a7_neon-vfpv4`

The firmware baseline is the build commit above. The later documentation
commit that adds this file records the baseline but does not replace or move
the firmware baseline.

## Verified GitHub Actions Run

- Workflow: `Phase E factory UBI build and audit`
- Workflow path: `.github/workflows/phase-e.yml`
- Run ID: `35081830132`
- Run URL: `https://github.com/shengwuhen/Actions-OpenWrt-RAX3000Q/actions/runs/35081830132`
- Event: `workflow_dispatch`
- Attempt: `1`
- Head branch: `master`
- Head SHA: `3ffaf58fafb397573cca4a32ccf55ae54a6a070d`
- Conclusion: `success`
- Started: `2026-09-16T09:52:09Z`
- Completed: `2026-09-16T11:09:51Z`

The following release-critical steps all completed successfully:

- `Build complete factory firmware`
- `Extract and audit final factory UBI`
- `Remove extracted rootfs before artifact upload`
- `Upload complete Phase E artifact`

## Frozen Source Inputs

The values below are copied from the verified artifact's
`frozen-inputs.txt`.

| Input | Frozen value |
|---|---|
| Build definition | `3ffaf58fafb397573cca4a32ccf55ae54a6a070d` |
| ImmortalWrt source | `e1ea5628d486979252a5dd7e507f335381b3ed59` |
| packages feed | `e09f3c7d1903cfe7f523e209ab3ec778013ba309` |
| luci feed | `5829eabba50ec0afa17d2ee486bc90dc15180c34` |
| routing feed | `a9e43101bb726070cbf81b6225fc0625f4a4a5e5` |
| telephony feed | `920fbc5c0a2e4badf51bceff42e9a1e3eb693462` |
| golang feed | `17077f28edf4f18be1cb490253e76e7f14876459` |
| node feed | `01cf77b516b7cd4cef84a667415544350e4c2501` |
| FRP package overlay | `5c4151039612910a89f082967842c387d1d972e3` |
| PassWall | `92714cdb2eb613fbab195f8b6005b9b1d9843294` |
| PassWall packages | `e73ad1c77a96fdaa498807ff7bc717dc92c349ea` |

## Build Configuration

- Final config SHA256: `51e5778feb79587e67b77381eef88cef61ebe77c3c5db032c2d8fa7bbd102337`
- `CONFIG_TARGET_ipq50xx=y`
- `CONFIG_TARGET_ipq50xx_arm=y`
- `CONFIG_TARGET_ipq50xx_arm_DEVICE_cmcc_rax3000q=y`
- `CONFIG_TARGET_BOARD="ipq50xx"`
- `CONFIG_TARGET_SUBTARGET="arm"`
- `CONFIG_TARGET_ARCH_PACKAGES="arm_cortex-a7_neon-vfpv4"`
- `CONFIG_ATH11K_MEM_PROFILE_256M=y`
- Root filesystem: SquashFS inside UBI

Hashes of release-critical build definitions at the firmware baseline commit:

| Repository file | SHA256 |
|---|---|
| `.github/workflows/phase-e.yml` | `6f4b9b6bb698dde6b31a2b012c7487d812705680bfdbd03b32f116dade5b0824` |
| `scripts/phase-e-image-audit.py` | `abdfb911b525f8d833c7186de32203d8b52f8ac2cb0f9ef41c58fee3eec87b7d` |
| `diy-part2.sh` | `71edaffd3a0d496af73cfc56bf9936dc4bf85039067a763d4004ef3fcb5031b3` |
| `patches/passwall/0001-compat-iptables-legacy-packaging.patch` | `ee1e8c87b514a65d63c81f50f4b9a446e3ec12fa0d01afd9170ee5f02ee67b05` |

## Kernel ABI

- Kernel ABI: `5.4-qsdk-11.5.0.5-1-c257fb1f68e3634fc68fbf99b141f87d`
- Kernel line: Linux `5.4` QSDK `11.5.0.5`
- The Phase E audit checked every installed `kmod-*` dependency against this
  exact ABI.

## Factory Firmware

- Filename: `immortalwrt-ipq50xx-arm-cmcc_rax3000q-squashfs-nand-factory.ubi`
- Size: `26607616` bytes (`25.375000` MiB)
- SHA256: `d5ebd295931a1d0d391809bd4c07572256a606af1f788844e16200ee4fa4344f`
- Rootfs partition start: `0x00900000`
- Rootfs partition size: `0x06E00000` (`115343360` bytes, `110` MiB)
- Remaining against the partition contract: `88735744` bytes
  (`84.625000` MiB, `76.93%`)

The partition start is part of the approved RAX3000-QY large-partition device
baseline and is not encoded inside the standalone UBI file. The partition size
is also enforced by `scripts/phase-e-image-audit.py` and recorded by the
verified artifact's `image-size-report.txt`.

The SHA256 above was independently recalculated from the archived UBI and
matches both `SHA256SUMS` and `PHASE-E-AUDIT.md` from Run `35081830132`.

## UBI Layout

The archived factory UBI was inspected directly with `ubi_reader`:

- Minimum I/O size: `2048` bytes
- Physical eraseblock size: `131072` bytes
- Logical eraseblock size: `126976` bytes
- Total PEB count: `203`
- Data PEB count: `201`
- Layout PEB count: `2`
- Image sequence number: `1726611392`
- Data PEB range: `2-202`

| Volume ID | Name | Type | Observed blocks | Reserved PEBs | Flags |
|---:|---|---|---:|---:|---|
| 0 | `kernel` | dynamic | 28 | 28 | none |
| 1 | `rootfs` | dynamic | 173 | 173 | none |
| 2 | `rootfs_data` | dynamic | 0 | 9 | `autoresize` |

## Package / PassWall State

- Package manifest entries: `321`
- PassWall: `luci-app-passwall 26.9.9`
- Chinese translation: `luci-i18n-passwall-zh-cn 26.9.9`
- `iptables-mod-tproxy 1.8.7-2`
- `kmod-ipt-tproxy 5.4-qsdk-11.5.0.5-1`
- QSDK/NSS/ECM/Wi-Fi package closure: preserved
- Optional large proxy cores in the audited image: none

The extracted rootfs audit confirmed the PassWall init script, LuCI
controller, PassWall iptables script, `libxt_socket.so`, `libxt_TPROXY.so`,
the required TPROXY/socket modules, iprange, connbytes, and raw-table support.

## Audit Result

- Phase E image gate: `PASS`
- Config audit gate: `PASS`
- Gate errors: none
- Factory UBI extraction: successful
- Rootfs SquashFS extraction exit code: `0`
- Extracted rootfs: 2911 files, 312 directories, 283 symlinks, 1 device
- Image fits the 110 MiB partition with more than the mandatory 10% margin
- PassWall 26.9.9 and transparent-proxy userspace/kernel capabilities: present
- NSS/ECM/QSDK/Wi-Fi package closure: preserved
- Forbidden optional proxy core packages/binaries: none

## Artifact Integrity

- GitHub Actions artifact name: `phase-e-factory-ubi-audit-35081830132`
- Artifact ID: `10443326456`
- Original GitHub artifact ZIP size: `25418630` bytes
- Original GitHub artifact ZIP SHA256:
  `523c955eeef360653f1193468a7dc12b7b22741f8f65f043ba38df8e1221e8cb`
- Original Actions retention expiry: `2026-12-15T09:52:11Z`

The artifact ZIP hash and factory UBI hash identify different objects and must
not be interchanged.

Hashes of the principal evidence files inside the original artifact:

| File | Bytes | SHA256 |
|---|---:|---|
| `SHA256SUMS` | 130 | `b5bcbe06803d69abef45ee2ce99c1478ca10729e9616441137ea4e87199bbeb7` |
| `package.manifest` | 10695 | `776cf21549e92a394463dcae3d1c35c7faf154be9c1b8b587bd27dc261a2fc9f` |
| `config.final` | 285572 | `51e5778feb79587e67b77381eef88cef61ebe77c3c5db032c2d8fa7bbd102337` |
| `frozen-inputs.txt` | 641 | `5819a5e0bbdee203d33a7c9d220b0c4eeb0b0ffa3b6e043d9352b4ac0b246340` |
| `kernel-abi.txt` | 53 | `58b8a7c761b0e5a75b278b331c8d042ef717f22c62fb84bcc1b1fb997accf3bc` |
| `PHASE-E-AUDIT.md` | 723 | `9155d090a86e606849fd85f695e5903da55e85a7ca2e65a460f789b1b7286e94` |
| `CONFIG-AUDIT.md` | 3777 | `df720ae9043d76aefdc93e11d723fc228c0f1837fccab1ec553777e3a30d556c` |
| `image-size-report.txt` | 274 | `997d44f92fd3014d502ea8458c48ad2cefd75ed9d6b24e22eeadda4e088a5ff8` |
| `rootfs-critical-files.txt` | 513 | `31df176dcf9d7abf59576c34e8daec79411f40fee8425728cacae9f3d7abeddb` |
| `disk-usage.txt` | 440 | `96558a4118f7f2d9d6edcc1921b7e979029d27c74f948e8b23bbe7481803179f` |
| `unsquashfs.exit-code.txt` | 2 | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |
| `unsquashfs.stdout.log` | 433 | `370c565f014be942833c76523d58d87c6917efb93108389f4b950e2c2cbeca4b` |
| `unsquashfs.stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| Factory UBI | 26607616 | `d5ebd295931a1d0d391809bd4c07572256a606af1f788844e16200ee4fa4344f` |

The `unsquashfs.exit-code.txt` digest above is for its exact two-byte content
(`0` followed by a newline).

## Reproduction Notes

The frozen commit and input revisions describe the source-level build. The
archived, hash-verified artifact is the authoritative Full v1 binary because
the GitHub-hosted runner image, apt repositories, moving action major tags,
and externally hosted downloads are not all immutable byte-for-byte inputs.

A future rebuild must not be called Full v1 merely because it uses the same
source commit. It is a reproduction candidate until its own output is audited
and compared with this record. Rebuilding is not required to validate the
archived Full v1 image.

## Long-term Retention

The GitHub Release attached to `rax3000qy-full-v1.0.0` retains:

- the original, unmodified GitHub Actions artifact ZIP;
- the factory UBI;
- `SHA256SUMS`;
- `frozen-inputs.txt`;
- `package.manifest`;
- `config.final` and its hash record;
- the Phase E and configuration audit reports;
- image-size, rootfs-critical-file, disk-usage, and unsquashfs evidence;
- a copy of this baseline record.

The original ZIP is preserved as downloaded. An extracted directory must not
be recompressed and represented as the original Actions artifact.

## Immutable Baseline Statement

CMCC RAX3000-QY Full v1.0.0 is jointly identified by:

1. annotated Git tag `rax3000qy-full-v1.0.0`;
2. firmware commit `3ffaf58fafb397573cca4a32ccf55ae54a6a070d`;
3. verified GitHub Actions Run `35081830132`;
4. original artifact `phase-e-factory-ubi-audit-35081830132` with SHA256
   `523c955eeef360653f1193468a7dc12b7b22741f8f65f043ba38df8e1221e8cb`;
5. factory UBI with SHA256
   `d5ebd295931a1d0d391809bd4c07572256a606af1f788844e16200ee4fa4344f`;
6. the hashes and archived evidence recorded in this document.

Later changes to `master`, later documentation commits, Lean firmware work,
or future rebuilds cannot redefine, replace, or move this Full v1 baseline.
