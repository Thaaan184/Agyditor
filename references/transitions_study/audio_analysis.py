import librosa
import numpy as np

videos = {
    "rK6t1utoWrc": (2.0, 3.5),
    "XLMHpphSxJQ": (0.0, 4.0),
    "ruwVARuOkqA": (1.0, 3.0),
    "wkbAl3Y2DnM": (0.5, 3.5)
}

for v_id, (t_start, t_end) in videos.items():
    path = f"references/transitions_study/{v_id}.wav"
    y, sr = librosa.load(path, sr=22050, offset=t_start, duration=(t_end - t_start))
    rms = librosa.feature.rms(y=y)[0]
    peak_idx = np.argmax(rms)
    peak_time = t_start + librosa.frames_to_time(peak_idx, sr=sr)
    max_amp = np.max(np.abs(y))
    print(f"[{v_id}] Window: {t_start}s-{t_end}s | Peak RMS at {peak_time:.2f}s | Max Amp: {max_amp:.3f}")
