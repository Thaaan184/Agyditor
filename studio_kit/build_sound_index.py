"""Scan all local bundled CC0/Pixabay audio libraries on drive D:, measure
objective spectral and loudness features per asset, tag each with acoustic
spectrum roles and coherent style palettes, and write studio_kit/sound_palette_index.json.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any

import librosa
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_INDEX = ROOT / "studio_kit" / "sound_palette_index.json"


def _measure_audio_features(audio_path: pathlib.Path) -> dict[str, Any]:
    y, sr = librosa.load(str(audio_path), sr=48000, mono=True)
    dur = float(len(y) / sr)
    peak = float(np.max(np.abs(y))) if len(y) else 0.0
    rms = float(np.sqrt(np.mean(y ** 2))) if len(y) else 0.0
    peak_db = round(20.0 * np.log10(max(peak, 1e-7)), 2)
    rms_db = round(20.0 * np.log10(max(rms, 1e-7)), 2)

    if len(y) < 32 or peak < 1e-6:
        bands = {"sub_20_90": 0.0, "mud_100_350": 0.0, "voice_350_2500": 0.0, "detail_2500_8000": 0.0, "air_8000_18000": 0.0}
        centroid = 0.0
    else:
        freqs = np.fft.rfftfreq(len(y), 1.0 / sr)
        mag2 = np.abs(np.fft.rfft(y)) ** 2
        total = float(mag2.sum()) + 1e-12
        bands = {
            k: round(100.0 * float(mag2[(freqs >= lo) & (freqs < hi)].sum()) / total, 2)
            for k, (lo, hi) in (
                ("sub_20_90", (20, 90)),
                ("mud_100_350", (100, 350)),
                ("voice_350_2500", (350, 2500)),
                ("detail_2500_8000", (2500, 8000)),
                ("air_8000_18000", (8000, 18000)),
            )
        }
        centroid = round(float(np.sum(freqs * mag2) / total), 1)

    low_share = bands["sub_20_90"] + bands["mud_100_350"]
    high_share = bands["detail_2500_8000"] + bands["air_8000_18000"]
    mid_share = bands["voice_350_2500"]

    if low_share >= 60.0 and high_share < 12.0:
        spectrum_role = "sub_low"
    elif high_share >= 35.0 and low_share < 30.0:
        spectrum_role = "high_air"
    elif mid_share >= 40.0 and low_share < 50.0:
        spectrum_role = "mid_body"
    else:
        spectrum_role = "full_spectrum"

    return {
        "duration_s": round(dur, 3),
        "peak_dbfs": peak_db,
        "rms_dbfs": rms_db,
        "spectral_centroid_hz": centroid,
        "band_pct": bands,
        "spectrum_role": spectrum_role,
    }


def _infer_profiles(category: str, name: str, spectrum_role: str) -> list[str]:
    low_name = f"{category} {name}".lower()
    if category == "ambience" or "room" in low_name or "cricket" in low_name:
        return ["universal-room", "organic-cinema", "editorial-clean"]
    if any(w in low_name for w in ("glitch", "phaser", "powerup", "cyberpunk", "digital", "error", "sci")):
        return ["kinetic-street", "gaming-montage"]
    if any(w in low_name for w in ("paper", "wood", "glass", "metal", "boom", "swell", "violin", "gong", "vinyl", "whip", "reverse", "soft_impact", "cinematic-impact")):
        return ["organic-cinema", "editorial-clean", "kinetic-street"]
    if any(w in low_name for w in ("honk", "horn", "zip", "tada", "ooh", "huh", "oof", "wow", "oh-no", "bubble")):
        return ["comedic-dry"]
    if category in ("click", "tick", "typing", "ui-blip", "pop"):
        if spectrum_role == "high_air" or "soft" in low_name or "key" in low_name or "click" in low_name:
            return ["editorial-clean", "talking-head-reel", "comedic-dry"]
        return ["editorial-clean", "kinetic-street"]
    if category in ("whoosh", "transition", "riser", "impact"):
        return ["editorial-clean", "kinetic-street", "organic-cinema"]
    return ["editorial-clean"]


def build_index() -> dict[str, Any]:
    assets: list[dict[str, Any]] = []

    # 1. .agents/skills/sound-effects/sfx (103 CC0 .ogg)
    se_dir = ROOT / ".agents" / "skills" / "sound-effects" / "sfx"
    se_man = json.loads((se_dir / "manifest.json").read_text(encoding="utf-8"))
    for entry in se_man.get("bundled", []):
        rel_file = entry.get("file")
        if not rel_file:
            continue
        p = se_dir / rel_file
        if not p.exists():
            continue
        feats = _measure_audio_features(p)
        cat = entry.get("category", "misc")
        if cat == "ambience":
            feats["spectrum_role"] = "room_bed"
        asset_id = f"se/{rel_file.replace('/', '__').rsplit('.', 1)[0]}"
        assets.append({
            "id": asset_id,
            "pack": "sound-effects-cc0",
            "rel_path": str(p.relative_to(ROOT)).replace("\\", "/"),
            "category": cat,
            "length_tag": entry.get("length", "short" if feats["duration_s"] < 1.0 else "long"),
            "license": entry.get("license", "CC0 1.0"),
            "attribution": entry.get("attribution", "Freesound CC0"),
            "source_url": entry.get("source_url", ""),
            "profiles": _infer_profiles(cat, rel_file, feats["spectrum_role"]),
            **feats,
        })

    # 2. .agents/skills/media-use/audio/assets/sfx (Pixabay commercial-free .mp3)
    mu_dir = ROOT / ".agents" / "skills" / "media-use" / "audio" / "assets" / "sfx"
    mu_man = json.loads((mu_dir / "manifest.json").read_text(encoding="utf-8"))
    for key, entry in mu_man.items():
        fname = entry.get("file")
        if not fname:
            continue
        p = mu_dir / fname
        if not p.exists():
            continue
        feats = _measure_audio_features(p)
        cat = key.split("-")[0]
        if cat in ("whoosh", "riser", "glitch", "click", "pop", "typing", "chime", "error", "ping", "sparkle", "notification"):
            norm_cat = "transition" if cat == "chime" else ("impact" if key.startswith("impact") else cat)
        else:
            norm_cat = "ui-blip"
        assets.append({
            "id": f"mu/{key}",
            "pack": "media-use-pixabay",
            "rel_path": str(p.relative_to(ROOT)).replace("\\", "/"),
            "category": norm_cat,
            "length_tag": "short" if feats["duration_s"] < 1.0 else "long",
            "license": "Pixabay Content License (Commercial OK, no attribution required)",
            "attribution": "Pixabay via media-use bundle",
            "description": entry.get("description", ""),
            "profiles": _infer_profiles(norm_cat, key, feats["spectrum_role"]),
            **feats,
        })

    # 3. .agents/skills/ghost-editor/library/sfx (CC0 WAV foley & accents)
    ge_dir = ROOT / ".agents" / "skills" / "ghost-editor" / "library" / "sfx"
    ge_man = json.loads((ge_dir / "manifest.json").read_text(encoding="utf-8"))
    for key, entry in ge_man.items():
        fname = entry.get("file")
        if not fname:
            continue
        p = ge_dir / fname
        if not p.exists():
            continue
        feats = _measure_audio_features(p)
        role = entry.get("role", "sfx")
        tags = " ".join(entry.get("tags", []))
        cat = "ambience" if "cricket" in key else (role if role in ("riser", "whoosh", "impact", "glitch") else "foley")
        if cat == "ambience":
            feats["spectrum_role"] = "room_bed"
        assets.append({
            "id": f"ge/{key}",
            "pack": "ghost-editor-cc0",
            "rel_path": str(p.relative_to(ROOT)).replace("\\", "/"),
            "category": cat,
            "length_tag": "short" if feats["duration_s"] < 1.0 else "long",
            "license": entry.get("licence", "CC0 1.0"),
            "attribution": entry.get("source", "CC0 Local Foley"),
            "tags": entry.get("tags", []),
            "profiles": _infer_profiles(cat, f"{key} {tags}", feats["spectrum_role"]),
            **feats,
        })

    # 4. studio_kit/sfx/tonal_pack (24 copyright-free Multiply Sound key-matched tonal WAVs)
    tonal_dir = ROOT / "studio_kit" / "sfx" / "tonal_pack"
    if tonal_dir.exists():
        import re as _re

        for p in sorted(tonal_dir.rglob("*.wav")):
            feats = _measure_audio_features(p)
            rel_str = str(p.relative_to(tonal_dir)).replace("\\", "/")
            stem = p.stem
            is_drone = ("atlantic" in rel_str.lower() or "drone" in rel_str.lower()) and "ping" not in rel_str.lower()
            tonal_type = "tonal_drone" if is_drone else "tonal_hit"
            # Extract canonical root note from filename e.g. "... C#_Db.wav" -> "C#" or "... C.wav" -> "C"
            km = _re.search(r"\b([A-G]#?)(?:_[A-G]b)?\s*$", stem)
            mkey = km.group(1) if km else "C"
            slug = _re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")
            assets.append({
                "id": f"tonal/{slug}",
                "pack": "multiply-sound-tonal",
                "rel_path": str(p.relative_to(ROOT)).replace("\\", "/"),
                "category": "tonal_drone" if is_drone else "tonal_impact",
                "tonal_type": tonal_type,
                "musical_key": mkey,
                "length_tag": "long" if is_drone else "medium",
                "license": "Copyright-Free (Multiply Sound / CHPTRS Free Pack)",
                "attribution": "Multiply Sound (c01Oqf69CC4)",
                "tags": ["tonal", tonal_type, f"key:{mkey}", "cinematic", "musical"],
                "profiles": ["organic-cinema", "editorial-clean", "kinetic-street", "cinematic-essay"],
                **feats,
            })

    by_role: dict[str, int] = {}
    by_pack: dict[str, int] = {}
    for a in assets:
        by_role[a["spectrum_role"]] = by_role.get(a["spectrum_role"], 0) + 1
        by_pack[a["pack"]] = by_pack.get(a["pack"], 0) + 1

    payload = {
        "version": 1,
        "total_assets": len(assets),
        "by_pack": by_pack,
        "by_spectrum_role": by_role,
        "palette_rules": {
            "editorial-clean": "Tight transients, crisp air >3kHz, low-mud controlled whooshes, room-tone beds.",
            "kinetic-street": "Glitch textures, punchy low-mid impacts paired with high mechanical whips.",
            "organic-cinema": "Foley materials (paper, wood, glass, metal, deep boom) & Emotional Realism contrast.",
            "comedic-dry": "Dry un-reverbed stingers & rapid silence drop-outs before punchlines.",
            "gaming-montage": "Sharp transient cutters lock-synced to beat onsets & swept pre-drops.",
        },
        "assets": assets,
    }
    OUT_INDEX.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


if __name__ == "__main__":
    data = build_index()
    print(json.dumps({
        "out": str(OUT_INDEX),
        "total_assets": data["total_assets"],
        "by_pack": data["by_pack"],
        "by_spectrum_role": data["by_spectrum_role"],
    }, indent=2))
