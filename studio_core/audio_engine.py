"""Audio-first foley synthesizer, punchline hard-cut silencer, and editorial audio mixer."""

from pathlib import Path
import numpy as np
from scipy.io import wavfile

SAMPLE_RATE = 44100


def _apply_room_tail(signal: np.ndarray, decay_sec: float = 0.14) -> np.ndarray:
    """Applies a subtle shared room impulse tail so all synthesized foley sits in one space."""
    delays_ms = [11, 23, 37, 53]
    gains = [0.18, 0.11, 0.07, 0.04]
    out = signal.astype(np.float64).copy()
    for d_ms, g in zip(delays_ms, gains):
        shift = int((d_ms / 1000.0) * SAMPLE_RATE)
        if shift < len(out):
            out[shift:] += g * signal[:-shift]
    peak = np.max(np.abs(out))
    if peak > 0.98:
        out = out / peak * 0.95
    return out


def synthesize_sfx_catalog(output_dir: str) -> dict[str, str]:
    """Synthesizes deterministic, room-matched WAV transients for motion graphics and gaming edits."""
    out_root = Path(output_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    catalog: dict[str, str] = {}

    # 1. sub_thud: Deep physical expansion transient (110Hz -> 38Hz pitch drop)
    dur_thud = 0.35
    t = np.linspace(0, dur_thud, int(SAMPLE_RATE * dur_thud), endpoint=False)
    freq = 38.0 + 72.0 * np.exp(-t * 18.0)
    phase = 2.0 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    env = np.exp(-t * 9.5) * (1.0 - np.exp(-t * 220.0))
    thud = _apply_room_tail(0.85 * np.sin(phase) * env)
    thud_path = out_root / "sub_thud.wav"
    wavfile.write(str(thud_path), SAMPLE_RATE, (thud * 32767).astype(np.int16))
    catalog["sub_thud"] = str(thud_path)

    # 2. data_lock: Crisp mechanical UI/metric lock click + harmonic ping
    dur_lock = 0.18
    t2 = np.linspace(0, dur_lock, int(SAMPLE_RATE * dur_lock), endpoint=False)
    click = np.sin(2.0 * np.pi * 1480.0 * t2) * np.exp(-t2 * 65.0)
    ping = 0.45 * np.sin(2.0 * np.pi * 2960.0 * t2) * np.exp(-t2 * 38.0)
    lock = _apply_room_tail((click + ping) * 0.75)
    lock_path = out_root / "data_lock.wav"
    wavfile.write(str(lock_path), SAMPLE_RATE, (lock * 32767).astype(np.int16))
    catalog["data_lock"] = str(lock_path)

    # 3. camera_whoosh: Filtered air sweep for continuous camera carry
    dur_whoosh = 0.42
    n_w = int(SAMPLE_RATE * dur_whoosh)
    t3 = np.linspace(0, dur_whoosh, n_w, endpoint=False)
    rng = np.random.default_rng(42)
    noise = rng.normal(0.0, 1.0, n_w)
    # Moving average bandpass approximation + tonal sweep
    kernel = np.ones(18) / 18.0
    filtered = np.convolve(noise, kernel, mode="same")
    sweep = 0.35 * np.sin(2.0 * np.pi * (160.0 + 240.0 * np.sin(np.pi * t3 / dur_whoosh)) * t3)
    env_w = np.sin(np.pi * t3 / dur_whoosh) ** 1.8
    whoosh = _apply_room_tail((0.55 * filtered + sweep) * env_w)
    whoosh_path = out_root / "camera_whoosh.wav"
    wavfile.write(str(whoosh_path), SAMPLE_RATE, (whoosh * 32767).astype(np.int16))
    catalog["camera_whoosh"] = str(whoosh_path)

    # 4. punch_stinger: Comedic/montage impact stinger (Windah/Faide cut-and-play accent)
    dur_sting = 0.45
    t4 = np.linspace(0, dur_sting, int(SAMPLE_RATE * dur_sting), endpoint=False)
    f_sting = 52.0 + 180.0 * np.exp(-t4 * 28.0)
    ph_sting = 2.0 * np.pi * np.cumsum(f_sting) / SAMPLE_RATE
    body = np.tanh(1.8 * np.sin(ph_sting)) * np.exp(-t4 * 7.5)
    sting = _apply_room_tail(body * 0.9)
    sting_path = out_root / "punch_stinger.wav"
    wavfile.write(str(sting_path), SAMPLE_RATE, (sting * 32767).astype(np.int16))
    catalog["punch_stinger"] = str(sting_path)

    return catalog


def mix_editorial_audio(
    duration_sec: float,
    events: list[dict],
    output_wav: str,
    punchline_windows: list[tuple[float, float]] | None = None,
    ambient_bed_gain: float = 0.06,
) -> str:
    """Mixes timed SFX events over a warm editorial ambient bed and enforces 0-amplitude punchline cut-outs."""
    total_samples = int(duration_sec * SAMPLE_RATE)
    t = np.linspace(0, duration_sec, total_samples, endpoint=False)

    # Subtle harmonic drone bed (110Hz A2 + 165Hz E3 + 220Hz A3) with gentle fade-in/out
    bed = (
        0.55 * np.sin(2.0 * np.pi * 110.0 * t)
        + 0.30 * np.sin(2.0 * np.pi * 165.0 * t)
        + 0.15 * np.sin(2.0 * np.pi * 220.0 * t)
    ) * ambient_bed_gain

    fade_samples = min(int(0.25 * SAMPLE_RATE), total_samples // 4)
    if fade_samples > 0:
        bed[:fade_samples] *= np.linspace(0.0, 1.0, fade_samples)
        bed[-fade_samples:] *= np.linspace(1.0, 0.0, fade_samples)

    master = bed.copy()

    for ev in events:
        t_start = float(ev.get("time_sec", 0.0))
        wav_p = ev.get("wav_path")
        gain_db = float(ev.get("gain_db", 0.0))
        if not wav_p or not Path(wav_p).exists():
            continue
        sr, data = wavfile.read(str(wav_p))
        if data.ndim > 1:
            data = data[:, 0]
        norm_data = data.astype(np.float64) / 32768.0
        gain_lin = 10.0 ** (gain_db / 20.0)
        idx_start = max(0, int(t_start * SAMPLE_RATE))
        idx_end = min(total_samples, idx_start + len(norm_data))
        if idx_end > idx_start:
            master[idx_start:idx_end] += norm_data[: idx_end - idx_start] * gain_lin

    # Peak limiter before punchline cut-out
    peak = np.max(np.abs(master))
    if peak > 0.95:
        master = master / peak * 0.92

    # Enforce hard silence in punchline windows (Windah / MILYHYA comedic pause discipline)
    if punchline_windows:
        for w_start, w_end in punchline_windows:
            s0 = max(0, int(w_start * SAMPLE_RATE))
            s1 = min(total_samples, int(w_end * SAMPLE_RATE))
            if s1 > s0:
                master[s0:s1] = 0.0

    out_p = Path(output_wav)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    stereo = np.column_stack([master, master])
    wavfile.write(str(out_p), SAMPLE_RATE, (stereo * 32767).astype(np.int16))
    return str(out_p)
