"""Modular Multi-Aspect Narrative Video & 5-Stem Audio Composer (Data-Driven).

Builds narrative films from ANY valid `beat_sheet.json` in 16:9 horizontal, 9:16 portrait,
or BOTH from one declarative pipeline:
1. Pre-render `studio_kit/beat_sheet.py` causality, copywriting & monotony validation.
2. Declarative 5-stem audio via `sound_engine.py` (`apply_beat_sheet_cues`, `audio_clips`,
   `music_plan` with dips/Great Hall tails, and adaptive 9-band voice carving).
3. Optional `faster-whisper` (`int8`) word-timestamp auto-captioning + live WAV peak bar
   extraction into `overlay_plan` for genuine NLE waveform pop-ups & music dip strips.
4. Per-beat non-monotonous camera motion (`zoom_start`->`zoom_end`, `speed`, `transition_in`).
5. Crisp 30fps RGBA overlays in headless Windows Chrome (`ANGLE D3D11`) + FFmpeg assembly.
6. Post-render `acoustic_audit.py` + audio arc PNG & exact-frame contact sheets.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT / "studio_kit") not in sys.path:
    sys.path.insert(0, str(ROOT / "studio_kit"))

import acoustic_audit  # noqa: E402
import beat_sheet  # noqa: E402
import color_grade  # noqa: E402
import safe_zones  # noqa: E402
import sound_engine  # noqa: E402

FFMPEG = str(ROOT / "bin" / "ffmpeg.exe")
HTML_STAGE = ROOT / "studio_kit" / "tactile_scene_kit.html"

ASPECT_PRESETS: dict[str, tuple[int, int, str]] = {
    "16x9": (1920, 1080, "narrative_cinema_16x9"),
    "9x16": (1080, 1920, "narrative_shorts_9x16"),
}

CHROME_GPU_ARGS = [
    "--use-gl=angle",
    "--use-angle=d3d11",
    "--enable-webgl",
    "--ignore-gpu-blocklist",
]


def auto_transcribe_words(audio_or_video: str | pathlib.Path, *, t_offset: float = 0.0, device: str = "cpu") -> list[dict[str, Any]]:
    """Extract word-level caption timings cleanly using local faster-whisper (int8)."""
    from faster_whisper import WhisperModel

    src = pathlib.Path(audio_or_video)
    if not src.is_absolute():
        src = ROOT / src
    model = WhisperModel("base", device=device, compute_type="int8")
    segments, _ = model.transcribe(str(src), word_timestamps=True)
    words: list[dict[str, Any]] = []
    for seg in segments:
        for w in (seg.words or []):
            words.append({
                "w": w.word.strip(),
                "t0": round(float(w.start) + t_offset, 3),
                "t1": round(float(w.end) + t_offset, 3),
            })
    return words


def build_overlay_plan(sheet: dict[str, Any], eng: sound_engine.SoundEngine5Stem, out_audio_dir: pathlib.Path) -> dict[str, Any]:
    """Assemble the complete overlay_plan JSON for tactile_scene_kit.html from beat-sheet + live stems."""
    ov = sheet.get("overlays", {})
    bus_map = {
        "ambience": eng.ambience,
        "foley": eng.foley,
        "transitions": eng.transitions,
        "voice": eng.voice,
    }

    wave_badges = []
    for wb in ov.get("wave_badges", []):
        bus_key = str(wb.get("bus", "ambience"))
        arr = bus_map.get(bus_key, eng.ambience)
        if wb.get("mix_transitions"):
            arr = arr + eng.transitions * 0.4
        bars = sound_engine.extract_waveform_bars(arr, float(wb["t0"]), float(wb["t1"]), bars=int(wb.get("bars_count", 28)))
        wave_badges.append({
            "t0": float(wb["t0"]),
            "t1": float(wb["t1"]),
            "label": str(wb.get("label", "")),
            "bars": bars,
        })

    music_dip_ui = None
    dip_cfg = ov.get("music_dip_ui")
    if dip_cfg:
        stem_mus = pathlib.Path(out_audio_dir) / "stems" / "stem_music.wav"
        mus_arr = sound_engine.load_stereo(stem_mus) if stem_mus.exists() else eng.music
        bars = sound_engine.extract_waveform_bars(
            mus_arr,
            float(dip_cfg.get("sample_t0", dip_cfg["t0"])),
            float(dip_cfg.get("sample_t1", dip_cfg["t1"])),
            bars=int(dip_cfg.get("bars_count", 48)),
        )
        music_dip_ui = {
            "t0": float(dip_cfg["t0"]),
            "t1": float(dip_cfg["t1"]),
            "headerLeft": str(dip_cfg.get("header_left", "STEM_MUSIC.WAV")),
            "headerRight": str(dip_cfg.get("header_right", "MUSIC DIPS FOR THE CUT")),
            "bars": bars,
        }

    return {
        "speakerCaptions": ov.get("speaker_captions", []),
        "cuttingMat": ov.get("cutting_mat"),
        "promptCards": ov.get("prompt_cards", []),
        "abTags": ov.get("ab_tags", []),
        "waveBadges": wave_badges,
        "musicDipUi": music_dip_ui,
        "closingTitle": ov.get("closing_title"),
        "ludaLetterbox": ov.get("luda_letterbox"),
        "collageCards": ov.get("collage_cards", []),
        "maciekCaptions": ov.get("maciek_captions", []),
        "socialBubbles": ov.get("social_bubbles", []),
        "narrativeClusters": ov.get("narrative_clusters", []),
        "camera2dCanvas": ov.get("camera_2d_canvas"),
        "explainerDiagrams": ov.get("explainer_diagrams", []),
        "debugSafeZone": bool(sheet.get("debug_safe_zone", False)),
    }


def build_narrative_audio(sheet: dict[str, Any], out_audio_dir: pathlib.Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Compose the 5-stem 48kHz mix strictly from declarative beat-sheet fields."""
    dur_s = float(sheet["duration_s"])
    eng = sound_engine.SoundEngine5Stem(
        dur_s,
        profile=sheet.get("sound_palette", "organic-cinema"),
        t60=float(sheet.get("room_ir_t60_s", 1.05)),
    )

    # 1. Load music bed FIRST so detect_musical_key sets eng.active_music_key for tonal SFX harmony
    mp = sheet.get("music_plan") or {}
    if mp.get("enabled", True):
        eng.add_music_bed(
            mp.get("track_path"),
            gain_db=float(mp.get("gain_db", -20.5)),
            root_hz=float(mp.get("root_hz", 146.83)),
            bpm=float(mp.get("bpm", sheet.get("bpm", 100.0))),
            reverse_lead_in_s=float(mp.get("reverse_lead_in_s", 0.0)),
            loop_end_rise_s=float(mp.get("loop_end_rise_s", 0.0)),
            segments=mp.get("segments"),
        )
        for dp in mp.get("dips", []):
            eng.add_music_dip(
                float(dp["t0"]),
                float(dp["t1"]),
                db=float(dp.get("db", -10.0)),
                fade_ms=float(dp.get("fade_ms", 180.0)),
            )

    # 2. Declarative sound_cues, key-matched tonal_cues, filter_sweeps & silence_pockets
    eng.apply_beat_sheet_cues(sheet)

    # 3. Declarative real-footage / dialogue audio clips
    for ac in sheet.get("audio_clips", []):
        eng.add_source_clip_audio(
            ac["src"],
            src_start_s=float(ac.get("src_start_s", 0.0)),
            dur_s=float(ac["dur_s"]),
            t_s=float(ac["t_s"]),
            bus=str(ac.get("bus", "ambience")),
            target_rms_db=float(ac.get("target_rms_db", -22.0)),
            pre_lap_ms=float(ac.get("pre_lap_ms", 0.0)),
            pan=float(ac.get("pan", 0.0)),
            hp_hz=float(ac.get("hp_hz", 120.0)),
            lp_hz=ac.get("lp_hz"),
            fade_ms=float(ac.get("fade_ms", 28.0)),
            send=float(ac.get("send", 0.14)),
        )

    plan = eng.render_mix(
        out_audio_dir,
        target_lufs=float(mp.get("target_lufs", -16.0)),
        target_peak_db=float(mp.get("target_peak_db", -5.4)),
        export_stems=True,
    )
    overlay_data = build_overlay_plan(sheet, eng, out_audio_dir)
    return plan, overlay_data


def _render_overlay_pngs(
    overlay_dir: pathlib.Path,
    *,
    width: int,
    height: int,
    fps: int,
    dur_s: float,
    overlay_plan: dict[str, Any],
    platform: str | None = None,
    enforce_safe_zones: bool = True,
) -> dict[str, Any]:
    if overlay_dir.exists():
        shutil.rmtree(overlay_dir)
    overlay_dir.mkdir(parents=True, exist_ok=True)
    n_frames = int(round(dur_s * fps))
    url = HTML_STAGE.as_uri()
    sz_report: dict[str, Any] = {"ok": True, "violations": []}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=True, args=CHROME_GPU_ARGS)
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
        page.goto(url, wait_until="load")
        page.evaluate("() => document.fonts.ready")
        page.evaluate(
            """() => Promise.all([
                document.fonts.load('800 42px "Inter Tight"'),
                document.fonts.load('italic 400 42px "Instrument Serif"'),
                document.fonts.load('700 16px "JetBrains Mono"')
            ])"""
        )
        page.evaluate("(p) => window.__setPlan(p)", overlay_plan)

        # Pre-render Platform UI Safe-Zone DOM bounding-box audit across timeline checkpoints
        plat = platform or ("universal_vertical" if height > width else "youtube_16x9")
        sample_ts = [round((k + 0.5) * dur_s / 14.0, 2) for k in range(14)]
        sz_report = safe_zones.audit_html_safe_zones(page, sample_ts, width=width, height=height, platform=plat)
        if enforce_safe_zones and not sz_report["ok"]:
            browser.close()
            raise RuntimeError(f"Platform safe-zone violation ({plat}): {sz_report['violations'][:3]}")

        for fi in range(n_frames):
            t = fi / float(fps)
            page.evaluate("(tt) => window.__seek(tt)", t)
            page.screenshot(path=str(overlay_dir / f"ov_{fi:05d}.png"), omit_background=True, type="png")
        browser.close()
    return sz_report


def _assemble_aspect_video(
    sheet: dict[str, Any],
    *,
    aspect_key: str,
    master_wav: pathlib.Path,
    overlay_dir: pathlib.Path,
    out_mp4: pathlib.Path,
    fps: int = 30,
) -> pathlib.Path:
    width, height, _ = ASPECT_PRESETS[aspect_key]
    inputs: list[str] = []
    f_lines: list[str] = []
    seg_refs: list[str] = []
    inp_idx = 0
    seg_cnt = 0

    def _add_clip_filter(
        src_path: str,
        in_s: float,
        seg_d: float,
        zoom_start: float = 1.0,
        zoom_end: float | None = None,
        crop_x: float = 0.5,
        speed: float = 1.0,
        transition_in: str | None = None,
        transition_dur_s: float = 0.25,
    ) -> None:
        nonlocal inp_idx, seg_cnt
        n_fr = max(1, int(round(seg_d * fps)))
        z0 = float(zoom_start)
        z1 = float(zoom_end) if zoom_end is not None else z0
        spd = max(0.25, min(4.0, float(speed)))
        src_need = seg_d * spd + 0.35
        inputs.extend(["-ss", f"{in_s:.3f}", "-t", f"{src_need:.3f}", "-i", str(ROOT / src_path)])
        vref = f"v{seg_cnt}"

        chain = [f"[{inp_idx}:v]"]
        if abs(spd - 1.0) > 1e-3:
            chain.append(f"setpts=PTS/{spd:.4f},")
        chain.append(f"fps={fps},")

        if width < height:
            chain.append(f"crop=trunc(ih*9/16/2)*2:ih:(iw-ow)*{crop_x:.3f}:0,")

        if abs(z1 - z0) > 1e-3 and n_fr > 2:
            # Smooth progressive push-in or pull-out motion to avoid static-shot monotony
            max_z = max(z0, z1, 1.06)
            zw, zh = int(round(width * max_z)), int(round(height * max_z))
            if width < height:
                chain.append(f"scale={zw}:{zh},")
            else:
                chain.append(f"scale={zw}:{zh}:force_original_aspect_ratio=increase,crop={zw}:{zh}:(iw-{zw})/2:(ih-{zh})/2,")
            dz = z1 - z0
            z_expr = f"({z0:.4f}+({dz:.4f})*(on/{max(1, n_fr - 1)}))/{max_z:.4f}"
            chain.append(
                f"zoompan=z='{z0:.4f}+({dz:.4f})*(in/{max(1, n_fr - 1)})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={width}x{height}:fps={fps},"
            )
            del z_expr
        else:
            zw, zh = int(round(width * z0)), int(round(height * z0))
            if width < height:
                chain.append(f"scale={zw}:{zh},crop={width}:{height}:(iw-{width})/2:(ih-{height})/2,")
            else:
                chain.append(f"scale={zw}:{zh}:force_original_aspect_ratio=increase,crop={width}:{height}:(iw-{width})/2:(ih-{height})/2,")

        chain.append(f"setsar=1,trim=end_frame={n_fr},setpts=PTS-STARTPTS")
        if transition_in in ("fade", "dissolve") and seg_d > transition_dur_s:
            chain.append(f",fade=t=in:st=0:d={transition_dur_s:.3f}")
        chain.append(f",format=yuv420p[{vref}]")

        f_lines.append("".join(chain))
        seg_refs.append(f"[{vref}]")
        inp_idx += 1
        seg_cnt += 1

    for beat in sheet["beats"]:
        t0, t1 = float(beat["t_start"]), float(beat["t_end"])
        bdur = t1 - t0
        tr_in = beat.get("transition_in")
        tr_dur = float(beat.get("transition_dur_s", 0.25))
        if beat.get("shot_type") == "match_cut_split" and beat.get("split_left") and beat.get("split_right"):
            # Gaku Lange Trend 3: Horizon/trajectory Match-Cut Split Screen (hstack)
            n_fr = max(1, int(round(bdur * fps)))
            left_cfg, right_cfg = beat["split_left"], beat["split_right"]
            half_w = width // 2
            li, ri = inp_idx, inp_idx + 1
            inputs.extend(["-ss", f"{float(left_cfg.get('in_s', 0.0)):.3f}", "-t", f"{bdur + 0.35:.3f}", "-i", str(ROOT / left_cfg["src"])])
            inputs.extend(["-ss", f"{float(right_cfg.get('in_s', 0.0)):.3f}", "-t", f"{bdur + 0.35:.3f}", "-i", str(ROOT / right_cfg["src"])])
            vref = f"v{seg_cnt}"
            f_lines.append(
                f"[{li}:v]fps={fps},scale={half_w}:{height}:force_original_aspect_ratio=increase,crop={half_w}:{height},setsar=1,trim=end_frame={n_fr},setpts=PTS-STARTPTS[{vref}_l];"
                f"[{ri}:v]fps={fps},scale={width - half_w}:{height}:force_original_aspect_ratio=increase,crop={width - half_w}:{height},setsar=1,trim=end_frame={n_fr},setpts=PTS-STARTPTS[{vref}_r];"
                f"[{vref}_l][{vref}_r]hstack=inputs=2,format=yuv420p[{vref}]"
            )
            seg_refs.append(f"[{vref}]")
            inp_idx += 2
            seg_cnt += 1
        elif "clip_segments" in beat:
            for idx_cs, cs in enumerate(beat["clip_segments"]):
                z0 = float(cs.get("zoom_start", cs.get("zoom", 1.0)))
                z1 = cs.get("zoom_end", z0)
                _add_clip_filter(
                    cs["src"], float(cs["in_s"]), float(cs["dur_s"]),
                    zoom_start=z0, zoom_end=z1,
                    crop_x=float(cs.get("crop_x", 0.5)),
                    speed=float(cs.get("speed", 1.0)),
                    transition_in=tr_in if idx_cs == 0 else None,
                    transition_dur_s=tr_dur,
                )
        elif "clip_source" in beat:
            z0 = float(beat.get("zoom_start", beat.get("zoom", 1.0)))
            z1 = beat.get("zoom_end", z0)
            _add_clip_filter(
                beat["clip_source"], float(beat.get("clip_in_s", 0.0)), bdur,
                zoom_start=z0, zoom_end=z1,
                crop_x=float(beat.get("crop_x", 0.5)),
                speed=float(beat.get("speed", 1.0)),
                transition_in=tr_in,
                transition_dur_s=tr_dur,
            )
        else:
            n_fr = max(1, int(round(bdur * fps)))
            vref = f"v{seg_cnt}"
            matte_hex = str(beat.get("matte_color", "#F4EFE6"))
            f_lines.append(
                f"color=c={matte_hex}:s={width}x{height}:r={fps},setsar=1,trim=end_frame={n_fr},setpts=PTS-STARTPTS,format=yuv420p[{vref}]"
            )
            seg_refs.append(f"[{vref}]")
            seg_cnt += 1

    ov_idx = inp_idx
    inputs.extend(["-framerate", str(fps), "-i", str(overlay_dir / "ov_%05d.png")])
    au_idx = ov_idx + 1
    inputs.extend(["-i", str(master_wav)])

    # Clean-Plate Grading Rule (PuoI9paASys): apply filmic LUT/halation strictly BEFORE crisp PNG overlay!
    grade_cfg = sheet.get("color_grade")
    if isinstance(grade_cfg, str):
        grade_cfg = {"preset": grade_cfg}
    if isinstance(grade_cfg, dict) and grade_cfg.get("preset") and grade_cfg["preset"] != "neutral_rec709":
        concat_line = f"{''.join(seg_refs)}concat=n={seg_cnt}:v=1:a=0,settb=1/{fps},setpts=N/({fps}*TB)[base_raw]"
        grade_line = color_grade.build_ffmpeg_grade_chain(
            str(grade_cfg["preset"]),
            in_label="base_raw",
            out_label="base",
            enable_halation=grade_cfg.get("halation"),
            enable_vignette=grade_cfg.get("vignette"),
        )
        post_lines = [concat_line, grade_line]
    else:
        post_lines = [f"{''.join(seg_refs)}concat=n={seg_cnt}:v=1:a=0,settb=1/{fps},setpts=N/({fps}*TB)[base]"]

    ov_line = f"[{ov_idx}:v]format=rgba,settb=1/{fps},setpts=N/({fps}*TB)[ov];[base][ov]overlay=0:0:eof_action=pass:format=auto,format=yuv420p[vout]"
    filt = ";".join(f_lines + post_lines + [ov_line])

    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        FFMPEG, "-y", "-v", "error",
        *inputs,
        "-filter_complex", filt,
        "-map", "[vout]",
        "-map", f"{au_idx}:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-t", f"{float(sheet['duration_s']):.3f}",
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True)
    return out_mp4


def _build_contact_sheet(mp4_path: pathlib.Path, out_jpg: pathlib.Path, times: list[float], cols: int = 4, fps: int = 30) -> pathlib.Path:
    frames = [max(0, int(round(t * fps))) for t in times]
    select_expr = "+".join(f"eq(n\\,{f})" for f in frames)
    rows = max(1, (len(times) + cols - 1) // cols)
    vf = f"select='{select_expr}',scale=480:-1,tile={cols}x{rows}"
    subprocess.run(
        [FFMPEG, "-y", "-v", "error", "-i", str(mp4_path), "-vf", vf, "-frames:v", "1", str(out_jpg)],
        check=True,
    )
    return out_jpg


def run_pipeline(
    beat_sheet_path: pathlib.Path,
    aspects: list[str],
    *,
    out_dir: pathlib.Path,
    debug_safe_zone: bool = False,
) -> dict[str, Any]:
    sheet_check = beat_sheet.validate_beat_sheet_file(beat_sheet_path)
    if not sheet_check["ok"]:
        raise RuntimeError(f"Beat-sheet validation failed: {sheet_check['errors']}")
    sheet = json.loads(beat_sheet_path.read_text(encoding="utf-8"))
    if debug_safe_zone:
        sheet["debug_safe_zone"] = True
    dur_s = float(sheet["duration_s"])
    fps = 30

    audio_dir = out_dir / "narrative_audio"
    mix_plan, overlay_base = build_narrative_audio(sheet, audio_dir)
    master_wav = pathlib.Path(mix_plan["master_wav"])

    results: dict[str, Any] = {
        "beat_sheet_metrics": sheet_check["metrics"],
        "mix_lufs": mix_plan["lufs_i"],
        "mix_peak_db": mix_plan["peak_dbfs"],
        "deliverables": {},
    }

    sheet_times = sheet.get("contact_sheet_times") or [
        round((i + 0.5) * dur_s / 16.0, 2) for i in range(16)
    ]

    for asp in aspects:
        if asp not in ASPECT_PRESETS:
            raise ValueError(f"Unsupported aspect '{asp}'. Use one of {list(ASPECT_PRESETS)}")
        w, h, stem_name = ASPECT_PRESETS[asp]
        out_prefix = str(sheet.get("output_prefix", "")).strip()
        final_stem = f"{out_prefix}_{asp}" if out_prefix else stem_name
        ov_dir = out_dir / f"_ov_{asp}"
        ov_plan = dict(overlay_base)
        ov_plan["aspect"] = asp
        _render_overlay_pngs(ov_dir, width=w, height=h, fps=fps, dur_s=dur_s, overlay_plan=ov_plan)

        mp4_path = out_dir / f"{final_stem}.mp4"
        _assemble_aspect_video(sheet, aspect_key=asp, master_wav=master_wav, overlay_dir=ov_dir, out_mp4=mp4_path, fps=fps)
        shutil.rmtree(ov_dir, ignore_errors=True)

        arc_png = out_dir / f"{final_stem}_audio_arc.png"
        audit = acoustic_audit.audit_media(
            mp4_path,
            beat_sheet_path=beat_sheet_path,
            out_png=arc_png,
            profile=sheet.get("audio_audit_profile", "narrative_voice_film"),
            has_bgm=bool(sheet.get("music_plan", {}).get("enabled", True)),
            check_cuts=True,
        )
        if not audit["ok"]:
            raise RuntimeError(f"Acoustic audit failed for {mp4_path}: {audit['failures']}")

        sheet_jpg = out_dir / f"{final_stem}_sheet.jpg"
        _build_contact_sheet(mp4_path, sheet_jpg, sheet_times, cols=4, fps=fps)

        results["deliverables"][asp] = {
            "mp4": str(mp4_path),
            "resolution": f"{w}x{h}",
            "contact_sheet": str(sheet_jpg),
            "audio_arc": str(arc_png),
            "audit_ok": audit["ok"],
            "lufs_i": audit["metrics"]["loudness"]["lufs_i"],
            "peak_dbfs": audit["metrics"]["loudness"]["peak_dbfs"],
            "mud_pct": audit["metrics"]["band_pct"]["mud_100_350"],
            "voice_pct": audit["metrics"]["band_pct"]["voice_350_2500"],
            "detail_air_pct": audit["metrics"]["detail_air_pct"],
        }

    return results


def main() -> int:
    ap = argparse.ArgumentParser(description="Declarative multi-aspect narrative video & 5-stem audio pipeline.")
    ap.add_argument("--beat-sheet", default=str(ROOT / "studio_kit" / "narrative_showcase_beat_sheet.json"))
    ap.add_argument("--aspects", default="16x9,9x16", help="Comma-separated aspect keys: 16x9, 9x16")
    ap.add_argument("--out-dir", default=str(ROOT / "studio_kit" / "renders"))
    ap.add_argument("--debug-safe-zone", action="store_true", help="Overlay translucent platform safe-zone grid for layout review")
    args = ap.parse_args()

    res = run_pipeline(
        pathlib.Path(args.beat_sheet),
        [x.strip() for x in args.aspects.split(",") if x.strip()],
        out_dir=pathlib.Path(args.out_dir),
        debug_safe_zone=args.debug_safe_zone,
    )
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
