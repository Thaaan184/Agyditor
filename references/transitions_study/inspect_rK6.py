import cv2
import numpy as np

# Let's inspect what colors/shapes are in rK6 frames 24-34
for i in range(24, 35):
    fn = f"references/transitions_study/rK6_f_{i:03d}.jpg"
    img = cv2.imread(fn)
    # Check left vs right half or top vs bottom to see direction of reveal
    h, w, _ = img.shape
    left = np.mean(img[:, :w//2])
    right = np.mean(img[:, w//2:])
    top = np.mean(img[:h//2, :])
    bottom = np.mean(img[h//2:, :])
    print(f"rK6 frame {i}: left_brightness={left:.1f}, right_brightness={right:.1f}, top={top:.1f}, bottom={bottom:.1f}")
