#!/usr/bin/env python3
import subprocess
import time
import os
import shutil

# Pasta onde o buffer de 60s vai ficar
BUFFER_DIR = "/tmp/recorded_videos"
# Padrão dos segmentos
SEG_PATTERN = "buffer%03d.mp4"
ffmpeg_cmd = [
    "ffmpeg",
    "-f", "v4l2",
    "-i", "/dev/video0",
    "-c:v", "libx264",
    "-preset", "ultrafast",
    "-f", "segment",
    "-segment_time", "60",
    "-segment_wrap", "5",
    "-reset_timestamps", "1",
    os.path.join(BUFFER_DIR, SEG_PATTERN)
]

# Inicia FFmpeg em background
proc = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("Recording… Press ENTER to save os últimos 60s.")

try:
    while True:
        input()  # “botão” = ENTER inicialmente
        segs = [
            f for f in os.listdir(BUFFER_DIR)
            if f.startswith("buffer") and f.endswith(".mp4")
        ]
        if not segs:
            print("Ainda não gerou nenhum segmento.")
            continue

        # escolhe o mais recente
        segs.sort(key=lambda f: os.path.getmtime(os.path.join(BUFFER_DIR, f)))
        latest = segs[-1]
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        dest = f"highlight_{timestamp}.mp4"
        shutil.copy(os.path.join(BUFFER_DIR, latest), dest)
        print(f"Salvo {dest}")

except KeyboardInterrupt:
    print("\nStopping…")
    proc.terminate()

