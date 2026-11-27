"""Comprehensive 14-Video Editorial Class-Up Study Runner.

Downloads smart-resolution local copies + subtitles onto Drive D:, measures
shot pacing (scene cuts & CV), acoustic profiles (LUFS/LRA/5-band FFT/dynamics),
color grading vectors (shadow lift, highlight roll-off, RGB/LAB shifts, saturation),
and generates contact sheets for visual inspection via read_file.
"""
from __future__ import annotations

import concurrent.futures
import json
import pathlib
import re
import subprocess
import sys
import tempfile

import cv2
import librosa
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
STUDY = ROOT / "references" / "editorial_classup_study"
MEDIA = STUDY / "media"
SUBS = STUDY / "subs"
SHEETS = STUDY / "sheets"
for d in (MEDIA, SUBS, SHEETS):
    d.mkdir(parents=True, exist_ok=True)

YTDLP = str(ROOT / "bin" / "yt-dlp.exe")
FFMPEG = str(ROOT / "bin" / "ffmpeg.exe")
FFPROBE = str(ROOT / "bin" / "ffprobe.exe")

META_PATH = STUDY / "metadata_all14.json"


def clean_vtt_to_text(vtt_path: pathlib.Path) -> str:
    raw = vtt_path.read_text(encoding="utf-8", errors="ignore")
    lines = []
    seen = set()
    for ln in raw.splitlines():
        s = ln.strip()
        if not s or s.startswith("WEBVTT") or s.startswith("Kind:") or s.startswith("Language:") or "-->" in s:
            continue
        s = re.sub(r"<[^>]+>", "", s)
        s = re.sub(r"\s+", " ", s).strip()
        if s and (not lines or lines[-1] != s):
            if s not in seen or len(s) > 40:
                lines.append(s)
                seen.add(s)
    # Deduplicate overlapping rolling caption fragments
    out = []
    for ln in lines:
        if out and ln.startswith(out[-1]):
            out[-1] = ln
        elif out and out[-1].endswith(ln):
            continue
        else:
            out.append(ln)
    return "\n".join(out)


def download_one(item: dict) -> dict:
    cat = item["category"]
    vid = item["id"]
    url = item["url"]
    dur = int(item.get("duration_s") or 0)
    mp4_path = MEDIA / f"{cat}__{vid}.mp4"

    # 1. Fetch YouTube subtitles (manual or auto English/Indonesian)
    sub_tpl = str(SUBS / f"{cat}__{vid}.%(ext)s")
    subprocess.run(
        [
            YTDLP, "--skip-download", "--no-warnings",
            "--write-sub", "--write-auto-sub",
            "--sub-langs", "en,en-orig,id,id-orig",
            "--sub-format", "vtt",
            "-o", sub_tpl, url,
        ],
        capture_output=True, text=True, check=False,
    )

    # 2. Download video cleanly capped so Drive D stays fast & lightweight
    if not mp4_path.exists() or mp4_path.stat().st_size < 10_000:
        if dur <= 60:
            fmt = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best"
        else:
            fmt = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]/best"
        p = subprocess.run(
            [
                YTDLP, "--no-warnings", "--ffmpeg-location", str(ROOT / "bin"),
                "-f", fmt, "--merge-output-format", "mp4",
                "-o", str(mp4_path), url,
            ],
            capture_output=True, text=True, check=False,
        )
        if p.returncode != 0:
            return {"id": vid, "category": cat, "download_error": p.stderr[-300:]}

    return {"id": vid, "category": cat, "mp4": str(mp4_path)}


def analyze_color_metrics(mp4_path: pathlib.Path, n_samples: int = 18) -> dict:
    cap = cv2.VideoCapture(str(mp4_path))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if total <= 0:
        cap.release()
        return {}
    idxs = np.linspace(int(total * 0.06), max(int(total * 0.06) + 1, int(total * 0.94)), n_samples, dtype=int)
    luma_p5, luma_p50, luma_p95, sat_med, a_shift, b_shift = [], [], [], [], [], []
    shad_b_r, high_b_r = [], []
    for fi in idxs:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(fi))
        ok, bgr = cap.read()
        if not ok or bgr is None:
            continue
        small = cv2.resize(bgr, (320, 180))
        lab = cv2.cvtColor(small, cv2.COLOR_BGR2LAB).astype(np.float32)
        hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV).astype(np.float32)
        L = lab[:, :, 0] * (100.0 / 255.0)
        A = lab[:, :, 1] - 128.0
        B = lab[:, :, 2] - 128.0
        luma_p5.append(float(np.percentile(L, 5)))
        luma_p50.append(float(np.percentile(L, 50)))
        luma_p95.append(float(np.percentile(L, 95)))
        sat_med.append(float(np.median(hsv[:, :, 1]) / 255.0))
        a_shift.append(float(np.mean(A)))
        b_shift.append(float(np.mean(B)))
        # Split-tone check: shadow vs highlight B-R balance (negative = warm/orange, positive = cool/teal)
        rgb = small[:, :, ::-1].astype(np.float32)
        lum = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
        sh_m = lum < 55.0
        hi_m = lum > 185.0
        if np.any(sh_m):
            shad_b_r.append(float(np.mean(rgb[:, :, 2][sh_m] - rgb[:, :, 0][sh_m])))
        if np.any(hi_m):
            high_b_r.append(float(np.mean(rgb[:, :, 2][hi_m] - rgb[:, :, 0][hi_m])))
    cap.release()
    if not luma_p5:
        return {}
    return {
        "black_floor_p5_L": round(float(np.median(luma_p5)), 1),
        "midtone_p50_L": round(float(np.median(luma_p50)), 1),
        "highlight_p95_L": round(float(np.median(luma_p95)), 1),
        "dynamic_span_L": round(float(np.median(luma_p95) - np.median(luma_p5)), 1),
        "sat_median": round(float(np.median(sat_med)), 3),
        "lab_a_green_magenta": round(float(np.median(a_shift)), 2),
        "lab_b_blue_yellow": round(float(np.median(b_shift)), 2),
        "shadow_blue_minus_red": round(float(np.median(shad_b_r)), 1) if shad_b_r else None,
        "highlight_blue_minus_red": round(float(np.median(high_b_r)), 1) if high_b_r else None,
    }


def analyze_video_full(item: dict) -> dict:
    cat = item["category"]
    vid = item["id"]
    mp4_path = MEDIA / f"{cat}__{vid}.mp4"
    res = {
        "category": cat,
        "id": vid,
        "title": item.get("title"),
        "channel": item.get("channel"),
        "duration_s": item.get("duration_s"),
        "width": item.get("width"),
        "height": item.get("height"),
        "chapters": item.get("chapters") or [],
        "links_in_desc": item.get("links_in_desc") or [],
    }
    # Collect best VTT transcript
    vtts = sorted(SUBS.glob(f"{cat}__{vid}*.vtt"))
    if vtts:
        txt = clean_vtt_to_text(vtts[0])
        txt_path = SUBS / f"{cat}__{vid}.txt"
        txt_path.write_text(txt, encoding="utf-8")
        res["transcript_path"] = str(txt_path.relative_to(ROOT))
        res["transcript_chars"] = len(txt)
        res["transcript_preview"] = txt[:500]
    else:
        res["transcript_path"] = None

    if not mp4_path.exists():
        res["error"] = "missing_mp4"
        return res

    # 1. Audio metrics (ebur128 + 5-band FFT + dynamics)
    with tempfile.TemporaryDirectory() as td:
        wav_p = pathlib.Path(td) / "a.wav"
        dec = subprocess.run(
            [FFMPEG, "-y", "-v", "error", "-i", str(mp4_path), "-vn", "-ac", "1", "-ar", "48000", str(wav_p)],
            capture_output=True, text=True, check=False,
        )
        eb = subprocess.run(
            [FFMPEG, "-nostats", "-i", str(mp4_path), "-af", "ebur128=peak=true", "-f", "null", "-"],
            capture_output=True, text=True, check=False,
        ).stderr
        lufs_m = re.findall(r"I:\s+([-\d.]+)\s+LUFS", eb)
        lra_m = re.findall(r"LRA:\s+([-\d.]+)\s+LU", eb)
        pk_m = re.findall(r"Peak:\s+([-\d.]+)\s+dBFS", eb)
        audio = {
            "lufs_i": float(lufs_m[-1]) if lufs_m else None,
            "lra": float(lra_m[-1]) if lra_m else None,
            "peak_dbfs": float(pk_m[-1]) if pk_m else None,
        }
        if dec.returncode == 0 and wav_p.exists():
            y, sr = librosa.load(str(wav_p), sr=48000, mono=True)
            # Limit FFT to first 180s if long to stay super snappy on RAM
            y_fft = y[: sr * 180]
            freqs = np.fft.rfftfreq(len(y_fft), 1.0 / sr)
            mag2 = np.abs(np.fft.rfft(y_fft)) ** 2
            tot = float(mag2.sum()) + 1e-12
            bands = {
                k: round(100.0 * float(mag2[(freqs >= lo) & (freqs < hi)].sum()) / tot, 2)
                for k, (lo, hi) in (
                    ("sub_20_90", (20, 90)),
                    ("mud_100_350", (100, 350)),
                    ("voice_350_2500", (350, 2500)),
                    ("detail_2500_8000", (2500, 8000)),
                    ("air_8000_18000", (8000, 18000)),
                )
            }
            hop = int(sr * 0.05)
            rms = librosa.feature.rms(y=y, frame_length=hop * 2, hop_length=hop)[0]
            db = 20.0 * np.log10(np.maximum(rms, 1e-6))
            act = db > -55.0
            med_db = float(np.median(db[act])) if np.any(act) else -35.0
            audio["band_pct"] = bands
            audio["detail_air_pct"] = round(bands["detail_2500_8000"] + bands["air_8000_18000"], 2)
            audio["quiet15_pct"] = round(100.0 * float(np.mean(db < med_db - 15.0)), 1)
            audio["dead_zero_pct"] = round(100.0 * float(np.mean(db < -68.0)), 1)
        res["audio"] = audio

    # 2. Shot cut pacing (sample first 180s on long videos so FFmpeg scene detect runs fast!)
    dur_val = float(item.get("duration_s") or 30.0)
    scan_dur = min(dur_val, 180.0)
    sc = subprocess.run(
        [FFMPEG, "-v", "info", "-t", f"{scan_dur:.1f}", "-i", str(mp4_path), "-vf", "select='gt(scene,0.28)',showinfo", "-f", "null", "-"],
        capture_output=True, text=True, check=False,
    ).stderr
    cuts = [round(float(m.group(1)), 2) for ln in sc.splitlines() if (m := re.search(r"pts_time:([\d.]+)", ln))]
    lens = np.diff([0.0] + cuts + [scan_dur]) if cuts else np.array([scan_dur])
    res["pacing"] = {
        "scan_window_s": round(scan_dur, 1),
        "cuts_in_window": len(cuts),
        "cuts_per_min": round(len(cuts) * 60.0 / max(scan_dur, 1.0), 1),
        "median_shot_s": round(float(np.median(lens)), 2),
        "p90_shot_s": round(float(np.percentile(lens, 90)), 2),
        "shot_cv": round(float(np.std(lens) / max(np.mean(lens), 1e-6)), 3),
        "first_12_cuts_s": cuts[:12],
    }

    # 3. Colorimetry metrics
    res["color"] = analyze_color_metrics(mp4_path)

    # 4. Contact sheet (16 frames across video; for longform also make hook sheet of first 45s!)
    sheet_path = SHEETS / f"sheet_{cat}__{vid}.jpg"
    fps_pick = 16.0 / max(dur_val, 2.0)
    scale_w = 320 if (item.get("height") or 0) > (item.get("width") or 1) else 440
    subprocess.run(
        [FFMPEG, "-y", "-v", "error", "-i", str(mp4_path), "-vf", f"fps={fps_pick:.5f},scale={scale_w}:-1,tile=4x4", "-frames:v", "1", str(sheet_path)],
        check=False,
    )
    res["sheet"] = str(sheet_path.relative_to(ROOT))
    if dur_val >= 120:
        hook_sheet = SHEETS / f"hook45_{cat}__{vid}.jpg"
        subprocess.run(
            [FFMPEG, "-y", "-v", "error", "-t", "45", "-i", str(mp4_path), "-vf", f"fps={16/45:.5f},scale=440:-1,tile=4x4", "-frames:v", "1", str(hook_sheet)],
            check=False,
        )
        res["hook_sheet"] = str(hook_sheet.relative_to(ROOT))

    return res


def main() -> int:
    items = json.loads(META_PATH.read_text(encoding="utf-8"))
    print(f"Downloading {len(items)} videos + subtitles in parallel...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        dl = list(ex.map(download_one, items))
    for d in dl:
        if "download_error" in d:
            print("DL_ERR:", d)

    print("Analyzing audio, pacing, colorimetry, and contact sheets...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        reports = list(ex.map(analyze_video_full, items))

    out_json = STUDY / "study_report_all14.json"
    out_json.write_text(json.dumps(reports, indent=2, ensure_ascii=False), encoding="utf-8")
    for r in reports:
        a = r.get("audio", {})
        p = r.get("pacing", {})
        c = r.get("color", {})
        print(
            f"{r['category']:16s} | {r['id']:11s} | {a.get('lufs_i')} LUFS LRA {a.get('lra')} "
            f"mud={a.get('band_pct', {}).get('mud_100_350')}% air={a.get('detail_air_pct')}% | "
            f"cuts/m={p.get('cuts_per_min')} med={p.get('median_shot_s')}s CV={p.get('shot_cv')} | "
            f"L5={c.get('black_floor_p5_L')} L95={c.get('highlight_p95_L')} sat={c.get('sat_median')} "
            f"shBR={c.get('shadow_blue_minus_red')} hiBR={c.get('highlight_blue_minus_red')} | sub={r.get('transcript_chars', 0)}ch"
        )
    print("STUDY_ALL14_DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
