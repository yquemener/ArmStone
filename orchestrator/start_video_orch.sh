#!/bin/bash

# Starts receiving videos on the orchestration PC

# Make sure the ports are open
# sudo ufw allow 8445
# sudo ufw allow 8444

#sudo rmmod v4l2loopback
#sudo modprobe v4l2loopback devices=2 max_buffers=2 exclusive_caps=1 card_label="Armstone Camera"


#nc -l 8445 | tee /home/yves/tmp/raw_video_file1 | ffplay -
#nc -l 8444 | tee /home/yves/tmp/raw_video_file2 | ffplay -


#nc -l 8445 | ffmpeg -f rawvideo -pix_fmt yuyv422 -s:v 640x480  -i - -f v4l2 /dev/video3 &
#nc -l 8445 | ffmpeg -f mjpeg -c:v mjpeg -i - -f v4l2 -vf format=yuv420p /dev/video3 &
#
#
#nc -l 8444 | ffmpeg -f rawvideo -pix_fmt yuyv422 -s:v 640x480  -i - -f v4l2 /dev/video4 &
#
#
#ffplay /dev/video3 &
#ffplay /dev/video4 &

sudo rmmod v4l2loopback
sudo modprobe v4l2loopback video_nr=32,33  card_label="Virtual Camera"
nc -l 8444 | ffmpeg -f mjpeg -i - -vcodec copy -f v4l2 /dev/video32 &
nc -l 8445 | ffmpeg -f mjpeg -i - -vcodec copy -f v4l2 /dev/video33 &
sleep 1
ffplay /dev/video32 &
ffplay /dev/video33 &

# Saving to disk
# ffmpeg -f v4l2 -i /dev/video32 -c copy /home/yves/tmp/saved_stream1.mkv
# ffmpeg -f v4l2 -i /dev/video33 -c copy /home/yves/tmp/saved_stream2.mkv