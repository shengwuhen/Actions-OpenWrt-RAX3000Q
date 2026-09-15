# Phase A build baseline

This file records inputs selected during Phase A. It does not certify a build.

## Firmware baseline

- Original successful release: `RAX3000Q-2026.09.08-2133`
- Original GitHub Actions run: `34227755212`
- Original Actions repository commit: `6c52cdbf4cc331986ab3165ce2cbf262b45518fe`
- ImmortalWrt repository: `https://github.com/kkstone/immortalwrt-ipq50xx`
- Branch used for discovery: `openwrt-21.02`
- Frozen source commit: `e1ea5628d486979252a5dd7e507f335381b3ed59`
- Version buildinfo: `r20123-e1ea5628d4`

## Feeds recovered from the original artifact

- packages: `e09f3c7d1903cfe7f523e209ab3ec778013ba309`
- luci: `5829eabba50ec0afa17d2ee486bc90dc15180c34`
- routing: `a9e43101bb726070cbf81b6225fc0625f4a4a5e5`
- telephony: `920fbc5c0a2e4badf51bceff42e9a1e3eb693462`

These are deliberately retained at the revisions recorded in the original
artifact's `feeds.buildinfo`.

## Selected external package inputs

- kenzok8/golang, branch `1.25`: `17077f28edf4f18be1cb490253e76e7f14876459`
- sbwml/feeds_packages_lang_node-prebuilt, branch `packages-24.10`: `01cf77b516b7cd4cef84a667415544350e4c2501`
- immortalwrt/packages `net/natmap`: `7cb0c183a9e98f71366c462f9a38c13246003764`
- immortalwrt/packages `net/ddns-go`: `03d8b9d71b5e27972e4111ebe39898d093544c92`
- immortalwrt/packages `net/frp`: `5c4151039612910a89f082967842c387d1d972e3`

The five revisions above are explicit selections for the next build baseline.
They are not claimed to be uniquely recoverable inputs from run `34227755212`.

## Deferred inputs

- PassWall is deferred to Phase C. The local reference checkout is release
  `26.9.9-1` at `92714cdb2eb613fbab195f8b6005b9b1d9843294`.
- Hysteria is deferred to Phase D and is not a condition for Phase B. The local
  package feed reference is `e73ad1c77a96fdaa498807ff7bc717dc92c349ea`;
  its Hysteria recipe declares version `2.12.2` and source SHA256
  `8db04a112e73685a1e5916d5d4d3df3ed897dbabc3e639fda4880b7ca9a7d18e`.

## Intentionally unresolved or floating inputs

- GitHub Actions referenced with moving tags such as `@main`.
- The `ubuntu-22.04` runner image and packages installed through apt.
- `klever1988/cachewrtbuild@main` and its cache contents/key behavior.
- The Dropbox-hosted TurboACC archive has no locally recorded content hash.
- The two Dropbox download URLs for kernel/backports are mutable locations;
  the OpenWrt download stage is expected to enforce recipe hashes, but this
  must be verified before a release build.
- The exact historical commits for the five selected external package inputs
  cannot be proven from the original artifact and therefore represent an
  explicit new-baseline choice.

## Phase A package selection

The firmware configuration directly selects these user-space packages:

- `CONFIG_PACKAGE_iptables-mod-tproxy=y`
- `CONFIG_PACKAGE_iptables-mod-iprange=y`
- `CONFIG_PACKAGE_iptables-mod-conntrack-extra=y`

Kernel packages are not selected manually. The configuration script runs
`make defconfig` during a later build phase and requires the dependency solver
to produce all of the following:

- `CONFIG_PACKAGE_kmod-ipt-tproxy=y`
- `CONFIG_PACKAGE_kmod-ipt-iprange=y`
- `CONFIG_PACKAGE_kmod-ipt-conntrack-extra=y`
- `CONFIG_PACKAGE_kmod-ipt-raw=y`

PassWall and Hysteria configuration symbols remain deferred until their package
definitions are integrated in Phase C and Phase D respectively.

## Planned later-phase package selections

Phase C will integrate the PassWall 26.9.9 package definition before enabling:

- `CONFIG_PACKAGE_luci-app-passwall=y`
- `CONFIG_PACKAGE_luci-app-passwall_Iptables_Transparent_Proxy=y`
- `# CONFIG_PACKAGE_luci-app-passwall_Nftables_Transparent_Proxy is not set`

Its package dependencies will be resolved and audited in Phase C. In particular,
the 21.02 tree has no independent `iptables-mod-socket` package, so that symbol
must not be added to this baseline.

Phase D will integrate the Hysteria 2.12.2 recipe before enabling:

- `CONFIG_PACKAGE_hysteria=y`
- `CONFIG_PACKAGE_luci-app-passwall_INCLUDE_Hysteria=y`

These deferred symbols are the planned final selections, not Phase A changes to
the current `.config`. Hysteria remains independent of the Phase B
kernel/iptables acceptance criteria.
