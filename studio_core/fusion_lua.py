"""Native DaVinci Resolve Fusion (.setting & .drfx) Lua table generator and validator."""

from pathlib import Path
import zipfile


def generate_kinetic_callout_setting(
    name: str,
    default_text: str,
    accent_rgb: tuple[float, float, float] = (0.055, 0.647, 0.914),
    duration_frames: int = 150,
) -> str:
    """Generates an editable DaVinci Resolve Fusion Macro (.setting) with KeyFrameStretcher and UserControls."""
    safe_name = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in name)
    r, g, b = accent_rgb
    stretch_start = min(20, max(5, duration_frames // 5))
    stretch_end = max(stretch_start + 10, duration_frames - stretch_start)

    lua_text = f"""{{
	Tools = ordered() {{
		{safe_name} = MacroOperator {{
			Inputs = ordered() {{
				MainText = InstanceInput {{
					SourceOp = "HeadlineText",
					Source = "StyledText",
					Name = "Headline Text",
					DefaultText = "{default_text}",
				}},
				TextSize = InstanceInput {{
					SourceOp = "HeadlineText",
					Source = "Size",
					Name = "Font Size",
					Default = 0.065,
				}},
				AccentRed = InstanceInput {{
					SourceOp = "AccentBarBg",
					Source = "TopLeftRed",
					Name = "Accent Color",
					ControlGroup = 2,
					Default = {r:.4f},
				}},
				AccentGreen = InstanceInput {{
					SourceOp = "AccentBarBg",
					Source = "TopLeftGreen",
					ControlGroup = 2,
					Default = {g:.4f},
				}},
				AccentBlue = InstanceInput {{
					SourceOp = "AccentBarBg",
					Source = "TopLeftBlue",
					ControlGroup = 2,
					Default = {b:.4f},
				}},
				SlideOffset = InstanceInput {{
					SourceOp = "MotionTransform",
					Source = "Center",
					Name = "Callout Position",
				}},
			}},
			Outputs = {{
				MainOutput1 = InstanceOutput {{
					SourceOp = "MediaOut1",
					Source = "Output",
				}}
			}},
			ViewInfo = GroupInfo {{ Pos = {{ 0, 0 }} }},
			Tools = ordered() {{
				BasePlateBg = Background {{
					Inputs = {{
						Width = Input {{ Value = 1920 }},
						Height = Input {{ Value = 1080 }},
						TopLeftRed = Input {{ Value = 0.043 }},
						TopLeftGreen = Input {{ Value = 0.059 }},
						TopLeftBlue = Input {{ Value = 0.090 }},
						TopLeftAlpha = Input {{ Value = 0.0 }},
					}},
					ViewInfo = OperatorInfo {{ Pos = {{ 110, 82.5 }} }},
				}},
				AccentBarBg = Background {{
					Inputs = {{
						Width = Input {{ Value = 12 }},
						Height = Input {{ Value = 96 }},
						TopLeftRed = Input {{ Value = {r:.4f} }},
						TopLeftGreen = Input {{ Value = {g:.4f} }},
						TopLeftBlue = Input {{ Value = {b:.4f} }},
						TopLeftAlpha = Input {{ Value = 1.0 }},
					}},
					ViewInfo = OperatorInfo {{ Pos = {{ 220, 49.5 }} }},
				}},
				HeadlineText = TextPlus {{
					Inputs = {{
						Width = Input {{ Value = 1920 }},
						Height = Input {{ Value = 1080 }},
						StyledText = Input {{ Value = "{default_text}" }},
						Font = Input {{ Value = "Open Sans" }},
						Style = Input {{ Value = "Bold" }},
						Size = Input {{ Value = 0.065 }},
						Red1 = Input {{ Value = 0.973 }},
						Green1 = Input {{ Value = 0.980 }},
						Blue1 = Input {{ Value = 0.988 }},
					}},
					ViewInfo = OperatorInfo {{ Pos = {{ 220, 115.5 }} }},
				}},
				AccentMerge = Merge {{
					Inputs = {{
						Background = Input {{
							SourceOp = "BasePlateBg",
							Source = "Output",
						}},
						Foreground = Input {{
							SourceOp = "AccentBarBg",
							Source = "Output",
						}},
						Center = Input {{ Value = {{ 0.16, 0.22 }} }},
					}},
					ViewInfo = OperatorInfo {{ Pos = {{ 330, 82.5 }} }},
				}},
				TextMerge = Merge {{
					Inputs = {{
						Background = Input {{
							SourceOp = "AccentMerge",
							Source = "Output",
						}},
						Foreground = Input {{
							SourceOp = "HeadlineText",
							Source = "Output",
						}},
						Center = Input {{ Value = {{ 0.42, 0.22 }} }},
					}},
					ViewInfo = OperatorInfo {{ Pos = {{ 440, 82.5 }} }},
				}},
				MotionTransform = Transform {{
					Inputs = {{
						Input = Input {{
							SourceOp = "TextMerge",
							Source = "Output",
						}},
						Center = Input {{ Value = {{ 0.5, 0.5 }} }},
						MotionBlur = Input {{ Value = 1 }},
						Quality = Input {{ Value = 4 }},
						ShutterAngle = Input {{ Value = 180 }},
					}},
					ViewInfo = OperatorInfo {{ Pos = {{ 550, 82.5 }} }},
				}},
				KeyFrameStretcher1 = KeyFrameStretcher {{
					Inputs = {{
						KeyFrames = Input {{
							SourceOp = "MotionTransform",
							Source = "Output",
						}},
						SourceEnd = Input {{ Value = {duration_frames} }},
						StretchStart = Input {{ Value = {stretch_start} }},
						StretchEnd = Input {{ Value = {stretch_end} }},
					}},
					ViewInfo = OperatorInfo {{ Pos = {{ 660, 82.5 }} }},
				}},
				MediaOut1 = MediaOut {{
					Inputs = {{
						Index = Input {{ Value = "0" }},
						Input = Input {{
							SourceOp = "KeyFrameStretcher1",
							Source = "Result",
						}},
					}},
					ViewInfo = OperatorInfo {{ Pos = {{ 770, 82.5 }} }},
				}},
			}},
		}}
	}},
	ActiveTool = "{safe_name}"
}}
"""
    return lua_text


def validate_fusion_setting(lua_text: str) -> dict:
    """Validates a DaVinci Resolve Fusion .setting Lua table string."""
    errors: list[str] = []
    open_braces = lua_text.count("{")
    close_braces = lua_text.count("}")
    if open_braces == 0 or open_braces != close_braces:
        errors.append(f"Unbalanced braces: {open_braces} open vs {close_braces} close")

    has_stretcher = "KeyFrameStretcher" in lua_text
    has_user_controls = "InstanceInput" in lua_text and "Inputs = ordered()" in lua_text
    has_media_out = "MediaOut" in lua_text

    if not has_stretcher:
        errors.append("Missing KeyFrameStretcher node for Edit Page duration scaling")
    if not has_user_controls:
        errors.append("Missing InstanceInput UserControls for Edit Page Inspector")
    if not has_media_out:
        errors.append("Missing MediaOut node termination")
    if "\u2014" in lua_text or "\u2013" in lua_text:
        errors.append("Forbidden em dash or en dash in Fusion setting")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "has_keyframe_stretcher": has_stretcher,
        "has_user_controls": has_user_controls,
        "has_media_out": has_media_out,
    }


def package_drfx(settings_map: dict[str, str], output_drfx_path: str) -> str:
    """Packages one or more validated .setting strings into a DaVinci Resolve .drfx archive."""
    out_path = Path(output_drfx_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel_target, lua_content in settings_map.items():
            report = validate_fusion_setting(lua_content)
            if not report["valid"]:
                raise ValueError(f"Invalid Fusion setting for {rel_target}: {report['errors']}")
            clean_rel = rel_target.lstrip("/")
            if not clean_rel.startswith("Fusion/Templates/"):
                clean_rel = f"Fusion/Templates/{clean_rel}"
            zf.writestr(clean_rel, lua_content.encode("utf-8"))
    return str(out_path)
