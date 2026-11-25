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
        "studio_kit/motion_primitives.js",
        "studio_kit/demo_showcase.html",
        "studio_kit/render_showcase.py",
        "references/transitions_study/TRANSITIONS_GUIDE.md",
        "references/text_motion_study/TEXT_MOTION_GUIDE.md",
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
    expected = ("apple-follower-reveal", "ghost-echo-kinetic", "rolling-cylinder-slot", "kinetic-3d-spatial")
    root_primitives = (ROOT / "studio_kit" / "motion_primitives.js").read_text(encoding="utf-8")
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


def test_baseline_showcase_render_artifacts():
    mp4 = ROOT / "studio_kit" / "renders" / "baseline_showcase.mp4"
    sheet = ROOT / "studio_kit" / "renders" / "showcase_sheet.jpg"
    assert mp4.exists() and mp4.stat().st_size > 100_000, "Missing rendered baseline_showcase.mp4"
    assert sheet.exists() and sheet.stat().st_size > 20_000, "Missing visual inspection contact sheet"

    ffprobe = ROOT / "bin" / "ffprobe.exe"
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
    assert float(data["format"]["duration"]) >= 8.0
