from pathlib import Path
import xml.etree.ElementTree as ET
import subprocess

from studio_core.antislop_gate import audit_antislop_deliverable
from studio_core.continuity_probe import probe_video_continuity
from studio_core.fusion_lua import validate_fusion_setting
from studio_core.html_renderer import _resolve_ffmpeg

ROOT = Path(__file__).resolve().parent.parent
PROJECT_DIR = ROOT / "projects" / "nct-ai-mograph"


def test_nct_ai_mograph_full_deliverable():
    comp_html = PROJECT_DIR / "composition.html"
    mp4_out = PROJECT_DIR / "output" / "nct_ai_mograph_1080p.mp4"
    wav_out = PROJECT_DIR / "output" / "nct_ai_master_audio.wav"
    sheet_out = PROJECT_DIR / "output" / "contact_sheet.png"
    fcpxml_out = PROJECT_DIR / "resolve" / "nct_ai_editorial.fcpxml"
    srt_out = PROJECT_DIR / "resolve" / "nct_ai_captions.srt"
    setting_out = PROJECT_DIR / "resolve" / "NCT_AI_Kinetic_Callout.setting"
    drfx_out = PROJECT_DIR / "resolve" / "NCT_AI_Mograph_Pack.drfx"

    for p in (comp_html, mp4_out, wav_out, sheet_out, fcpxml_out, srt_out, setting_out, drfx_out):
        assert p.exists(), f"Missing required deliverable: {p}"

    # 1. Antislop & Antislop-Copywriting gate check
    html_text = comp_html.read_text(encoding="utf-8")
    srt_text = srt_out.read_text(encoding="utf-8")
    gate = audit_antislop_deliverable(html_text, [srt_text])
    assert gate["passed"] is True, f"Antislop violations: {gate['violations']}"

    # Verify authentic NCT AI facts are present in the deliverable
    for fact in ("PT Nalar Cerdas Teknologi", "0.8s", "21ms", "24ms", "26ms", "Telkomsel", "Indosat", "XL Axiata", "pt-nct.ai"):
        assert fact in html_text, f"Missing verified NCT AI fact in HTML composition: {fact}"

    # 2. Verify MP4 video stream and audio stream via ffprobe
    ffprobe_bin = _resolve_ffmpeg("ffprobe")
    probe_cmd = [
        ffprobe_bin,
        "-v",
        "error",
        "-show_entries",
        "stream=codec_type,width,height",
        "-of",
        "default=noprint_wrappers=1",
        str(mp4_out),
    ]
    res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
    assert "codec_type=video" in res.stdout
    assert "codec_type=audio" in res.stdout
    assert "width=1920" in res.stdout
    assert "height=1080" in res.stdout

    # 3. Verify continuity probe passes
    cont = probe_video_continuity(str(mp4_out), beat_boundaries_sec=[3.0, 6.2, 9.4])
    assert cont["passed"] is True, f"Continuity probe failed: {cont}"
    assert cont["carry_score"] >= 0.75

    # 4. Verify DaVinci Resolve Free deliverables (.setting, .drfx, .fcpxml)
    lua_text = setting_out.read_text(encoding="utf-8")
    assert validate_fusion_setting(lua_text)["valid"] is True
    tree = ET.parse(str(fcpxml_out))
    assert tree.getroot().tag == "fcpxml"
