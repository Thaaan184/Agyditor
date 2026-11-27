"""Deep Narrative Typography & Safe-Zone Deconstruction Study (3 References).

Downloads RhVB8WPLJAI (Short), BWRdNeNkph4 (Long/Mid), and G-DHQAzulyU (Long/Mid)
onto Drive D:, extracts transcripts, measures cut/text cadence, and builds dense
contact sheets (full arc + high-res detail strips) for visual inspection.
"""
from __future__ import annotations

import concurrent.futures
import json
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
STUDY = ROOT / "references" / "narrative_typography_study"
MEDIA = STUDY / "media"
SUBS = STUDY / "subs"
SHEETS = STUDY / "sheets"
for d in (MEDIA, SUBS, SHEETS):
    d.mkdir(parents=True, exist_ok=True)

YTDLP = str(ROOT / "bin" / "yt-dlp.exe")
FFMPEG = str(ROOT / "bin" / "ffmpeg.exe")

URLS = [
    ("typo_short", "RhVB8WPLJAI", "https://youtube.com/shorts/RhVB8WPLJAI"),
    ("typo_long_1", "BWRdNeNkph4", "https://youtu.be/BWRdNeNkph4"),
    ("typo_long_2", "G-DHQAzulyU", "https://youtu.be/G-DHQAzulyU"),
]


def clean_vtt(p: pathlib.Path) -> str:
    lines, out = [], []
    for ln in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = re.sub(r"<[^>]+>", "", ln).strip()
        if not s or s.startswith(("WEBVTT", "Kind:", "Language:")) or "-->" in s:
            continue
        s = re.sub(r"\s+", " ", s)
        if not lines or lines[-1] != s:
            lines.append(s)
    for ln in lines:
        if out and ln.startswith(out[-1]):
            out[-1] = ln
        elif out and out[-1].endswith(ln):
            continue
        else:
            out.append(ln)
    return "\n".join(out)


def process_one(item: tuple[str, str, str]) -> dict:
    cat, vid, url = item
    # 1. Metadata
    mp = subprocess.run(
        [YTDLP, "--dump-single-json", "--no-warnings", "--skip-download", url],
        capture_output=True, text=True, check=False,
    )
    if mp.returncode != 0:
        return {"category": cat, "id": vid, "error": mp.stderr[:400]}
    meta = json.loads(mp.stdout)
    dur = float(meta.get("duration") or 0)
    w, h = int(meta.get("width") or 0), int(meta.get("height") or 0)

    # 2. Subtitles
    subprocess.run(
        [
            YTDLP, "--skip-download", "--no-warnings",
            "--write-sub", "--write-auto-sub",
            "--sub-langs", "en,en-orig,id,id-orig",
            "--sub-format", "vtt",
            "-o", str(SUBS / f"{cat}__{vid}.%(ext)s"), url,
        ],
        capture_output=True, text=True, check=False,
    )
    vtts = sorted(SUBS.glob(f"{cat}__{vid}*.vtt"))
    transcript = ""
    if vtts:
        transcript = clean_vtt(vtts[0])
        (SUBS / f"{cat}__{vid}.txt").write_text(transcript, encoding="utf-8")

    # 3. Video download (1080p for short, 720p for long)
    mp4 = MEDIA / f"{cat}__{vid}.mp4"
    if not mp4.exists() or mp4.stat().st_size < 10_000:
        fmt = (
            "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best"
            if dur <= 90 else
            "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best"
        )
        subprocess.run(
            [
                YTDLP, "--no-warnings", "--ffmpeg-location", str(ROOT / "bin"),
                "-f", fmt, "--merge-output-format", "mp4", "-o", str(mp4), url,
            ],
            capture_output=True, text=True, check=False,
        )

    sheets_made = []
    if mp4.exists():
        is_vert = h > w
        sw = 340 if is_vert else 480
        # Full overview 4x4 sheet
        s_all = SHEETS / f"full_{cat}__{vid}.jpg"
        fps_all = 16.0 / max(dur, 2.0)
        subprocess.run(
            [FFMPEG, "-y", "-v", "error", "-i", str(mp4), "-vf", f"fps={fps_all:.5f},scale={sw}:-1,tile=4x4", "-frames:v", "1", str(s_all)],
            check=False,
        )
        sheets_made.append(str(s_all.relative_to(ROOT)))

        # Dense early/mid typography inspection sheets (captures actual motion/highlight sequences!)
        if dur <= 90:
            # Dense 1 frame every ~1.2s for first 19s (16 frames) + remainder
            s_d1 = SHEETS / f"dense1_{cat}__{vid}.jpg"
            fps_d1 = 16.0 / min(dur, 24.0)
            subprocess.run(
                [FFMPEG, "-y", "-v", "error", "-t", str(min(dur, 24.0)), "-i", str(mp4), "-vf", f"fps={fps_d1:.5f},scale={sw}:-1,tile=4x4", "-frames:v", "1", str(s_d1)],
                check=False,
            )
            sheets_made.append(str(s_d1.relative_to(ROOT)))
        else:
            # First 60s hook + Mid 60s typography sequence (16 frames each = every 3.75s!)
            for label, ss in (("hook60", 0), ("mid60", int(dur * 0.35))):
                s_part = SHEETS / f"{label}_{cat}__{vid}.jpg"
                subprocess.run(
                    [FFMPEG, "-y", "-v", "error", "-ss", str(ss), "-t", "60", "-i", str(mp4), "-vf", f"fps={16/60:.5f},scale={sw}:-1,tile=4x4", "-frames:v", "1", str(s_part)],
                    check=False,
                )
                sheets_made.append(str(s_part.relative_to(ROOT)))

    return {
        "category": cat,
        "id": vid,
        "url": url,
        "title": meta.get("title"),
        "channel": meta.get("channel") or meta.get("uploader"),
        "duration_s": dur,
        "width": w,
        "height": h,
        "chapters": meta.get("chapters") or [],
        "description": (meta.get("description") or "")[:700],
        "transcript_chars": len(transcript),
        "sheets": sheets_made,
    }


def main() -> int:
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        res = list(ex.map(process_one, URLS))
    (STUDY / "typo_study_report.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    for r in res:
        print(f"{r['category']:12s} | {r['id']} | {r.get('duration_s')}s | {r.get('width')}x{r.get('height')} | {r.get('channel')} | {r.get('title')}")
        print("  CHAPTERS:", [(round(c["start_time"], 1), c["title"]) for c in r.get("chapters", [])])
        print("  SHEETS:", r.get("sheets"))
        print("  SUBS:", r.get("transcript_chars"), "chars")
    print("TYPO_STUDY_DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
