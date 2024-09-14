#!/bin/bash
sudo apt-get install bluez bluez-tools bluetooth
hciattach /dev/ttyPS1 -t 10 any 115200 noflow nosleep
