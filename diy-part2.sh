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

packages=(
	iptables-mod-tproxy
	iptables-mod-iprange
	iptables-mod-conntrack-extra
)

for package in "${packages[@]}"; do
	symbol="CONFIG_PACKAGE_${package}"
	sed -i -e "/^${symbol}=/d" -e "/^# ${symbol} is not set$/d" .config
	printf '%s=m\n' "$symbol" >> .config
done

# Resolve package dependencies before the expensive download and build steps.
make defconfig

for package in "${packages[@]}"; do
	grep -qx "CONFIG_PACKAGE_${package}=m" .config
done

for package in ipt-tproxy ipt-iprange ipt-conntrack-extra; do
	grep -Eq "^CONFIG_PACKAGE_kmod-${package}=(m|y)$" .config
done
