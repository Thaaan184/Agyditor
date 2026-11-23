import importlib
import json
import os
from pathlib import Path
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
        "GEMINI.md",
        "DESIGN.md",
        ".agents/skills/managing-video-brand/SKILL.md",
        ".agents/skills/driving-weftcut/SKILL.md",
        ".agents/skills/editing-gaming-clips/SKILL.md",
    )
    for rel in authored_paths:
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "\u2014" not in text, f"Forbidden em dash in {rel}"
        assert "\u2013" not in text, f"Forbidden en dash in {rel}"

    gemini_text = (ROOT / "GEMINI.md").read_text(encoding="utf-8")
    design_text = (ROOT / "DESIGN.md").read_text(encoding="utf-8")
    for text in (gemini_text, design_text):
        for tool in ("WeftCut", "HyperFrames", "OneTake", "Three.js", "ghost-editor", "motion-video-director"):
            assert tool in text, f"Missing {tool} reference"
