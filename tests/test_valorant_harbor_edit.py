"""Test suite for Valorant Harbor 3K Lucky Clutch vertical edit pipeline."""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from projects.valorant_edit import timeline_map as tm


def test_timeline_monotonic_and_covers_45_to_75():
    assert abs(tm.map_out_to_src(0.0)["src_t"] - 45.0) < 1e-3
    assert abs(tm.map_out_to_src(tm.TOTAL_DURATION_S)["src_t"] - 75.0) < 0.05
    prev = 45.0
    for f in range(tm.TOTAL_FRAMES):
        st = tm.map_out_to_src(f / tm.FPS)
        assert st["src_t"] >= prev - 1e-6
        prev = st["src_t"]


def test_freeze_frame_holds_exact_71_75_for_1_75s():
    mid_freeze = tm.map_out_to_src(22.50)
    assert mid_freeze["is_freeze"] is True
    assert abs(mid_freeze["src_t"] - 71.75) < 1e-3
    assert mid_freeze["segment_id"] == "b08_lucky_freeze"
    # Before and after freeze map smoothly without reversing
    before = tm.map_out_to_src(21.70)
    after = tm.map_out_to_src(23.55)
    assert before["is_freeze"] is False and before["src_t"] < 71.75
    assert after["is_freeze"] is False and after["src_t"] > 71.75


def test_project_source_to_canvas_accuracy_and_censor_span():
    cx, cy = tm.project_source_to_canvas(*tm.CHAMBER_SRC_XY, 22.50)
    rx, ry = tm.project_source_to_canvas(*tm.REYNA_SRC_XY, 22.50)
    assert 200 < cx < 880 and 600 < cy < 1300
    assert rx > cx and ry < cy  # Reyna stands right and above Chamber inside the arch
    c0 = tm.map_src_to_out(tm.CENSOR_SRC_SPAN[0])
    c1 = tm.map_src_to_out(tm.CENSOR_SRC_SPAN[1])
    assert 8.85 < c0 < c1 < 9.55
    assert tm.OUTPUT_ROOT == pathlib.Path(r"D:\Clip\Edit\Valorant")


def test_beat_sheet_passes_studio_gate():
    from studio_kit.beat_sheet import validate_beat_sheet_file

    res = validate_beat_sheet_file(ROOT / "projects" / "valorant_edit" / "beat_sheet.json")
    assert res["ok"] is True, f"Beat sheet errors: {res['errors']}"
    assert res["warnings"] == []
    assert res["metrics"]["shot_cv"] >= 0.20
    assert res["metrics"]["silence_pockets_count"] == 2
    assert res["metrics"]["hero_cues_count"] >= 2


def test_audio_master_censor_waveform_and_acoustic_gate():
    import json
    import numpy as np
    import soundfile as sf
    from studio_kit.acoustic_audit import audit_media

    master = tm.WORK_DIR / "audio_mix" / "master_mix.wav"
    voice_stem = tm.WORK_DIR / "audio_mix" / "stems" / "stem_voice.wav"
    wf_json = tm.WORK_DIR / "audio_waveform.json"
    assert master.exists(), f"Missing {master}"
    assert voice_stem.exists(), f"Missing {voice_stem}"
    assert wf_json.exists(), f"Missing {wf_json}"

    # Verify profanity window on stem_voice is attenuated by >= 20 dB vs "backup-nya To" speech right before it
    y, sr = sf.read(str(voice_stem))
    c0, c1 = tm.map_src_to_out(tm.CENSOR_SRC_SPAN[0]), tm.map_src_to_out(tm.CENSOR_SRC_SPAN[1])
    before = y[int((c0 - 0.70) * sr) : int((c0 - 0.30) * sr)]
    censored = y[int((c0 + 0.05) * sr) : int((c1 - 0.05) * sr)]
    db_before = 20.0 * np.log10(np.sqrt(np.mean(before ** 2)) + 1e-9)
    db_censored = 20.0 * np.log10(np.sqrt(np.mean(censored ** 2)) + 1e-9)
    assert (db_before - db_censored) >= 20.0, f"Censor drop too small: {db_before:.1f} -> {db_censored:.1f} dB"

    wf = json.loads(wf_json.read_text(encoding="utf-8"))
    assert len(wf["bars"]) >= 200

    verdict = audit_media(
        master,
        beat_sheet_path=ROOT / "projects" / "valorant_edit" / "beat_sheet.json",
        out_png=tm.QA_DIR / "qa_audio_arc.png",
        profile="mograph_sfx",
        has_bgm=True,
    )
    assert verdict["ok"] is True, f"Acoustic failures: {verdict['failures']}"
    assert len(verdict["metrics"]["pocket_checks"]) == 2
    for pk in verdict["metrics"]["pocket_checks"]:
        assert pk["drop_db"] >= 8.0, f"Silence pocket too shallow: {pk}"


def test_optical_effects_and_loupe_preserve_frame_shape():
    import numpy as np
    from projects.valorant_edit import render_gameplay as rg

    dummy = np.full((1920, 1080, 3), 80, dtype=np.uint8)
    for fx in ("motion_tile_whip", "optical_radial_match", "flash_cutout_strobe"):
        out = rg.apply_optical_effect(dummy, fx, 0.5)
        assert out.shape == (1920, 1080, 3) and out.dtype == np.uint8
    src_dummy = np.full((768, 1366, 3), 120, dtype=np.uint8)
    patch, mask = rg.render_loupe_inset(src_dummy, tm.REYNA_SRC_XY, radius_px=tm.LOUPE_RADIUS_PX, zoom_factor=tm.LOUPE_ZOOM_FACTOR)
    d = tm.LOUPE_RADIUS_PX * 2
    assert patch.shape == (d, d, 3) and mask.shape == (d, d)
    assert mask[tm.LOUPE_RADIUS_PX, tm.LOUPE_RADIUS_PX] == 255 and mask[0, 0] == 0


def test_stage_config_copy_safe_zones_and_overlay_contract():
    import json

    cfg_path = tm.export_stage_config()
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    for sub in cfg["subtitles"]:
        assert "\u2014" not in sub["text"] and "\u2013" not in sub["text"]
        assert 1360 <= sub["y_px"] <= 1560
    assert cfg["loupe"]["target_canvas_xy"][0] > cfg["chamber"]["target_canvas_xy"][0]

    html_path = ROOT / "projects" / "valorant_edit" / "overlay_stage.html"
    assert html_path.exists(), f"Missing {html_path}"
    html = html_path.read_text(encoding="utf-8")
    for font_file in ("Oswald-Latin.woff2", "InterTight-Latin.woff2", "InstrumentSerif.ttf", "JetBrainsMono-Latin.woff2"):
        assert font_file in html, f"Missing self-hosted font {font_file}"
    for forbidden in ("<nav", "<header", "<footer", "Segoe UI", "\u2014", "\u2013", "2V4 FLIPPED", "border-top: 3px"):
        assert forbidden not in html, f"Forbidden token in video overlay: {forbidden}"
    assert "2V3 FLIPPED TO 2V1" in html
    gila_sub = next(s for s in cfg["subtitles"] if s["id"] == "sub_gila_to")
    assert gila_sub["y_px"] <= 1370


def test_final_mp4_specs_and_acoustic_gate():
    import json
    import subprocess
    from studio_kit.acoustic_audit import audit_media

    mp4 = tm.FINAL_MP4_PATH
    assert mp4.exists(), f"Missing final MP4: {mp4}"
    probe = json.loads(
        subprocess.check_output(
            [
                str(ROOT / "bin" / "ffprobe.exe"),
                "-v", "error",
                "-show_streams", "-show_format",
                "-of", "json",
                str(mp4),
            ],
            text=True,
        )
    )
    v = next(s for s in probe["streams"] if s["codec_type"] == "video")
    a = next(s for s in probe["streams"] if s["codec_type"] == "audio")
    assert (v["width"], v["height"]) == (1080, 1920)
    assert v["r_frame_rate"] == "60/1"
    assert a["sample_rate"] == "48000" and a["channels"] == 2
    verdict = audit_media(
        mp4,
        beat_sheet_path=ROOT / "projects" / "valorant_edit" / "beat_sheet.json",
        profile="mograph_sfx",
        has_bgm=True,
    )
    assert verdict["ok"] is True, f"Final MP4 acoustic failure: {verdict['failures']}"


def test_v2_anti_slop_zero_cards_and_reels_safe_subtitles():
    import json

    cfg_path = tm.export_v2_stage_config()
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    for sub in cfg["subtitles"]:
        assert "\u2014" not in sub["text"] and "\u2013" not in sub["text"]
        # Strictly above TikTok/Reels/Shorts bottom caption & audio bar danger zone (y<=1340)
        assert 1220 <= sub["y_px"] <= 1340, f"Subtitle too low for Reels/Shorts UI: {sub}"

    html_v2 = ROOT / "projects" / "valorant_edit" / "overlay_stage_v2.html"
    assert html_v2.exists(), f"Missing {html_v2}"
    txt = html_v2.read_text(encoding="utf-8")
    # Ban every AI-slop dashboard card, web telemetry label, and unrequested English stat copy
    for banned in (
        "TARGET: CHAMBER",
        "STRAY HEADSHOT",
        "4.2X",
        "THROUGH ULT",
        "0.40S DOUBLE HS",
        "2V3 FLIPPED",
        "2-4 ATTACK",
        "waveform-dock",
        "kill1-pill",
        "kill3-counter",
        "Segoe UI",
        "<nav",
        "<header",
        "<footer",
    ):
        assert banned not in txt, f"V2 overlay still contains AI-slop card/copy: {banned}"
    for font_file in ("Oswald-Latin.woff2", "InterTight-Latin.woff2", "InstrumentSerif.ttf"):
        assert font_file in txt, f"Missing self-hosted font in V2 overlay: {font_file}"


def test_v2_final_mp4_specs_and_acoustic_gate():
    import json
    import subprocess
    from studio_kit.acoustic_audit import audit_media

    mp4 = tm.FINAL_V2_MP4_PATH
    assert mp4.exists(), f"Missing final V2 MP4: {mp4}"
    probe = json.loads(
        subprocess.check_output(
            [
                str(ROOT / "bin" / "ffprobe.exe"),
                "-v", "error",
                "-show_streams", "-show_format",
                "-of", "json",
                str(mp4),
            ],
            text=True,
        )
    )
    v = next(s for s in probe["streams"] if s["codec_type"] == "video")
    a = next(s for s in probe["streams"] if s["codec_type"] == "audio")
    assert (v["width"], v["height"]) == (1080, 1920)
    assert v["r_frame_rate"] == "60/1"
    assert a["sample_rate"] == "48000" and a["channels"] == 2
    verdict = audit_media(
        mp4,
        beat_sheet_path=ROOT / "projects" / "valorant_edit" / "beat_sheet.json",
        profile="mograph_sfx",
        has_bgm=True,
    )
    assert verdict["ok"] is True, f"V2 Final MP4 acoustic failure: {verdict['failures']}"
