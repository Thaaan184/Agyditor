from pathlib import Path
import pytest

from studio_core.antislop_gate import audit_antislop_deliverable
from studio_core.html_renderer import render_seekable_html
from studio_core.continuity_probe import probe_video_continuity


def test_audit_antislop_deliverable_catches_slop_and_passes_clean():
    slop_html = "<div>Revolutionary AI-powered platform \u2014 trusted by 10,000+ users</div>"
    slop_report = audit_antislop_deliverable(slop_html, ["Revolutionary AI-powered \u2014 10,000+ users"])
    assert slop_report["passed"] is False
    assert any("R-02" in v for v in slop_report["violations"])
    assert any("R-16" in v for v in slop_report["violations"])

    clean_html = """<!DOCTYPE html>
<html lang="id">
<head><title>PT Nalar Cerdas Teknologi</title></head>
<body><main><h1>PT Nalar Cerdas Teknologi</h1></main></body>
</html>"""
    clean_report = audit_antislop_deliverable(clean_html, ["PT Nalar Cerdas Teknologi membangun solusi AI dan IoT."])
    assert clean_report["passed"] is True, f"Unexpected violations: {clean_report['violations']}"


def test_render_seekable_html_and_probe_continuity(tmp_path: Path):
    html_file = tmp_path / "mini_comp.html"
    html_file.write_text(
        """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>
  body { margin: 0; background: #0B0F17; overflow: hidden; width: 640px; height: 360px; }
  #bar { position: absolute; top: 140px; height: 80px; background: #0EA5E9; }
</style>
</head>
<body>
  <div id="bar"></div>
  <script>
    window.__seek = function(t) {
      const bar = document.getElementById('bar');
      const x = 40 + (t / 1.0) * 320;
      const w = 120 + (t / 1.0) * 140;
      bar.style.left = x + 'px';
      bar.style.width = w + 'px';
    };
    window.__seek(0);
  </script>
</body>
</html>""",
        encoding="utf-8",
    )
    out_mp4 = tmp_path / "mini.mp4"
    res = render_seekable_html(
        html_path=str(html_file),
        output_mp4=str(out_mp4),
        duration_sec=1.0,
        fps=10,
        width=640,
        height=360,
        audio_wav=None,
    )
    assert Path(res["output_mp4"]).exists()
    assert res["frames_rendered"] == 10

    probe = probe_video_continuity(str(out_mp4), beat_boundaries_sec=[0.5])
    assert probe["passed"] is True
    assert probe["carry_score"] >= 0.70
    assert probe["motion_energy"] > 0.001


def test_probe_continuity_rejects_static_slideshow(tmp_path: Path):
    static_html = tmp_path / "static_comp.html"
    static_html.write_text(
        """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"></head>
<body style="margin:0;background:#0B0F17;width:640px;height:360px;">
  <script>window.__seek = function(t) {};</script>
</body></html>""",
        encoding="utf-8",
    )
    out_mp4 = tmp_path / "static.mp4"
    render_seekable_html(str(static_html), str(out_mp4), duration_sec=0.6, fps=10, width=640, height=360)
    probe = probe_video_continuity(str(out_mp4), beat_boundaries_sec=[0.3])
    assert probe["passed"] is False
    assert probe["motion_energy"] < 0.0005

