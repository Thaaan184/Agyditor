import importlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent.parent


def _env_with_bin() -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = f"{ROOT / 'bin'};{env.get('PATH', '')}"
    env["HYPERFRAMES_FFMPEG_PATH"] = str(ROOT / "bin" / "ffmpeg.exe")
    env["HYPERFRAMES_FFPROBE_PATH"] = str(ROOT / "bin" / "ffprobe.exe")
    return env


def test_ffmpeg_ffprobe_and_ytdlp_binaries():
    for exe, flag in (("ffmpeg.exe", "-version"), ("ffprobe.exe", "-version"), ("yt-dlp.exe", "--version")):
        bin_path = ROOT / "bin" / exe
        assert bin_path.exists(), f"bin/{exe} missing"
        res = subprocess.run([str(bin_path), flag], capture_output=True, text=True, check=False)
        assert res.returncode == 0, f"{exe} {flag} failed: {res.stderr}"


def test_weftcut_desktop_and_mcp_cli():
    weftcut_cli = ROOT / "bin" / "weftcut.exe"
    assert weftcut_cli.exists(), "bin/weftcut.exe missing"
    ver = subprocess.run([str(weftcut_cli), "--version"], capture_output=True, text=True, check=False)
    assert ver.returncode == 0, f"weftcut --version failed: {ver.stderr}"
    cfg = subprocess.run([str(weftcut_cli), "print-config"], capture_output=True, text=True, check=False)
    assert cfg.returncode == 0, f"weftcut print-config failed: {cfg.stderr}"
    assert "mcp" in cfg.stdout.lower()

    local_app = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "WeftCut" / "WeftCut.exe"
    d_app = ROOT / "tools" / "WeftCut" / "WeftCut.exe"
    assert d_app.exists() or local_app.exists(), "WeftCut.exe desktop app not found"


def test_onetake_official_repo_and_motion_suite():
    onetake_dir = ROOT / ".agents" / "skills" / "onetake"
    for rel in ("SKILL.md", "lib/motion.js", "scripts/render.py", "scripts/sfx_palette.py", "scripts/probe.py", "scripts/test_motion.js"):
        assert (onetake_dir / rel).exists(), f"Missing OneTake file: {rel}"

    res = subprocess.run(
        ["node", str(onetake_dir / "scripts" / "test_motion.js")],
        capture_output=True,
        text=True,
        env=_env_with_bin(),
        check=False,
    )
    assert res.returncode == 0, f"OneTake test_motion.js failed:\n{res.stdout}\n{res.stderr}"
    assert "ALL PASS" in res.stdout


def test_hyperframes_official_cli_and_skills():
    for skill in ("hyperframes", "hyperframes-cli", "hyperframes-registry"):
        assert (ROOT / ".agents" / "skills" / skill / "SKILL.md").exists(), f"Missing HyperFrames skill: {skill}"

    res = subprocess.run(
        "npx hyperframes --version",
        shell=True,
        capture_output=True,
        text=True,
        env=_env_with_bin(),
        check=False,
    )
    assert res.returncode == 0, f"npx hyperframes --version failed: {res.stderr}"
    assert res.stdout.strip() != ""

    doc = subprocess.run(
        "npx hyperframes doctor --json",
        shell=True,
        capture_output=True,
        text=True,
        env=_env_with_bin(),
        check=False,
    )
    assert doc.returncode == 0, f"hyperframes doctor failed: {doc.stderr}"
    payload = json.loads(doc.stdout[doc.stdout.find("{") :])
    checks = {c["name"]: c for c in payload["checks"]}
    assert checks["FFmpeg"]["ok"] is True, checks["FFmpeg"]
    assert checks["FFprobe"]["ok"] is True, checks["FFprobe"]
    assert checks["Chrome"]["ok"] is True, checks["Chrome"]
    assert payload["_meta"].get("skillsOutdated", 0) == 0
    assert payload["_meta"].get("skillsMissing", 0) == 0


def test_kasta_1_video_and_threejs_skills():
    assert (ROOT / ".agents" / "skills" / "ffmpeg-skill" / "SKILL.md").exists()
    assert (ROOT / ".agents" / "skills" / "claude-shorts" / "SKILL.md").exists()

    barty_skills = (
        "explainer-default",
        "explainer-engaging",
        "explainer-high-energy",
        "motion-broll",
        "object-separation",
        "sound-effects",
    )
    for skill in barty_skills:
        p = ROOT / ".agents" / "skills" / skill / "SKILL.md"
        assert p.exists(), f"Missing Barty-Bart skill: {skill}"
        assert p.read_text(encoding="utf-8").startswith("---"), f"Missing frontmatter in {skill}"

    threejs_skills = (
        "threejs-animation",
        "threejs-asset-pipeline",
        "threejs-fundamentals",
        "threejs-geometry",
        "threejs-interaction",
        "threejs-lighting",
        "threejs-loaders",
        "threejs-materials",
        "threejs-performance",
        "threejs-postprocessing",
        "threejs-react-three-fiber",
        "threejs-shaders",
        "threejs-textures",
    )
    for skill in threejs_skills:
        p = ROOT / ".agents" / "skills" / skill / "SKILL.md"
        assert p.exists(), f"Missing Three.js skill: {skill}"


def test_kasta_2_adapted_skills_for_windows_and_free_audio():
    ghost = (ROOT / ".agents" / "skills" / "ghost-editor" / "SKILL.md").read_text(encoding="utf-8")
    assert "Windows & Option A Local Studio Adaptation" in ghost
    assert "bin/ffmpeg.exe" in ghost
    assert "faster-whisper" in ghost

    mvd = (ROOT / ".agents" / "skills" / "motion-video-director" / "SKILL.md").read_text(encoding="utf-8")
    assert "Windows & 100% Free Local Audio Adaptation" in mvd
    assert "NO Paid ElevenLabs" in mvd
    assert "faster-whisper" in mvd


def test_weftcut_and_custom_skills_present():
    driving = ROOT / ".agents" / "skills" / "driving-weftcut"
    assert (driving / "SKILL.md").exists()
    assert (driving / "references" / "mcp.md").exists()
    assert (driving / "references" / "motif-authoring.md").exists()
    assert (ROOT / ".agents" / "skills" / "editing-gaming-clips" / "SKILL.md").exists()
    assert (ROOT / ".agents" / "skills" / "managing-video-brand" / "SKILL.md").exists()
    directing = ROOT / ".agents" / "skills" / "directing-agy-video"
    assert (directing / "SKILL.md").exists()
    assert (directing / "references" / "studio-catalog.md").exists()
    dir_txt = (directing / "SKILL.md").read_text(encoding="utf-8")
    assert dir_txt.startswith("---") and "name: directing-agy-video" in dir_txt
    assert "Mode A" in dir_txt and "Mode B" in dir_txt


def test_python_audio_and_vision_dependencies():
    for mod in ("numpy", "scipy", "PIL", "matplotlib", "fontTools", "brotli", "cv2", "playwright", "faster_whisper", "librosa"):
        assert importlib.import_module(mod) is not None


def test_authored_studio_files_antislop_clean():
    authored_paths = (
        "README.md",
        "GEMINI.md",
        "DESIGN.md",
        ".agents/skills/managing-video-brand/SKILL.md",
        ".agents/skills/managing-video-brand/resources/video-design-tokens.json",
        ".agents/skills/managing-video-brand/resources/style-profiles.md",
        ".agents/skills/driving-weftcut/SKILL.md",
        ".agents/skills/editing-gaming-clips/SKILL.md",
        ".agents/skills/directing-agy-video/SKILL.md",
        ".agents/skills/directing-agy-video/references/studio-catalog.md",
        "studio_kit/motion_primitives.js",
        "studio_kit/keyframe_rig.js",
        "studio_kit/optical_stage.js",
        "studio_kit/occlusion_cutout.py",
        "studio_kit/demo_showcase.html",
        "studio_kit/render_showcase.py",
        "studio_kit/demo_showcase_v2.html",
        "studio_kit/render_showcase_v2.py",
        "references/transitions_study/TRANSITIONS_GUIDE.md",
        "references/transitions_study_v2/TRANSITIONS_V2_GUIDE.md",
        "references/text_motion_study/TEXT_MOTION_GUIDE.md",
        "references/depth_optical_study/DEPTH_OPTICS_ARCHITECTURE.md",
        "references/sound_cinematography_study/SOUND_CINEMA_ARCHITECTURE.md",
        "references/editorial_classup_study/EDITORIAL_CLASSUP_GUIDE.md",
        "references/narrative_typography_study/NARRATIVE_TYPOGRAPHY_SAFEZONE_GUIDE.md",
        "studio_kit/build_sound_index.py",
        "studio_kit/beat_sheet.py",
        "studio_kit/acoustic_audit.py",
        "studio_kit/sound_engine.py",
        "studio_kit/context_router.py",
        "studio_kit/color_grade.py",
        "studio_kit/safe_zones.py",
        "studio_kit/tactile_scene_kit.html",
        "studio_kit/narrative_composer.py",
        "studio_kit/narrative_showcase_beat_sheet.json",
    )
    for rel in authored_paths:
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "\u2014" not in text, f"Forbidden em dash in {rel}"
        assert "\u2013" not in text, f"Forbidden en dash in {rel}"

    gemini_text = (ROOT / "GEMINI.md").read_text(encoding="utf-8")
    design_text = (ROOT / "DESIGN.md").read_text(encoding="utf-8")
    for text in (gemini_text, design_text):
        for tool in ("WeftCut", "HyperFrames", "OneTake", "Three.js", "ghost-editor", "motion-video-director", "studio_kit"):
            assert tool in text, f"Missing {tool} reference"

    tokens = json.loads(
        (ROOT / ".agents" / "skills" / "managing-video-brand" / "resources" / "video-design-tokens.json").read_text(
            encoding="utf-8"
        )
    )
    assert "Segoe UI" not in json.dumps(tokens), "Unbundled Segoe UI fallback must not appear in video tokens"
    for family, rel_font in tokens["typography"]["local_font_files"].items():
        font_path = ROOT / rel_font
        assert font_path.exists() and font_path.stat().st_size > 1000, f"Missing bundled font {family}: {rel_font}"


def test_studio_kit_primitives_and_sfx():
    sfx_dir = ROOT / "studio_kit" / "sfx"
    for name in ("click.ogg", "impact.ogg", "pop.ogg", "riser.ogg", "tick.ogg", "whoosh.ogg"):
        assert (sfx_dir / name).exists(), f"Missing studio SFX: {name}"

    res = subprocess.run(
        [
            "node",
            "-e",
            (
                "const m = require('./studio_kit/motion_primitives.js');"
                "if (Math.abs(m.CURVES.appleOut(1) - 1) > 1e-5) throw new Error('appleOut');"
                "if (m.spring(0, {from:-100, to:0}) !== -100) throw new Error('spring');"
                "if (m.appleFollowerChar(0.0, 0, 0).blurPx < 5) throw new Error('appleFollower');"
                "if (m.ghostEchoPair(0.1, 0).ghost.opacity <= 0) throw new Error('ghostEcho');"
                "if (!m.rollingSlotColumn(1.2, 0, 0).settled) throw new Error('rollingSlot');"
                "if (m.spatial3DCameraWord(0, -400, {focalZ:0}).dofBlurPx <= 0) throw new Error('spatial3D');"
                "if (!m.foregroundOcclusionWipe(0.2, 0).clipPathPolygon.includes('polygon')) throw new Error('wipe');"
                "if (m.smoothMaskReveal(0.25, 0).edgeBlurPx <= 0) throw new Error('smoothMask');"
                "if (!m.angledSplitZoom(0.12, 0).clipPolygon.includes('polygon')) throw new Error('splitZoom');"
                "const sc = m.splitSCurveHandoff(1.05, 1.0, {durOutS:0.24, durInS:0.34}); if (sc.outgoing.opacity !== 0 || sc.incoming.opacity <= 0) throw new Error('splitS');"
                "const ac = m.asymmetricCaptionLayout(['OKAY', 'GUYS SO', 'THIS'], 1); if (ac[1].tier !== 'hero' || ac[1].scale <= 1.2) throw new Error('asym');"
                "if (m.matchCutSplitWipe(0.5, 0, {durationS:0.36}).splitPct < 49) throw new Error('matchSplit');"
                "const c2d = m.camera2DTypographyState(0.95, [{t:0,x:0,y:0,zoom:1},{t:1.0,x:200,y:80,zoom:1.3}], {preBeatLeadS:0.083, transitionS:0.28}); if (c2d.stopIndex !== 1 || c2d.camX <= 0) throw new Error('cam2d');"
                "const ncw = m.narrativeClusterWord(1.15, 1.0); if (!ncw.visible || ncw.opacity <= 0.5) throw new Error('clusterWord');"
                "const gts = m.goldenTypeScale(16); if (gts.bodyPx !== 16 || gts.headlinePx < 40 || gts.gridUnitPx !== 8) throw new Error('goldenScale');"
            ),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, f"studio_kit/motion_primitives.js test failed: {res.stderr}"


def test_starter_motifs_contract_and_self_contained():
    motifs_root = ROOT / "studio_kit" / "motifs"
    expected = (
        "apple-follower-reveal",
        "ghost-echo-kinetic",
        "rolling-cylinder-slot",
        "kinetic-3d-spatial",
        "cylinder-3d-orbit",
        "signature-glow-trim",
    )
    root_primitives = (ROOT / "studio_kit" / "motion_primitives.js").read_text(encoding="utf-8")
    root_rig = (ROOT / "studio_kit" / "keyframe_rig.js").read_text(encoding="utf-8")
    root_optics = (ROOT / "studio_kit" / "optical_stage.js").read_text(encoding="utf-8")
    three_bundle = ROOT / "studio_kit" / "vendor" / "three_optical.bundle.js"
    assert three_bundle.exists() and three_bundle.stat().st_size > 200_000, "Missing offline three_optical.bundle.js"
    assert "cdn.jsdelivr.net" not in three_bundle.read_text(encoding="utf-8"), "CDN URL leaked in three_optical.bundle.js"

    allowed_prop_types = {"string", "color", "number", "enum", "media"}

    for name in expected:
        mdir = motifs_root / name
        manifest_path = mdir / "manifest.json"
        index_path = mdir / "index.html"
        assert manifest_path.exists() and index_path.exists(), f"Missing Motif files for {name}"

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest.get("name"), f"Empty Motif name in {name}"
        size = manifest.get("size")
        assert isinstance(size, list) and len(size) == 2 and all(1 <= s <= 8192 for s in size), f"Bad size in {name}"
        assert manifest.get("default_duration_s", 0) >= 3.0, f"Title/overlay hold too short in {name}"
        for rel_font in manifest.get("fonts", []):
            assert (mdir / rel_font).exists(), f"Missing bundled Motif font {rel_font} in {name}"
        for prop_key, spec in manifest.get("props_schema", {}).items():
            assert spec.get("type") in allowed_prop_types, f"Invalid prop type {prop_key} in {name}"
            assert "default" in spec, f"Missing default for {prop_key} in {name}"

        html = index_path.read_text(encoding="utf-8")
        assert "motif.define" in html, f"Missing motif.define in {name}"
        assert "document.fonts.load" in html, f"Missing explicit document.fonts.load in {name}"
        assert "background: transparent" in html, f"Motif canvas must default transparent in {name}"
        assert "\u2014" not in html and "\u2013" not in html, f"Forbidden dash in {name}"
        ext_urls = [u for u in re.findall(r"https?://[^\s\"'<>]+", html) if u != "http://www.w3.org/2000/svg"]
        assert not ext_urls, f"Forbidden external URLs {ext_urls} in {name}"
        for bad in ("<nav", "<header", "<button", "Segoe UI"):
            assert bad not in html, f"Forbidden web/external pattern '{bad}' in {name}"

        assert (mdir / "motion_primitives.js").read_text(encoding="utf-8") == root_primitives, (
            f"motion_primitives.js drifted in {name}"
        )
        if (mdir / "keyframe_rig.js").exists():
            assert (mdir / "keyframe_rig.js").read_text(encoding="utf-8") == root_rig, (
                f"keyframe_rig.js drifted in {name}"
            )
        if (mdir / "optical_stage.js").exists():
            assert (mdir / "optical_stage.js").read_text(encoding="utf-8") == root_optics, (
                f"optical_stage.js drifted in {name}"
            )


def test_v2_keyframe_rig_optics_and_occlusion_tools():
    res = subprocess.run(
        [
            "node",
            "-e",
            (
                "const rig = require('./studio_kit/keyframe_rig.js');"
                "const opt = require('./studio_kit/optical_stage.js');"
                "const cam = rig.resolveCameraState({ positionTrack: [{u:0,v:[0,0,7],ease:'aeWhipOut'},{u:1,v:[0,0,3.5]}], focalLengthMm: 35, aperturePx: 64 }, 0.5, 2.0, 9/16);"
                "const p1 = rig.projectWorldToScreen([0, 0, 1.0], cam, 1080, 1920);"
                "if (!p1.visible || p1.scale <= 0) throw new Error('projection');"
                "if (Math.abs(rig.solveDollyZoomFov(4, 40, 2) - 70.96) > 1.5) throw new Error('dolly');"
                "if (rig.evalTrack(rig.popOvershootTrack(0, 0.34, 1.06), 0.23, 1.0) <= 1.02) throw new Error('pop');"
                "if (!rig.flashStrobeEval(0.02, 0, 0.32, 3).active) throw new Error('flash');"
                "if (rig.toWeftCutLayerPlan({foregroundCutout:'a.png',transitionAdjustment:'MotionTileWhip'}).length !== 4) throw new Error('sandwich');"
                "if (!opt.MotionTileWhipShader.fragmentShader.includes('uMirrorEdges')) throw new Error('mt');"
                "if (!opt.OpticalRadialMatchShader.fragmentShader.includes('uChromatic')) throw new Error('radial');"
                "if (!opt.FlashCutoutStrobeShader.fragmentShader.includes('uInvertMix')) throw new Error('strobe');"
            ),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, f"v2 rig/optics Node test failed: {res.stderr}"
    assert importlib.import_module("rembg") is not None


def test_baseline_showcase_render_artifacts():
    ffprobe = ROOT / "bin" / "ffprobe.exe"
    for fname, sheet_name, min_dur in (
        ("baseline_showcase.mp4", "showcase_sheet.jpg", 8.0),
        ("showcase_v2_depth_optics.mp4", "showcase_v2_sheet.jpg", 8.5),
    ):
        mp4 = ROOT / "studio_kit" / "renders" / fname
        sheet = ROOT / "studio_kit" / "renders" / sheet_name
        assert mp4.exists() and mp4.stat().st_size > 100_000, f"Missing rendered {fname}"
        assert sheet.exists() and sheet.stat().st_size > 20_000, f"Missing sheet {sheet_name}"

        probe = subprocess.run(
            [
                str(ffprobe),
                "-v",
                "error",
                "-show_entries",
                "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate",
                "-of",
                "json",
                str(mp4),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(probe.stdout)
        streams = {s["codec_type"]: s for s in data["streams"]}
        assert streams["video"]["width"] == 1080
        assert streams["video"]["height"] == 1920
        assert streams["video"]["r_frame_rate"] == "60/1"
        assert streams["audio"]["codec_name"] == "aac"
        assert float(data["format"]["duration"]) >= min_dur


def test_v3_sound_palette_index_and_zero_waste_beat_sheet():
    import sys

    sys.path.insert(0, str(ROOT / "studio_kit"))
    import beat_sheet

    idx_path = ROOT / "studio_kit" / "sound_palette_index.json"
    assert idx_path.exists(), "Missing studio_kit/sound_palette_index.json"
    idx = json.loads(idx_path.read_text(encoding="utf-8"))
    assert idx["total_assets"] >= 145
    assert idx["by_spectrum_role"]["room_bed"] >= 3
    assert idx["by_spectrum_role"]["sub_low"] >= 10
    assert idx["by_spectrum_role"]["high_air"] >= 10

    nar_sheet = beat_sheet.validate_beat_sheet_file(ROOT / "studio_kit" / "narrative_showcase_beat_sheet.json")
    assert nar_sheet["ok"] is True, nar_sheet
    assert nar_sheet["metrics"]["shot_cv"] >= 0.25
    assert nar_sheet["metrics"]["causal_sfx_count"] >= 5

    bad_sheet = {
        "title": "Bad Test",
        "profile": "narrative-film",
        "sound_palette": "organic-cinema",
        "beats": [
            {
                "id": "b1",
                "t_start": 0.0,
                "t_end": 4.0,
                "shot_type": "b_roll",
                "visual_subject": "Floating amber prism on cyberpunk grid",
                "narrative_purpose": "Valid visual beat purpose here",
                "audio_intent": {"strategy": "dry"},
            },
            {
                "id": "b2",
                "t_start": 4.0,
                "t_end": 8.0,
                "shot_type": "kinetic_card",
                "narrative_purpose": "Missing visual subject on beat two",
                "audio_intent": {"strategy": "dry"},
            },
            {
                "id": "b3",
                "t_start": 8.0,
                "t_end": 12.0,
                "shot_type": "kinetic_card",
                "visual_subject": "Real desk typing footage closeup",
                "narrative_purpose": "Closing beat without dynamic rest",
                "audio_intent": {"strategy": "dry"},
            },
        ],
        "silence_pockets": [],
        "sound_cues": [{"id": "c1", "intensity": "hero", "raw_sine": True, "layers": []}],
    }
    res = beat_sheet.validate_beat_sheet(bad_sheet)
    assert res["ok"] is False
    joined = "\n".join(res["errors"])
    assert "broll_justification" in joined
    assert "abstract placeholder" in joined
    assert "visual_subject" in joined
    assert "raw sine" in joined
    assert "visual_cause" in joined
    assert "hero cue" in joined

    monotony_sheet = {
        "title": "Monotony Check",
        "profile": "narrative-film",
        "sound_palette": "organic-cinema",
        "beats": [
            {
                "id": f"m{i}",
                "t_start": float(i * 2),
                "t_end": float((i + 1) * 2),
                "shot_type": "kinetic_card",
                "visual_subject": f"Tactile craft card number {i}",
                "narrative_purpose": "Repeating card without rhythm change.",
                "on_screen_copy": "This is effortless not just fast, it's magic.",
                "audio_intent": {"strategy": "dry"},
            }
            for i in range(4)
        ],
        "silence_pockets": [{"t0": 3.0, "t1": 3.5}],
        "sound_cues": [],
    }
    mres = beat_sheet.validate_beat_sheet(monotony_sheet)
    assert mres["ok"] is False
    mjoined = "\n".join(mres["errors"])
    assert "monotony" in mjoined.lower()
    assert "effortless" in mjoined.lower()
    assert any("negative parallelism" in w.lower() for w in mres["warnings"])


def test_v3_sound_engine_carving_and_hall_tail(tmp_path):
    import sys

    import numpy as np
    import soundfile as sf

    sys.path.insert(0, str(ROOT / "studio_kit"))
    import sound_engine

    # Extract real 2.2s human voice clip from bundled ffmpeg-skill demo video
    vo_clip = tmp_path / "vo_sample.wav"
    ffmpeg = str(ROOT / "bin" / "ffmpeg.exe")
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-v",
            "error",
            "-t",
            "2.2",
            "-i",
            str(ROOT / ".agents" / "skills" / "ffmpeg-skill" / "demos" / "footage" / "veo_talk_en.mp4"),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "48000",
            str(vo_clip),
        ],
        check=True,
    )

    eng = sound_engine.SoundEngine5Stem(dur_s=4.5, profile="editorial-clean")
    eng.add_room_tone("se/ambience__fs-329569-roomtone-bedroom-yew", gain_db=-34.0)
    eng.add_voice(vo_clip, start_s=0.35)
    eng.add_music_bed(
        segments=[{"start_s": 0.0, "end_s": 3.4, "src_offset_s": 0.0, "lead_in_reverse": False, "hall_tail": True}],
        gain_db=-16.0,
        loop_end_rise_s=0.6,
    )
    eng.add_silence_pocket(3.45, 3.95, fade_ms=25.0)
    eng.add_layered_transition(t_s=2.45, pre_lap_ms=100.0)
    plan = eng.render_mix(tmp_path / "out_stems", target_lufs=-16.0, export_stems=True)

    assert Path(plan["master_wav"]).exists()
    for sname in ("stem_voice.wav", "stem_ambience.wav", "stem_foley.wav", "stem_transitions.wav", "stem_music.wav"):
        assert Path(plan["stems"][sname]).exists()

    # Confirm 9-band voice carving actually attenuated music mid pocket during speech vs silence
    mus, _ = sf.read(plan["stems"]["stem_music.wav"], dtype="float64")
    active_rms = float(np.sqrt(np.mean(mus[int(0.6 * 48000) : int(2.2 * 48000)] ** 2)))
    assert active_rms > 0.0
    pocket_rms = float(np.sqrt(np.mean(mus[int(3.55 * 48000) : int(3.85 * 48000)] ** 2)))
    assert pocket_rms < active_rms * 0.25


def test_declarative_composer_music_dip_and_overlay_plan(tmp_path):
    import sys

    import numpy as np
    import soundfile as sf

    sys.path.insert(0, str(ROOT / "studio_kit"))
    import narrative_composer

    custom_sheet = {
        "title": "Custom Project",
        "profile": "narrative-film",
        "sound_palette": "organic-cinema",
        "duration_s": 4.0,
        "bpm": 100.0,
        "beats": [
            {
                "id": "c1",
                "t_start": 0.0,
                "t_end": 1.6,
                "shot_type": "visual_proof",
                "visual_subject": "Harbor city dusk footage",
                "narrative_purpose": "Establish setting cleanly.",
                "audio_intent": {"strategy": "ambience"},
            },
            {
                "id": "c2",
                "t_start": 1.6,
                "t_end": 4.0,
                "shot_type": "tactile_diagram",
                "visual_subject": "Craft cutting mat cards",
                "narrative_purpose": "Explain cut structure.",
                "audio_intent": {"strategy": "music dip"},
            },
        ],
        "silence_pockets": [],
        "sound_cues": [
            {
                "id": "room",
                "bus": "ambience",
                "contrast_rule": "room_tone_bed",
                "layers": [{"asset": "se/ambience__fs-426767-apartment-room-tone-wav", "spectrum_role": "room_bed"}],
            }
        ],
        "music_plan": {
            "enabled": True,
            "gain_db": -16.0,
            "dips": [{"t0": 2.2, "t1": 3.4, "db": -12.0, "fade_ms": 120.0}],
        },
        "overlays": {
            "wave_badges": [{"t0": 0.2, "t1": 1.2, "label": "Custom Wave", "bus": "ambience"}],
            "music_dip_ui": {"t0": 2.0, "t1": 3.8, "sample_t0": 1.6, "sample_t1": 3.9},
        },
    }
    plan, ov = narrative_composer.build_narrative_audio(custom_sheet, tmp_path / "custom_audio")
    assert Path(plan["master_wav"]).exists()
    assert ov["waveBadges"][0]["label"] == "Custom Wave"
    assert len(ov["waveBadges"][0]["bars"]) == 28
    assert len(ov["musicDipUi"]["bars"]) == 48

    mus, _ = sf.read(plan["stems"]["stem_music.wav"], dtype="float64")
    pre_dip = float(np.sqrt(np.mean(mus[int(0.5 * 48000) : int(1.4 * 48000)] ** 2)))
    in_dip = float(np.sqrt(np.mean(mus[int(2.45 * 48000) : int(3.15 * 48000)] ** 2)))
    assert in_dip < pre_dip * 0.40


def test_v3_acoustic_audit_catches_v2_mud_and_passes_narrative_dual_aspect():
    import sys

    sys.path.insert(0, str(ROOT / "studio_kit"))
    import acoustic_audit

    v2_res = acoustic_audit.audit_media(
        ROOT / "studio_kit" / "renders" / "showcase_v2_depth_optics.mp4",
        profile="mograph_sfx",
    )
    assert v2_res["ok"] is False
    v2_fail_text = " ".join(v2_res["failures"])
    assert "mud" in v2_fail_text.lower()
    assert "clarity & air" in v2_fail_text.lower()

    ffprobe = ROOT / "bin" / "ffprobe.exe"
    beat_path = ROOT / "studio_kit" / "narrative_showcase_beat_sheet.json"
    for stem, exp_w, exp_h in (
        ("narrative_cinema_16x9", 1920, 1080),
        ("narrative_shorts_9x16", 1080, 1920),
    ):
        mp4 = ROOT / "studio_kit" / "renders" / f"{stem}.mp4"
        sheet = ROOT / "studio_kit" / "renders" / f"{stem}_sheet.jpg"
        arc = ROOT / "studio_kit" / "renders" / f"{stem}_audio_arc.png"
        assert mp4.exists() and mp4.stat().st_size > 200_000, f"Missing {mp4}"
        assert sheet.exists() and sheet.stat().st_size > 20_000, f"Missing {sheet}"
        assert arc.exists() and arc.stat().st_size > 20_000, f"Missing {arc}"

        probe = subprocess.run(
            [
                str(ffprobe), "-v", "error",
                "-show_entries", "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate",
                "-of", "json", str(mp4),
            ],
            capture_output=True, text=True, check=True,
        )
        pdata = json.loads(probe.stdout)
        streams = {s["codec_type"]: s for s in pdata["streams"]}
        assert streams["video"]["width"] == exp_w
        assert streams["video"]["height"] == exp_h
        assert streams["video"]["r_frame_rate"] == "30/1"
        assert streams["audio"]["codec_name"] == "aac"
        assert float(pdata["format"]["duration"]) >= 22.0

        aud = acoustic_audit.audit_media(
            mp4,
            beat_sheet_path=beat_path,
            profile="narrative_voice_film",
            has_bgm=True,
        )
        assert aud["ok"] is True, aud
        assert aud["metrics"]["band_pct"]["mud_100_350"] <= 48.0
        assert aud["metrics"]["band_pct"]["voice_350_2500"] >= 18.0
        assert aud["metrics"]["detail_air_pct"] >= 2.5
        assert aud["metrics"]["dynamics"]["dead_digital_zero_pct"] <= 28.0
        assert aud["metrics"]["pocket_checks"][0]["drop_db"] >= 8.0


def test_v4_editorial_classup_router_luts_tonal_sfx_and_flow(tmp_path):
    import sys

    import numpy as np
    import soundfile as sf

    sys.path.insert(0, str(ROOT / "studio_kit"))
    import acoustic_audit
    import beat_sheet
    import color_grade
    import context_router
    import sound_engine

    # 1. Context Router auto-selects distinct editorial profiles
    assert context_router.route_context("cinematic documentary essay")["profile"] == "cinematic-essay"
    assert context_router.route_context("podcast collage short clip")["profile"] == "podcast-collage-short"
    assert context_router.route_context("youtube breakdown tutorial")["profile"] == "creator-editorial"
    assert context_router.route_context("kinetic reels typography captions")["profile"] == "kinetic-reel-typography"
    for prof in ("cinematic_essay", "podcast_collage_short", "narrative_voice_film", "mograph_sfx"):
        assert prof in acoustic_audit.PROFILE_THRESHOLDS

    # 2. Color Grading 3D .cube LUTs + HSV Ch-2 Density + Halation filtergraph + visual proof sheets
    for preset in ("luda_filmic_warm", "gaku_filmic_teal", "editorial_tungsten_clean", "collage_punch_clean", "neutral_rec709"):
        lut = ROOT / "studio_kit" / "luts" / f"{preset}.cube"
        assert lut.exists() and lut.stat().st_size > 200_000, f"Missing LUT {lut}"
    # Verify lifted blacks & cool cyan-teal split + planar gbrp halation filtergraph
    black_out = color_grade.apply_grade_array(np.array([[[0.0, 0.0, 0.0]]]), "luda_filmic_warm")
    assert float(black_out.mean()) > 0.015 and black_out[0, 0, 2] > black_out[0, 0, 0], "Expected lifted cool black floor"
    chain = color_grade.build_ffmpeg_grade_chain("gaku_filmic_teal", in_label="a", out_label="b")
    assert "lut3d=" in chain and "format=gbrp" in chain and "blend=all_mode=screen" in chain
    assert (ROOT / "studio_kit" / "renders" / "color_grade_proof_sheet.jpg").exists()
    assert (ROOT / "studio_kit" / "renders" / "editorial_styles_proof_sheet.jpg").exists()

    # 3. 24 Free Multiply Sound Tonal SFX indexed + automatic librosa musical key matching + EQ filter sweep
    idx = json.loads((ROOT / "studio_kit" / "sound_palette_index.json").read_text(encoding="utf-8"))
    assert idx["total_assets"] >= 173
    assert idx["by_pack"]["multiply-sound-tonal"] == 24

    eng = sound_engine.SoundEngine5Stem(dur_s=4.5, profile="organic-cinema")
    eng.add_music_bed(None, gain_db=-18.0, root_hz=146.83, bpm=100.0)
    assert eng.active_music_key in ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
    picked = eng.add_tonal_sfx("tonal_hit", t_s=1.8, auto_match_music=True, gain_db=-8.0, max_dur_s=1.8)
    assert picked.startswith("tonal/")
    eng.add_filter_sweep("music", t0=0.2, t1=1.4, sweep_type="lowpass_open", f_start=320.0, f_end=14000.0)
    plan = eng.render_mix(tmp_path / "tonal_test", target_lufs=-16.0, export_stems=True)
    assert Path(plan["master_wav"]).exists()
    tr_sig, _ = sf.read(plan["stems"]["stem_transitions.wav"], dtype="float64")
    assert float(np.max(np.abs(tr_sig))) > 0.01

    # 4. Flow-of-Motion collision & Transition Restraint warnings in beat_sheet.py
    flow_sheet = {
        "title": "Flow Check",
        "profile": "creator-editorial",
        "sound_palette": "organic-cinema",
        "beats": [
            {
                "id": f"f{i}",
                "t_start": float(i * (1.2 if i % 2 == 0 else 2.2)),
                "t_end": float(i * (1.2 if i % 2 == 0 else 2.2) + (1.0 if i % 2 == 0 else 2.0)),
                "shot_type": "visual_proof",
                "visual_subject": f"Real street clip {i}",
                "narrative_purpose": "Demonstrate flow warning cleanly.",
                "motion_vector": "pan_left" if i % 2 == 0 else "pan_right",
                "transition_in": "dissolve",
                "audio_intent": {"strategy": "ambience"},
            }
            for i in range(5)
        ],
        "silence_pockets": [{"t0": 2.0, "t1": 2.4}],
        "sound_cues": [],
    }
    fres = beat_sheet.validate_beat_sheet(flow_sheet)
    wjoined = "\n".join(fres["warnings"]).lower()
    assert "flow-of-motion clash" in wjoined
    assert "transition restraint" in wjoined


def test_v5_safe_zones_and_narrative_typography_engines():
    import sys
    from playwright.sync_api import sync_playwright

    sys.path.insert(0, str(ROOT / "studio_kit"))
    import beat_sheet
    import safe_zones

    # 1. Unit checks for Universal Vertical Safe Zone collision guard
    bottom_bad = safe_zones.check_rect_against_platform(
        {"x": 120, "y": 1650, "width": 700, "height": 110},
        1080,
        1920,
        platform="universal_vertical",
    )
    assert bottom_bad["safe"] is False
    assert any(v["zone"] == "bottom_caption_ui" for v in bottom_bad["violations"])

    right_bad = safe_zones.check_rect_against_platform(
        {"x": 910, "y": 960, "width": 140, "height": 120},
        1080,
        1920,
        platform="universal_vertical",
    )
    assert right_bad["safe"] is False
    assert any(v["zone"] == "right_action_buttons" for v in right_bad["violations"])

    chest_ok = safe_zones.check_rect_against_platform(
        {"x": 100, "y": 940, "width": 720, "height": 180},
        1080,
        1920,
        platform="universal_vertical",
    )
    assert chest_ok["safe"] is True, chest_ok

    # 2. Live Playwright DOM bounding-box audit across BOTH 9:16 and 16:9 engines
    kit_url = (ROOT / "studio_kit" / "tactile_scene_kit.html").resolve().as_uri()
    plan_9x16 = {
        "aspect": "9x16",
        "narrativeClusters": [
            {
                "t0": 0.0,
                "t1": 2.0,
                "topPct": 50,
                "words": [
                    {"w": "kata", "role": "connector", "t0": 0.0},
                    {"w": "KUNCI", "role": "brush_red", "t0": 0.2},
                    {"w": "AMAN", "role": "oval_red", "t0": 0.4},
                ],
            }
        ],
        "maciekCaptions": [{"t0": 2.0, "t1": 4.0, "lead": "STAY", "hero": "SAFE", "tail": "ABOVE 30%"}],
        "ludaLetterbox": {
            "t0": 4.0,
            "t1": 6.0,
            "actHtml": "ACT I",
            "captions": [{"t0": 4.0, "t1": 6.0, "html": "Quiet frame"}],
        },
        "abTags": [{"t0": 4.0, "t1": 6.0, "label": "SAFE CHECK", "style": "full"}],
    }
    plan_16x9 = {
        "aspect": "16x9",
        "explainerDiagrams": [
            {"t0": 0.0, "t1": 2.0, "mode": "anatomy_ruler", "headlineHtml": "Golden <em>Scale</em>", "bodyText": "Clean grid."},
            {
                "t0": 2.0,
                "t1": 4.0,
                "mode": "flanking_word_field",
                "leftWords": [{"text": "LEFT", "t0": 2.1}],
                "rightWords": [{"text": "RIGHT", "t0": 2.2}],
            },
            {"t0": 4.0, "t1": 6.0, "mode": "chapter_slam", "theme": "crimson", "kicker": "CH 01", "headlineHtml": "SHOW"},
        ],
    }
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            channel="chrome",
            headless=True,
            args=["--use-gl=angle", "--use-angle=d3d11", "--enable-webgl", "--ignore-gpu-blocklist"],
        )
        c9 = browser.new_context(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
        p9 = c9.new_page()
        p9.goto(kit_url, wait_until="load")
        p9.evaluate("() => document.fonts.ready")
        p9.evaluate("(cfg) => window.__setPlan(cfg)", plan_9x16)
        aud9 = safe_zones.audit_html_safe_zones(p9, [1.0, 3.0, 5.0], width=1080, height=1920, platform="universal_vertical")
        assert aud9["ok"] is True and aud9["checked_elements"] >= 5, aud9
        c9.close()

        c16 = browser.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        p16 = c16.new_page()
        p16.goto(kit_url, wait_until="load")
        p16.evaluate("() => document.fonts.ready")
        p16.evaluate("(cfg) => window.__setPlan(cfg)", plan_16x9)
        aud16 = safe_zones.audit_html_safe_zones(p16, [1.0, 3.0, 5.0], width=1920, height=1080, platform="youtube_16x9")
        assert aud16["ok"] is True and aud16["checked_elements"] >= 3, aud16
        c16.close()
        browser.close()

    # 3. Context-aware narrative emphasis balance (no false alarm on cinematic-essay; catches flat streak & >60% overuse)
    def _make_text_sheet(profile: str, emph_list: list[str] | None = None) -> dict:
        return {
            "title": "Typo Balance Test",
            "profile": profile,
            "target_platform": "universal_vertical",
            "sound_palette": "organic-cinema",
            "beats": [
                {
                    "id": f"tb{i}",
                    "t_start": float(i * 2.0),
                    "t_end": float(i * 2.0 + (1.4 if i % 2 == 0 else 2.6)),
                    "shot_type": "visual_proof",
                    "visual_subject": f"Talking head explanation clip {i}",
                    "narrative_purpose": "Explain key story point clearly.",
                    "on_screen_copy": "Every single word matters when viewers read captions quickly.",
                    "emphasis_words": emph_list if emph_list is not None else [],
                    "audio_intent": {"strategy": "voice"},
                }
                for i in range(3)
            ],
            "silence_pockets": [{"t0": 2.0, "t1": 2.4}],
            "sound_cues": [],
        }

    cine_res = beat_sheet.validate_beat_sheet(_make_text_sheet("cinematic-essay"))
    assert not any("flat text warning" in w.lower() for w in cine_res["warnings"]), cine_res["warnings"]

    flat_res = beat_sheet.validate_beat_sheet(_make_text_sheet("creator-editorial"))
    assert any("flat text warning" in w.lower() for w in flat_res["warnings"]), flat_res["warnings"]

    over_res = beat_sheet.validate_beat_sheet(
        _make_text_sheet("creator-editorial", emph_list=["Every", "single", "word", "matters", "when", "viewers", "read"])
    )
    assert any("highlight overuse" in w.lower() for w in over_res["warnings"]), over_res["warnings"]

    # 4. Visual proof sheets & token contract exist
    for fname in ("safe_zone_typo_proof_9x16.jpg", "narrative_typo_longform_proof_16x9.jpg"):
        p = ROOT / "studio_kit" / "renders" / fname
        assert p.exists() and p.stat().st_size > 20_000, f"Missing visual proof sheet {fname}"
    tokens = json.loads(
        (ROOT / ".agents" / "skills" / "managing-video-brand" / "resources" / "video-design-tokens.json").read_text(
            encoding="utf-8"
        )
    )
    assert "platform_safe_zones" in tokens and "universal_vertical" in tokens["platform_safe_zones"]


