import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def get_ffmpeg_bin(name: str) -> str | None:
    local_bin = ROOT / "bin" / f"{name}.exe"
    if local_bin.exists():
        return str(local_bin)
    return shutil.which(name)


def test_ffmpeg_and_ffprobe_available():
    ffmpeg_path = get_ffmpeg_bin("ffmpeg")
    ffprobe_path = get_ffmpeg_bin("ffprobe")
    assert ffmpeg_path is not None, "ffmpeg binary not found in bin/ or PATH"
    assert ffprobe_path is not None, "ffprobe binary not found in bin/ or PATH"
    res = subprocess.run([ffmpeg_path, "-version"], capture_output=True, text=True, check=False)
    assert res.returncode == 0
    assert "ffmpeg version" in res.stdout.lower()


def test_workspace_rules_and_design_exist_and_antislop_clean():
    gemini_md = ROOT / "GEMINI.md"
    design_md = ROOT / "DESIGN.md"
    assert gemini_md.exists(), "GEMINI.md is missing"
    assert design_md.exists(), "DESIGN.md is missing"

    gemini_text = gemini_md.read_text(encoding="utf-8")
    design_text = design_md.read_text(encoding="utf-8")

    # R-02: Zero em dashes or en dashes
    assert "\u2014" not in gemini_text, "Em dash found in GEMINI.md"
    assert "\u2013" not in gemini_text, "En dash found in GEMINI.md"
    assert "\u2014" not in design_text, "Em dash found in DESIGN.md"
    assert "\u2013" not in design_text, "En dash found in DESIGN.md"

    # Required guardrails
    assert "invideo" in gemini_text.lower()
    assert ".fcpxml" in gemini_text.lower()
    assert ".setting" in gemini_text.lower()
    assert "ENERGY" in design_text and "RHYTHM" in design_text and "MOTION" in design_text
