import os
from faster_whisper import WhisperModel

model = WhisperModel("base", device="cpu", compute_type="int8")

videos = ["rK6t1utoWrc.mp4", "XLMHpphSxJQ.mp4", "ruwVARuOkqA.mp4", "wkbAl3Y2DnM.mp4"]
base_dir = "references/transitions_study"

for v in videos:
    path = os.path.join(base_dir, v)
    print(f"=== TRANSCRIPT: {v} ===")
    segments, info = model.transcribe(path, beam_size=1)
    for seg in segments:
        print(f"[{seg.start:.2f}s -> {seg.end:.2f}s] {seg.text}")
    print()
