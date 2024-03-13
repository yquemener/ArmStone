#!/bin/bash
# Starts streaming videos from the ArmStone

v4l2-ctl -d /dev/video0 -c focus_auto=0
v4l2-ctl -d /dev/video0 -c focus_absolute=40

v4l2-ctl -d /dev/video0 -v width=640,height=480,pixelformat=MJPG --stream-mmap --stream-to=- | nc 192.168.1.135 8445 &


v4l2-ctl -d /dev/video2 -c focus_auto=0
v4l2-ctl -d /dev/video2 -c focus_absolute=40

v4l2-ctl -d /dev/video2 -v width=640,height=480,pixelformat=MJPG --stream-mmap --stream-to=- | nc 192.168.1.135 8444 &
