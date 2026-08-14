#!/bin/sh
# Regenerate the example audio (needs espeak-ng) and the README playback videos (needs ffmpeg).
set -e
cd "$(dirname "$0")"
python3 tts_demo.py "$@"
for name in clear decoded; do
  ffmpeg -y -loglevel error -i "$name.wav" -filter_complex \
    "[0:a]showwaves=s=800x160:mode=line:rate=25:colors=0x2f81f7,format=yuv420p[v]" \
    -map "[v]" -map 0:a -c:v libx264 -c:a aac -shortest "$name.mp4"
done
ffmpeg -y -loglevel error -i link.wav -filter_complex \
  "[0:a]pan=mono|c0=c0,asplit[a][w];[w]showwaves=s=800x160:mode=line:rate=25:colors=0xd29922,format=yuv420p[v]" \
  -map "[v]" -map "[a]" -c:v libx264 -c:a aac -shortest link.mp4
