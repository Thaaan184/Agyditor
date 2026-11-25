import subprocess, glob, os
from PIL import Image, ImageDraw

# 1. Tail of 4tx33YWabuE (23.5s -> 33s)
os.makedirs("references/text_motion_study/tail_4tx", exist_ok=True)
subprocess.run(["bin/ffmpeg.exe", "-y", "-ss", "23.5", "-t", "9.5", "-i", "references/text_motion_study/4tx33YWabuE.mp4", "-vf", "fps=2,scale=360:-1", "references/text_motion_study/tail_4tx/t_%03d.jpg"], capture_output=True)
files = sorted(glob.glob("references/text_motion_study/tail_4tx/*.jpg"))[:15]
if files:
    imgs = [Image.open(f) for f in files]
    w, h = imgs[0].size
    sheet = Image.new("RGB", (5*w, ((len(imgs)+4)//5)*h), (10,10,10))
    draw = ImageDraw.Draw(sheet)
    for i, im in enumerate(imgs):
        cx, cy = (i%5)*w, (i//5)*h
        sheet.paste(im, (cx, cy))
        draw.rectangle([cx+4, cy+4, cx+85, cy+26], fill=(0,0,0))
        draw.text((cx+8, cy+8), f"{23.5+i*0.5:.1f}s", fill=(255,200,80))
    sheet.save("references/text_motion_study/tail_4tx.jpg", quality=90)

# 2. Hires 12fps of L3HeXpHpxaY (0.0 -> 1.0s)
os.makedirs("references/text_motion_study/hires_L3", exist_ok=True)
subprocess.run(["bin/ffmpeg.exe", "-y", "-ss", "0.0", "-t", "1.0", "-i", "references/text_motion_study/L3HeXpHpxaY.mp4", "-vf", "fps=12,scale=420:-1", "references/text_motion_study/hires_L3/f_%03d.jpg"], capture_output=True)
files2 = sorted(glob.glob("references/text_motion_study/hires_L3/*.jpg"))[:12]
if files2:
    imgs = [Image.open(f) for f in files2]
    w, h = imgs[0].size
    sheet = Image.new("RGB", (6*w, 2*h), (10,10,10))
    draw = ImageDraw.Draw(sheet)
    for i, im in enumerate(imgs):
        cx, cy = (i%6)*w, (i//6)*h
        sheet.paste(im, (cx, cy))
        draw.rectangle([cx+4, cy+4, cx+75, cy+26], fill=(0,0,0))
        draw.text((cx+8, cy+8), f"f{i} {i/12:.2f}s", fill=(100,255,255))
    sheet.save("references/text_motion_study/hires_L3.jpg", quality=92)

print("EXTRAS_DONE")
