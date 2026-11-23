"""DaVinci Resolve Free compatible FCPXML v1.9 timeline and SRT subtitle builder."""

from pathlib import Path
import xml.etree.ElementTree as ET


def _sec_to_rational(sec: float, fps: int) -> str:
    frames = round(sec * fps)
    return f"{frames}/{fps}s"


def build_fcpxml_timeline(
    project_name: str,
    fps: int,
    width: int,
    height: int,
    video_clips: list[dict],
    audio_clips: list[dict],
    output_path: str,
) -> str:
    """Builds a multi-track FCPXML v1.9 timeline ready for File -> Import -> Timeline in DaVinci Resolve Free."""
    if not video_clips:
        raise ValueError("video_clips cannot be empty when building an FCPXML timeline")

    for clip in video_clips + audio_clips:
        if float(clip.get("start_sec", 0.0)) < 0.0 or float(clip.get("duration_sec", 0.0)) <= 0.0:
            raise ValueError(f"Invalid clip timing in {clip}")

    fcpxml = ET.Element("fcpxml", version="1.9")
    resources = ET.SubElement(fcpxml, "resources")
    fmt_id = "r1"
    ET.SubElement(
        resources,
        "format",
        id=fmt_id,
        name=f"FFVideoFormat{height}p{fps}",
        frameDuration=f"1/{fps}s",
        width=str(width),
        height=str(height),
        colorSpace="1-1-1 (Rec. 709)",
    )

    asset_map: dict[str, str] = {}
    next_id = 2
    for clip in video_clips + audio_clips:
        src = str(clip["src"])
        if src not in asset_map:
            aid = f"r{next_id}"
            next_id += 1
            asset_map[src] = aid
            is_audio_only = src.lower().endswith(".wav") or src.lower().endswith(".mp3")
            asset_el = ET.SubElement(
                resources,
                "asset",
                id=aid,
                name=Path(src).stem,
                start="0s",
                duration=_sec_to_rational(float(clip.get("duration_sec", 10.0)), fps),
                hasVideo="0" if is_audio_only else "1",
                hasAudio="1",
                format=fmt_id,
            )
            src_uri = src if src.startswith("file://") else Path(src).resolve().as_uri()
            ET.SubElement(asset_el, "media-rep", kind="original-media", src=src_uri)

    total_dur = max(float(c["start_sec"]) + float(c["duration_sec"]) for c in video_clips)

    library = ET.SubElement(fcpxml, "library")
    event = ET.SubElement(library, "event", name=f"{project_name}_Event")
    project = ET.SubElement(event, "project", name=project_name)
    sequence = ET.SubElement(
        project,
        "sequence",
        format=fmt_id,
        duration=_sec_to_rational(total_dur, fps),
        tcStart="0s",
        tcFormat="NDF",
        audioLayout="stereo",
        audioRate="48k",
    )
    spine = ET.SubElement(sequence, "spine")

    primary_clips = [c for c in video_clips if int(c.get("lane", 0)) == 0]
    overlay_clips = [c for c in video_clips if int(c.get("lane", 0)) != 0]

    primary_el = None
    for idx, vclip in enumerate(primary_clips):
        el = ET.SubElement(
            spine,
            "asset-clip",
            name=str(vclip["name"]),
            ref=asset_map[str(vclip["src"])],
            offset=_sec_to_rational(float(vclip["start_sec"]), fps),
            start="0s",
            duration=_sec_to_rational(float(vclip["duration_sec"]), fps),
            format=fmt_id,
        )
        scale = float(vclip.get("scale", 1.0))
        if abs(scale - 1.0) > 1e-3:
            ET.SubElement(el, "adjust-transform", scale=f"{scale:.2f} {scale:.2f}")
        if idx == 0:
            primary_el = el

    host_el = primary_el if primary_el is not None else spine
    for oclip in overlay_clips:
        el = ET.SubElement(
            host_el,
            "asset-clip",
            name=str(oclip["name"]),
            ref=asset_map[str(oclip["src"])],
            lane=str(int(oclip.get("lane", 1))),
            offset=_sec_to_rational(float(oclip["start_sec"]), fps),
            start="0s",
            duration=_sec_to_rational(float(oclip["duration_sec"]), fps),
            format=fmt_id,
        )
        scale = float(oclip.get("scale", 1.0))
        if abs(scale - 1.0) > 1e-3:
            ET.SubElement(el, "adjust-transform", scale=f"{scale:.2f} {scale:.2f}")

    for aclip in audio_clips:
        el = ET.SubElement(
            host_el,
            "asset-clip",
            name=str(aclip["name"]),
            ref=asset_map[str(aclip["src"])],
            lane=str(int(aclip.get("lane", -1))),
            offset=_sec_to_rational(float(aclip["start_sec"]), fps),
            start="0s",
            duration=_sec_to_rational(float(aclip["duration_sec"]), fps),
            role="effects",
        )
        gain_db = float(aclip.get("gain_db", 0.0))
        if abs(gain_db) > 1e-3:
            ET.SubElement(el, "adjust-volume", amount=f"{gain_db:.1f}dB")

    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(fcpxml, space="  ")
    xml_bytes = ET.tostring(fcpxml, encoding="utf-8", xml_declaration=True)
    out_p.write_bytes(xml_bytes)
    return str(out_p)


def _format_srt_timestamp(sec: float) -> str:
    total_ms = max(0, round(sec * 1000))
    hours = total_ms // 3_600_000
    rem = total_ms % 3_600_000
    minutes = rem // 60_000
    rem %= 60_000
    seconds = rem // 1000
    ms = rem % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"


def export_srt(captions: list[dict], output_path: str) -> str:
    """Exports word or phrase captions to an editable .srt subtitle track for DaVinci Resolve."""
    lines: list[str] = []
    for idx, cap in enumerate(captions, start=1):
        t0 = _format_srt_timestamp(float(cap["start_sec"]))
        t1 = _format_srt_timestamp(float(cap["end_sec"]))
        text = str(cap["text"]).replace("\u2014", ", ").replace("\u2013", "-")
        lines.append(f"{idx}\n{t0} --> {t1}\n{text}\n")
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text("\n".join(lines), encoding="utf-8")
    return str(out_p)
