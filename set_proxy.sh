#!/bin/zsh
HOST_IP=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}')
export HTTP_PROXY="http://$HOST_IP:7890"
export HTTPS_PROXY="http://$HOST_IP:7890"
export ALL_PROXY="http://$HOST_IP:7890"
echo "Proxy set to $HTTP_PROXY"
