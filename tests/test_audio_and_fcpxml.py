from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from scipy.io import wavfile
import pytest

from studio_core.audio_engine import (
    synthesize_sfx_catalog,
    mix_editorial_audio,
)
from studio_core.fcpxml_builder import (
    build_fcpxml_timeline,
    export_srt,
)


def test_synthesize_sfx_catalog_creates_room_matched_wavs(tmp_path: Path):
    catalog = synthesize_sfx_catalog(str(tmp_path / "sfx"))
    assert "sub_thud" in catalog
    assert "data_lock" in catalog
    assert "camera_whoosh" in catalog
    assert "punch_stinger" in catalog
    for name, wav_path in catalog.items():
        p = Path(wav_path)
        assert p.exists(), f"Missing SFX {name}"
        sr, data = wavfile.read(str(p))
        assert sr == 44100
        assert len(data) > 1000


def test_mix_editorial_audio_enforces_punchline_silence(tmp_path: Path):
    sfx = synthesize_sfx_catalog(str(tmp_path / "sfx"))
    out_wav = tmp_path / "master_mix.wav"
    res_path = mix_editorial_audio(
        duration_sec=3.0,
        events=[{"time_sec": 0.2, "wav_path": sfx["sub_thud"], "gain_db": 0.0}],
        output_wav=str(out_wav),
        punchline_windows=[(1.2, 1.8)],
    )
    assert Path(res_path).exists()
    sr, samples = wavfile.read(res_path)
    # Check that the punchline silence window [1.25s, 1.75s] has zero amplitude
    s_start = int(1.25 * sr)
    s_end = int(1.75 * sr)
    window_slice = samples[s_start:s_end]
    assert np.max(np.abs(window_slice)) == 0, "Punchline silence window was not muted to 0"


def test_build_fcpxml_timeline_and_srt_valid_for_resolve(tmp_path: Path):
    fcpxml_out = tmp_path / "resolve_edit.fcpxml"
    video_clips = [
        {"name": "NCT_Beat_1", "src": "file:///D:/test/mograph.mp4", "start_sec": 0.0, "duration_sec": 4.0, "lane": 0, "scale": 1.0},
        {"name": "NCT_Zoom_Cut", "src": "file:///D:/test/mograph.mp4", "start_sec": 4.0, "duration_sec": 2.0, "lane": 1, "scale": 1.25},
    ]
    audio_clips = [
        {"name": "SFX_Lock", "src": "file:///D:/test/data_lock.wav", "start_sec": 1.0, "duration_sec": 0.4, "lane": -1, "gain_db": 0.0},
    ]
    out_file = build_fcpxml_timeline(
        project_name="NCT_AI_Timeline",
        fps=30,
        width=1920,
        height=1080,
        video_clips=video_clips,
        audio_clips=audio_clips,
        output_path=str(fcpxml_out),
    )
    assert Path(out_file).exists()
    tree = ET.parse(out_file)
    root = tree.getroot()
    assert root.tag == "fcpxml"
    assert root.attrib.get("version") == "1.9"

    # Negative/empty clip validation (Review Focus item)
    with pytest.raises(ValueError):
        build_fcpxml_timeline("Bad", 30, 1920, 1080, [], [], str(tmp_path / "bad.fcpxml"))
    with pytest.raises(ValueError):
        build_fcpxml_timeline(
            "BadTime",
            30,
            1920,
            1080,
            [{"name": "Neg", "src": "a.mp4", "start_sec": -1.0, "duration_sec": 2.0}],
            [],
            str(tmp_path / "bad2.fcpxml"),
        )

    srt_out = tmp_path / "captions.srt"
    export_srt(
        [{"start_sec": 0.0, "end_sec": 2.5, "text": "PT Nalar Cerdas Teknologi"}],
        str(srt_out),
    )
    srt_text = srt_out.read_text(encoding="utf-8")
    assert "00:00:00,000 --> 00:00:02,500" in srt_text
    assert "PT Nalar Cerdas Teknologi" in srt_text
