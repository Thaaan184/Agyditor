import os
import glob
from PIL import Image

def make_montage(pattern, out_path, max_frames=20, cols=5):
    frames = sorted(glob.glob(pattern))[:max_frames]
    if not frames:
        return
    imgs = [Image.open(f) for f in frames]
    w, h = imgs[0].size
    rows = (len(imgs) + cols - 1) // cols
    montage = Image.new("RGB", (cols * w, rows * h))
    for i, img in enumerate(imgs):
        montage.paste(img, ((i % cols) * w, (i // cols) * h))
    montage.save(out_path)
    print(f"Created montage {out_path}")

make_montage("references/transitions_study/rK6_f_*.jpg", "references/transitions_study/montage_rK6.jpg", 20, 5)
make_montage("references/transitions_study/ruw_f_*.jpg", "references/transitions_study/montage_ruw.jpg", 20, 5)
