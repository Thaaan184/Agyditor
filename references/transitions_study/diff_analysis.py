import cv2
import numpy as np
import glob
import os

def analyze_frames(title, pattern):
    print(f"=== ANALYZING: {title} ===")
    files = sorted(glob.glob(pattern))
    prev_gray = None
    cuts = []
    for idx, f in enumerate(files):
        img = cv2.imread(f)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if prev_gray is not None:
            diff = cv2.absdiff(gray, prev_gray)
            mean_diff = np.mean(diff)
            if mean_diff > 30:
                cuts.append((idx, f, mean_diff))
        prev_gray = gray
    print(f"Total frames: {len(files)}, Significant frame jumps/transitions: {len(cuts)}")
    for c in cuts[:10]:
        print(f"  Frame {c[0]} ({os.path.basename(c[1])}): diff = {c[2]:.2f}")

analyze_frames("rK6t1utoWrc (After Effects Mask Reveal)", "references/transitions_study/rK6_f_*.jpg")
analyze_frames("ruwVARuOkqA (Capcut Masking)", "references/transitions_study/ruw_f_*.jpg")
analyze_frames("XLMHpphSxJQ (Mask Transition 3-layer)", "references/transitions_study/frames_XLMHpphSxJQ/*.jpg")
analyze_frames("wkbAl3Y2DnM (Cutout Frame Hold)", "references/transitions_study/frames_wkbAl3Y2DnM/*.jpg")
