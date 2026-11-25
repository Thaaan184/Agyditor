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
    c0 = tm.map_src_to_out(54.45)
    c1 = tm.map_src_to_out(54.82)
    assert 8.2 < c0 < c1 < 8.8
    assert tm.OUTPUT_ROOT == pathlib.Path(r"D:\Clip\Edit\Valorant")
