import zipfile
from pathlib import Path
import pytest

from studio_core.fusion_lua import (
    generate_kinetic_callout_setting,
    validate_fusion_setting,
    package_drfx,
)


def test_generate_and_validate_kinetic_callout_setting():
    lua_text = generate_kinetic_callout_setting(
        name="NCT_Kinetic_Callout",
        default_text="PT Nalar Cerdas Teknologi",
        accent_rgb=(0.055, 0.647, 0.914),
        duration_frames=150,
    )
    report = validate_fusion_setting(lua_text)
    assert report["valid"] is True, f"Validation failed: {report['errors']}"
    assert report["has_keyframe_stretcher"] is True
    assert report["has_user_controls"] is True
    assert report["has_media_out"] is True
    assert "PT Nalar Cerdas Teknologi" in lua_text


def test_validate_fusion_setting_rejects_unbalanced_braces_and_missing_nodes():
    bad_lua = "{\n Tools = ordered() {\n   Text1 = TextPlus {\n }\n"
    report = validate_fusion_setting(bad_lua)
    assert report["valid"] is False
    assert any("brace" in err.lower() for err in report["errors"])
    assert report["has_keyframe_stretcher"] is False
    assert report["has_media_out"] is False


def test_package_drfx_creates_valid_resolve_bundle(tmp_path: Path):
    lua_text = generate_kinetic_callout_setting(
        name="NCT_Title",
        default_text="NCT AI",
        accent_rgb=(0.1, 0.7, 0.9),
        duration_frames=120,
    )
    drfx_path = tmp_path / "NCT_Mograph.drfx"
    out = package_drfx({"Edit/Titles/NCT_Title.setting": lua_text}, str(drfx_path))
    assert Path(out).exists()
    with zipfile.ZipFile(out, "r") as zf:
        names = zf.namelist()
        assert "Fusion/Templates/Edit/Titles/NCT_Title.setting" in names
        extracted = zf.read("Fusion/Templates/Edit/Titles/NCT_Title.setting").decode("utf-8")
        assert validate_fusion_setting(extracted)["valid"] is True
