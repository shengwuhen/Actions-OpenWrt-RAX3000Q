# Phase C: PassWall 26.9.9 compatibility

This phase integrates PassWall only. It does not build firmware or enter any
other project phase.

## Fixed inputs

- `openwrt-passwall` commit: `92714cdb2eb613fbab195f8b6005b9b1d9843294`
  (`luci-app-passwall` 26.9.9-1)
- `openwrt-passwall-packages` commit:
  `e73ad1c77a96fdaa498807ff7bc717dc92c349ea`
- ImmortalWrt commit: `e1ea5628d486979252a5dd7e507f335381b3ed59`
- packages feed: `e09f3c7d1903cfe7f523e209ab3ec778013ba309`
- luci feed: `5829eabba50ec0afa17d2ee486bc90dc15180c34`

The workflow removes the old `luci-app-passwall` link installed from the pinned
luci feed, clones both PassWall repositories at their exact commits, verifies
each checked-out HEAD, and applies the compatibility patch only after
`git apply --check` succeeds. The packages repository uses sparse checkout for
only `chinadns-ng`, `dns2socks`, `ipt2socks`, `microsocks`, and `tcping`, so
unrelated proxy core recipes do not enter the build tree.

## Compatibility decisions

The 21.02 `iptables-mod-tproxy` recipe includes the `socket` match and `TPROXY`
target. Its package payload contains both `/usr/lib/iptables/libxt_socket.so`
and `/usr/lib/iptables/libxt_TPROXY.so`; `kmod-ipt-tproxy` likewise carries the
matching kernel modules. Therefore the PassWall selection of the nonexistent
split package `iptables-mod-socket` is removed.

PassWall also checks the split socket package at runtime. The patch accepts
socket capability only when `libxt_socket.so` is non-empty and either the
independent socket package record or the combined `iptables-mod-tproxy` package
record is present. No package, `PROVIDES`, binary, ABI, or kernel rule is
fabricated.

The 21.02 `iptables` package directly installs `xtables-legacy-multi` and the
`iptables`, `iptables-restore`, and `iptables-save` entry points. It has no
`iptables-zz-legacy` package. The invalid selection is removed; no replacement
package is created. PassWall already uses `iptables-legacy` when available and
falls back to `iptables`.

## Direct hard dependencies

The fixed PassWall Makefile has unconditional dependencies on:

- From the fixed packages feed: `coreutils`, `coreutils-base64`,
  `coreutils-nohup`, `coreutils-timeout`, `curl`, and `lyaml`.
- From the fixed luci feed: `luci-compat` and `luci-lib-jsonc`.
- From the ImmortalWrt base tree: `dnsmasq-full`, `ip-full`, `libuci-lua`,
  `lua`, and `resolveip`.
- From the fixed PassWall packages repository: `chinadns-ng`, `dns2socks`,
  `microsocks`, and `tcping`.

The iptables transparent proxy option additionally selects `ipset`,
`ipt2socks`, `iptables`, `iptables-mod-conntrack-extra`,
`iptables-mod-iprange`, `iptables-mod-tproxy`, and `kmod-ipt-nat`.
`ipt2socks` comes from the fixed PassWall packages repository; the others come
from the ImmortalWrt base tree.

The original firmware manifest already contains `dnsmasq-full`, `iptables`,
`kmod-ipt-nat`, `lua`, `luci-compat`, and `luci-lib-jsonc`. All remaining valid
hard dependencies above have real definitions in the fixed source inputs and
are selected through PassWall's dependency metadata.

`iptables-mod-socket` and `iptables-zz-legacy` are absent in this 21.02 tree and
are handled by the patch. The nftables path and every optional PassWall
component are explicitly disabled. This includes Hysteria, Xray, Sing-Box,
NaiveProxy, Shadowsocks variants, Shadow-TLS, Simple-Obfs, V2ray data/plugins,
HAProxy, and Geoview. No proxy core is introduced in Phase C.

## Patch retirement condition

Stop if the PassWall patch fails its exact context check. Re-audit rather than
forward-porting it automatically. Also retire and reassess the patch if the
target iptables packaging gains independent `iptables-mod-socket` or
`iptables-zz-legacy` packages.
