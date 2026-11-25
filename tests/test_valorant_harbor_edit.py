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
