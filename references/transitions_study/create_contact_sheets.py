import os
import glob
from PIL import Image

base_dir = "references/transitions_study"
videos = ["rK6t1utoWrc", "XLMHpphSxJQ", "ruwVARuOkqA", "wkbAl3Y2DnM"]

for v_name in videos:
    frames_dir = os.path.join(base_dir, f"frames_{v_name}")
    frames = sorted(glob.glob(os.path.join(frames_dir, "*.jpg")))
    if not frames:
        continue
    
    # Take up to 16 or 24 evenly spaced frames
    step = max(1, len(frames) // 16)
    selected = frames[::step][:16]
    
    # Load images
    imgs = [Image.open(f) for f in selected]
    w, h = imgs[0].size
    
    # 4 columns, 4 rows
    cols = 4
    rows = (len(imgs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w, rows * h))
    
    for idx, img in enumerate(imgs):
        c = idx % cols
        r = idx // cols
        sheet.paste(img, (c * w, r * h))
    
    out_sheet = os.path.join(base_dir, f"sheet_{v_name}.jpg")
    sheet.save(out_sheet, quality=85)
    print(f"Saved contact sheet: {out_sheet} ({cols}x{rows}, {len(imgs)} frames)")
