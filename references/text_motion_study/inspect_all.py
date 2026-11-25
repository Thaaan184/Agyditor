import os
import json
import glob
import subprocess
from PIL import Image, ImageDraw
from faster_whisper import WhisperModel

base_dir = "references/text_motion_study"

print("=== METADATA ===")
with open(os.path.join(base_dir, "meta.jsonl"), "r", encoding="utf-8-sig") as f:
    for line in f:
        if not line.strip():
            continue
        d = json.loads(line)
        vid = d.get("id")
        print(f"\nID: {vid}")
        print(f"Title: {d.get('title')}")
        print(f"Uploader: {d.get('uploader')} ({d.get('channel_url')})")
        print(f"Duration: {d.get('duration')}s | Resolution: {d.get('width')}x{d.get('height')} | FPS: {d.get('fps')}")
        print("Description:")
        print((d.get("description") or "").strip())

model = WhisperModel("base", device="cpu", compute_type="int8")

videos = ["ZcmcHeWWAuI", "hRjZf_sg9GQ", "BU64zlrW1Ik", "L3HeXpHpxaY", "4tx33YWabuE", "NyOTPC5aQog"]

for vid in videos:
    mp4_path = os.path.join(base_dir, f"{vid}.mp4")
    wav_path = os.path.join(base_dir, f"{vid}.wav")
    if not os.path.exists(mp4_path):
        continue

    # Probe exact stream info
    probe = subprocess.run(
        ["bin/ffprobe.exe", "-v", "quiet", "-print_format", "json", "-show_streams", mp4_path],
        capture_output=True, text=True
    )
    pdata = json.loads(probe.stdout)
    vs = next((s for s in pdata["streams"] if s["codec_type"] == "video"), {})
    print(f"\n=== STREAM & TRANSCRIPT: {vid} ({vs.get('width')}x{vs.get('height')} @ {vs.get('r_frame_rate')} fps) ===")

    # Extract wav
    subprocess.run(
        ["bin/ffmpeg.exe", "-y", "-i", mp4_path, "-vn", "-ar", "16000", "-ac", "1", wav_path],
        capture_output=True
    )

    segments, _ = model.transcribe(wav_path, beam_size=1, word_timestamps=True)
    for seg in segments:
        print(f"  [{seg.start:.2f}s -> {seg.end:.2f}s] {seg.text.strip()}")

    # Extract sample frames across full duration (aim for ~16-20 frames per video for contact sheet)
    frames_dir = os.path.join(base_dir, f"frames_{vid}")
    os.makedirs(frames_dir, exist_ok=True)
    for old in glob.glob(os.path.join(frames_dir, "*.jpg")):
        os.remove(old)

    # Probe duration
    dur_res = subprocess.run(
        ["bin/ffprobe.exe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", mp4_path],
        capture_output=True, text=True
    )
    dur = float(dur_res.stdout.strip() or 10.0)
    target_fps = min(3.0, max(0.8, 16.0 / max(1.0, dur)))

    subprocess.run([
        "bin/ffmpeg.exe", "-y", "-i", mp4_path,
        "-vf", f"fps={target_fps:.3f},scale=360:-1",
        os.path.join(frames_dir, "f_%03d.jpg")
    ], capture_output=True)

    f_list = sorted(glob.glob(os.path.join(frames_dir, "*.jpg")))[:20]
    if f_list:
        imgs = [Image.open(p) for p in f_list]
        w, h = imgs[0].size
        cols = 5
        rows = (len(imgs) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * w, rows * h), (15, 15, 15))
        draw = ImageDraw.Draw(sheet)
        for idx, img in enumerate(imgs):
            cx = (idx % cols) * w
            cy = (idx // cols) * h
            sheet.paste(img, (cx, cy))
            ts = idx / target_fps
            draw.rectangle([cx + 4, cy + 4, cx + 92, cy + 28], fill=(0, 0, 0))
            draw.text((cx + 8, cy + 8), f"#{idx+1} {ts:.2f}s", fill=(255, 220, 60))
        sheet_path = os.path.join(base_dir, f"sheet_{vid}.jpg")
        sheet.save(sheet_path, quality=90)
        print(f"Saved contact sheet: {sheet_path} ({len(imgs)} frames)")
