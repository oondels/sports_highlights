#!/usr/bin/env python3
import subprocess
import os
import threading
import time
import re
from pathlib import Path

# ——— CONFIG ———
BUFFER_DIR = "/tmp/recorded_videos"
SEG_TIME = 1  # 1 s segments
AFTER = 10  # record 10 s after click
DIR = Path(BUFFER_DIR)
DIR.mkdir(parents=True, exist_ok=True)

# ——— calcula o próximo número de segmento ———
pattern = re.compile(r"buffer(\d{3})\.mp4")
existing = []
for f in os.listdir(BUFFER_DIR):
    m = pattern.match(f)
    if m:
        existing.append(int(m.group(1)))
start_num = max(existing) + 1 if existing else 0

# ——— comando FFmpeg ajustado ———
ffmpeg_cmd = [
    "ffmpeg",
    "-nostdin",
    "-f",
    "v4l2",
    "-i",
    "/dev/video0",
    "-c:v",
    "libx264",
    "-preset",
    "ultrafast",
    "-force_key_frames",
    "expr:gte(t,n_forced*1)",
    "-f",
    "segment",
    "-segment_time",
    str(SEG_TIME),
    "-segment_start_number",
    str(start_num),  # <<< novo
    "-reset_timestamps",
    "1",
    os.path.join(BUFFER_DIR, "buffer%03d.mp4"),
]

proc = subprocess.Popen(
    ffmpeg_cmd,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    stdin=subprocess.DEVNULL,
)

print("Recording… press ENTER to capture 60 s + next 10 s")

segs = []


def monitor():
    while True:
        videos = [
            os.path.join(BUFFER_DIR, f)
            for f in os.listdir(BUFFER_DIR)
            if f.endswith(".mp4")
        ]
        segs.clear()
        segs.extend(videos)
        # ordena pelo timestamp de modificação
        segs.sort(key=lambda p: os.path.getmtime(p))
        if len(segs) >= 80:  # mantém no máximo 80 s (80 arquivos de 1 s)
            print(f"{len(segs)} videos em buffer, substituindo primeiro.")
            # Deleta o mais antigo
            print(f"Deletando {segs[0]}")
            os.remove(segs[0])
            segs.pop(0)

        time.sleep(1)


monitor_thread = threading.Thread(target=monitor, daemon=True)
monitor_thread.start()

try:
    while True:
        input()  # wait for ENTER
        click_ts = time.time()
        print("Button pressed! Waiting 10 s to finish post-buffer…")
        time.sleep(3)
        # time.sleep(AFTER)

        if not segs:
            print("No segments recorded.")
            proc.terminate()
            exit(0)

        # gera o arquivo de lista para concat
        list_txt = DIR / "to_concat.txt"
        with open(list_txt, "w") as f:
            print(f"Videos {segs[-10:]}")
            for seg in segs[-10:]:  # pega os últimos 10 segmentos
                if not seg.endswith(".mp4"):
                    continue

                print(f"Adding video: {seg}", flush=True)
                f.write(f"file '{seg}'\n")

        # nome do highlight
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        out = f"highlight_{timestamp}.mp4"
        # print(f"Output file: {out}", flush=True)

        # concatena sem recodificar
        subprocess.run(
            [
                "ffmpeg",
                "-nostdin",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_txt),
                "-c",
                "copy",
                out,
            ],
            check=True,
        )

        print(f"Saved {out}", flush=True)
        list_txt.unlink()

except KeyboardInterrupt:
    print("\nStopping…", flush=True)
    proc.terminate()
