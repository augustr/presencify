#!/bin/bash

# Credits for this script goes to Jonathan Dunn
# See https://community.openhab.org/t/working-iphone-wifi-presence-locator/5985

# This script needs to be run as root user

declare -a DEVICES
#ip neigh flush ${1} # spams dmesg/syslog with "netlink: 12 bytes leftover after parsing attributes in process `ip'." messages.
arp -d ${1} # use this instead
hping3 -2 -c 10 -p 5353 -i u1 ${1} -q >/dev/null 2>&1 
DEVICES=`arp -an | awk '{print $4}'`
CHECK="${2}"
if [[ ${DEVICES[*]} =~ $CHECK ]]
then
  exit 0
else
  exit 1
fi
