import os
import subprocess

# In rK6t1utoWrc (7s long), extract frames from 0 to 4s at 10 fps to see exact transition
cmd = [
    "bin/ffmpeg.exe", "-y",
    "-ss", "0", "-t", "4",
    "-i", "references/transitions_study/rK6t1utoWrc.mp4",
    "-vf", "fps=10,scale=360:-1",
    "references/transitions_study/rK6_f_%03d.jpg"
]
subprocess.run(cmd)

# In ruwVARuOkqA (23s long), extract frames from 0 to 6s at 5 fps
cmd2 = [
    "bin/ffmpeg.exe", "-y",
    "-ss", "0", "-t", "6",
    "-i", "references/transitions_study/ruwVARuOkqA.mp4",
    "-vf", "fps=5,scale=360:-1",
    "references/transitions_study/ruw_f_%03d.jpg"
]
subprocess.run(cmd2)

print("Extracted detailed frames.")
