import os
import glob
import json
import subprocess

videos = [
    "rK6t1utoWrc.mp4",
    "XLMHpphSxJQ.mp4",
    "ruwVARuOkqA.mp4",
    "wkbAl3Y2DnM.mp4"
]

base_dir = "references/transitions_study"

for v in videos:
    v_path = os.path.join(base_dir, v)
    if not os.path.exists(v_path):
        print(f"File not found: {v_path}")
        continue
    
    cmd = [
        "bin/ffprobe.exe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        v_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    try:
        data = json.loads(res.stdout)
        v_stream = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
        a_stream = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
        
        duration = float(data["format"].get("duration", 0))
        width = v_stream.get("width") if v_stream else None
        height = v_stream.get("height") if v_stream else None
        r_fps = v_stream.get("r_frame_rate") if v_stream else None
        
        print(f"=== {v} ===")
        print(f"Size: {width}x{height} | FPS: {r_fps} | Duration: {duration:.2f}s")
        
        # Make a frames subfolder
        v_name = os.path.splitext(v)[0]
        out_frames_dir = os.path.join(base_dir, f"frames_{v_name}")
        os.makedirs(out_frames_dir, exist_ok=True)
        
        # Extract a contact sheet / sample frames every 0.5s or 1s to inspect visual progression
        # We can extract fps=2 or fps=4 to see transition details clearly
        cmd_extract = [
            "bin/ffmpeg.exe",
            "-y",
            "-i", v_path,
            "-vf", "fps=2,scale=360:-1",
            os.path.join(out_frames_dir, "frame_%03d.jpg")
        ]
        subprocess.run(cmd_extract, capture_output=True)
        extracted = len(glob.glob(os.path.join(out_frames_dir, "*.jpg")))
        print(f"Extracted {extracted} sample frames to {out_frames_dir}")
    except Exception as e:
        print(f"Error processing {v}: {e}")
