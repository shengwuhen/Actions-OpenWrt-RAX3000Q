#!/bin/bash
#
# Copyright (c) 2019-2020 P3TERX <https://p3terx.com>
#
# This is free software, licensed under the MIT License.
# See /LICENSE for more information.
#
# https://github.com/P3TERX/Actions-OpenWrt
# File name: diy-part2.sh
# Description: OpenWrt DIY script part 2 (After Update feeds)
#

set -euo pipefail

enabled_packages=(
	iptables-mod-tproxy
	iptables-mod-iprange
	iptables-mod-conntrack-extra
	luci-app-passwall
	luci-app-passwall_Iptables_Transparent_Proxy
)

disabled_packages=(
	luci-app-passwall_Nftables_Transparent_Proxy
	luci-app-passwall_INCLUDE_Geoview
	luci-app-passwall_INCLUDE_Haproxy
	luci-app-passwall_INCLUDE_Hysteria
	luci-app-passwall_INCLUDE_NaiveProxy
	luci-app-passwall_INCLUDE_Shadowsocks_Rust_Client
	luci-app-passwall_INCLUDE_Shadowsocks_Rust_Server
	luci-app-passwall_INCLUDE_ShadowsocksR_Libev_Client
	luci-app-passwall_INCLUDE_ShadowsocksR_Libev_Server
	luci-app-passwall_INCLUDE_Shadow_TLS
	luci-app-passwall_INCLUDE_Simple_Obfs
	luci-app-passwall_INCLUDE_SingBox
	luci-app-passwall_INCLUDE_V2ray_Geodata
	luci-app-passwall_INCLUDE_V2ray_Plugin
	luci-app-passwall_INCLUDE_Xray
	luci-app-passwall_INCLUDE_Xray_Plugin
)

for package in "${enabled_packages[@]}"; do
	symbol="CONFIG_PACKAGE_${package}"
	sed -i -e "/^${symbol}=/d" -e "/^# ${symbol} is not set$/d" .config
	printf '%s=y\n' "$symbol" >> .config
done

for package in "${disabled_packages[@]}"; do
	symbol="CONFIG_PACKAGE_${package}"
	sed -i -e "/^${symbol}=/d" -e "/^# ${symbol} is not set$/d" .config
	printf '# %s is not set\n' "$symbol" >> .config
done

# Resolve package dependencies before the expensive download and build steps.
make defconfig

for package in "${enabled_packages[@]}"; do
	grep -qx "CONFIG_PACKAGE_${package}=y" .config
done

for package in "${disabled_packages[@]}"; do
	grep -qx "# CONFIG_PACKAGE_${package} is not set" .config
done

for package in ipt-tproxy ipt-iprange ipt-conntrack-extra ipt-raw; do
	grep -qx "CONFIG_PACKAGE_kmod-${package}=y" .config
done

passwall_dependencies=(
	coreutils
	coreutils-base64
	coreutils-nohup
	coreutils-timeout
	curl
	chinadns-ng
	dns2socks
	dnsmasq-full
	ip-full
	libuci-lua
	lua
	luci-compat
	luci-lib-jsonc
	microsocks
	resolveip
	tcping
	lyaml
	ipset
	ipt2socks
	iptables
	kmod-ipt-nat
)

for package in "${passwall_dependencies[@]}"; do
	grep -qx "CONFIG_PACKAGE_${package}=y" .config
done

if grep -Eq '^CONFIG_PACKAGE_(iptables-mod-socket|iptables-zz-legacy)=y$' .config; then
	echo "obsolete PassWall iptables package symbol selected" >&2
	exit 1
fi

for package in hysteria naiveproxy shadowsocks-rust-sslocal shadowsocks-rust-ssserver \
	shadowsocksr-libev-ssr-local shadowsocksr-libev-ssr-redir shadow-tls \
	simple-obfs-client sing-box v2ray-plugin xray-core xray-plugin; do
	if grep -qx "CONFIG_PACKAGE_${package}=y" .config; then
		echo "unexpected PassWall proxy core selected: ${package}" >&2
		exit 1
	fi
done
