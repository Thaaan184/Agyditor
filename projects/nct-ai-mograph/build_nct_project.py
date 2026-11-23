"""End-to-end builder for the PT Nalar Cerdas Teknologi (NCT AI) Motion Graphic & DaVinci Resolve Free package."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from studio_core.antislop_gate import audit_antislop_deliverable
from studio_core.audio_engine import mix_editorial_audio, synthesize_sfx_catalog
from studio_core.continuity_probe import probe_video_continuity
from studio_core.fcpxml_builder import build_fcpxml_timeline, export_srt
from studio_core.fusion_lua import (
    generate_kinetic_callout_setting,
    package_drfx,
    validate_fusion_setting,
)
from studio_core.html_renderer import render_seekable_html


def build_nct_ai_project() -> dict:
    project_dir = ROOT / "projects" / "nct-ai-mograph"
    comp_html = project_dir / "composition.html"
    output_dir = project_dir / "output"
    resolve_dir = project_dir / "resolve"
    sfx_dir = project_dir / "sfx"

    output_dir.mkdir(parents=True, exist_ok=True)
    resolve_dir.mkdir(parents=True, exist_ok=True)

    # 1. Synthesize room-matched SFX catalog and master editorial audio
    sfx = synthesize_sfx_catalog(str(sfx_dir))
    events = [
        {"time_sec": 0.10, "wav_path": sfx["sub_thud"], "gain_db": 0.0},
        {"time_sec": 0.85, "wav_path": sfx["camera_whoosh"], "gain_db": -1.5},
        {"time_sec": 2.15, "wav_path": sfx["data_lock"], "gain_db": 1.0},
        {"time_sec": 3.00, "wav_path": sfx["camera_whoosh"], "gain_db": 0.0},
        {"time_sec": 3.35, "wav_path": sfx["data_lock"], "gain_db": 0.0},
        {"time_sec": 3.55, "wav_path": sfx["data_lock"], "gain_db": -1.0},
        {"time_sec": 3.75, "wav_path": sfx["data_lock"], "gain_db": -2.0},
        {"time_sec": 6.20, "wav_path": sfx["sub_thud"], "gain_db": 0.5},
        {"time_sec": 6.55, "wav_path": sfx["data_lock"], "gain_db": 0.0},
        {"time_sec": 9.40, "wav_path": sfx["punch_stinger"], "gain_db": 1.0},
        {"time_sec": 9.75, "wav_path": sfx["data_lock"], "gain_db": 0.0},
    ]
    # Deliberate 150ms silence pocket right before Beat 4 lockup impact (9.25s -> 9.40s)
    master_wav = output_dir / "nct_ai_master_audio.wav"
    mix_editorial_audio(
        duration_sec=12.0,
        events=events,
        output_wav=str(master_wav),
        punchline_windows=[(9.25, 9.39)],
        ambient_bed_gain=0.055,
    )

    # 2. Export verified Indonesian SRT subtitles
    captions = [
        {
            "start_sec": 0.15,
            "end_sec": 2.95,
            "text": "PT Nalar Cerdas Teknologi: Human Answer Detection memangkas waktu tunggu 22 detik menjadi <0.8s.",
        },
        {
            "start_sec": 3.05,
            "end_sec": 6.15,
            "text": "Interkoneksi SIP Trunk langsung: Telkomsel 21ms, XL Axiata 24ms, dan Indosat Ooredoo 26ms.",
        },
        {
            "start_sec": 6.25,
            "end_sec": 9.25,
            "text": "1,240 dari 2,000 kanal paralel aktif di 11 modul CRM eksekutif dan WebRTC Softphone.",
        },
        {
            "start_sec": 9.45,
            "end_sec": 11.90,
            "text": "PT Nalar Cerdas Teknologi (NCT.ai) | Jadwalkan konsultasi arsitektur di pt-nct.ai/contact",
        },
    ]
    srt_path = resolve_dir / "nct_ai_captions.srt"
    export_srt(captions, str(srt_path))

    # 3. Audit Antislop & Antislop-Copywriting gate BEFORE rendering
    html_text = comp_html.read_text(encoding="utf-8")
    srt_text = srt_path.read_text(encoding="utf-8")
    gate = audit_antislop_deliverable(html_text, [srt_text])
    if not gate["passed"]:
        raise RuntimeError(f"Antislop gate failed: {gate['violations']}")

    # 4. Render 1920x1080 30fps MP4 via Playwright Chromium + FFmpeg
    mp4_path = output_dir / "nct_ai_mograph_1080p.mp4"
    render_info = render_seekable_html(
        html_path=str(comp_html),
        output_mp4=str(mp4_path),
        duration_sec=12.0,
        fps=30,
        width=1920,
        height=1080,
        audio_wav=str(master_wav),
    )

    # 5. Probe continuity and generate 4x2 visual QA contact sheet
    sheet_path = output_dir / "contact_sheet.png"
    probe_info = probe_video_continuity(
        mp4_path=str(mp4_path),
        beat_boundaries_sec=[3.0, 6.2, 9.4],
        contact_sheet_path=str(sheet_path),
    )
    if not probe_info["passed"]:
        raise RuntimeError(f"Continuity probe failed: {probe_info}")

    # 6. Generate native DaVinci Resolve Free Fusion Macro (.setting) & Bundle (.drfx)
    setting_lua = generate_kinetic_callout_setting(
        name="NCT_AI_Kinetic_Callout",
        default_text="PT Nalar Cerdas Teknologi // HAD <0.8s // SIP Trunk 21ms",
        accent_rgb=(0.2196, 0.7412, 0.9725),
        duration_frames=360,
    )
    val = validate_fusion_setting(setting_lua)
    if not val["valid"]:
        raise RuntimeError(f"Fusion Lua validation failed: {val['errors']}")

    setting_file = resolve_dir / "NCT_AI_Kinetic_Callout.setting"
    setting_file.write_text(setting_lua, encoding="utf-8")

    drfx_file = resolve_dir / "NCT_AI_Mograph_Pack.drfx"
    package_drfx(
        {"Edit/Titles/NCT_AI_Kinetic_Callout.setting": setting_lua},
        str(drfx_file),
    )

    # 7. Generate multi-track DaVinci Resolve Free Editorial Timeline (.fcpxml)
    video_clips = [
        {
            "name": "NCT_Beat1_HAD_Compression",
            "src": str(mp4_path),
            "start_sec": 0.0,
            "duration_sec": 3.0,
            "lane": 0,
            "scale": 1.0,
        },
        {
            "name": "NCT_Beat2_Carrier_BGP_Matrix",
            "src": str(mp4_path),
            "start_sec": 3.0,
            "duration_sec": 3.2,
            "lane": 0,
            "scale": 1.0,
        },
        {
            "name": "NCT_Beat3_CRM_Wallboard_Zoom",
            "src": str(mp4_path),
            "start_sec": 6.2,
            "duration_sec": 3.2,
            "lane": 0,
            "scale": 1.15,
        },
        {
            "name": "NCT_Beat4_Architecture_Lockup",
            "src": str(mp4_path),
            "start_sec": 9.4,
            "duration_sec": 2.6,
            "lane": 0,
            "scale": 1.0,
        },
    ]
    audio_clips = [
        {"name": "SFX_Sub_Thud_Intro", "src": sfx["sub_thud"], "start_sec": 0.10, "duration_sec": 0.35, "lane": -1, "gain_db": 0.0},
        {"name": "SFX_HAD_Lock", "src": sfx["data_lock"], "start_sec": 2.15, "duration_sec": 0.18, "lane": -1, "gain_db": 1.0},
        {"name": "SFX_BGP_Whoosh", "src": sfx["camera_whoosh"], "start_sec": 3.00, "duration_sec": 0.42, "lane": -1, "gain_db": 0.0},
        {"name": "SFX_CRM_Thud", "src": sfx["sub_thud"], "start_sec": 6.20, "duration_sec": 0.35, "lane": -1, "gain_db": 0.5},
        {"name": "SFX_Lockup_Stinger", "src": sfx["punch_stinger"], "start_sec": 9.40, "duration_sec": 0.45, "lane": -1, "gain_db": 1.0},
        {"name": "Master_Editorial_Mix", "src": str(master_wav), "start_sec": 0.0, "duration_sec": 12.0, "lane": -2, "gain_db": 0.0},
    ]
    fcpxml_path = resolve_dir / "nct_ai_editorial.fcpxml"
    build_fcpxml_timeline(
        project_name="NCT_AI_Enterprise_Mograph",
        fps=30,
        width=1920,
        height=1080,
        video_clips=video_clips,
        audio_clips=audio_clips,
        output_path=str(fcpxml_path),
    )

    return {
        "render": render_info,
        "continuity": probe_info,
        "fcpxml": str(fcpxml_path),
        "drfx": str(drfx_file),
    }


if __name__ == "__main__":
    summary = build_nct_ai_project()
    print("NCT AI Build Summary:", summary)
