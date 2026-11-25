# Transition Reference Guide: Masking, Occlusion & Cutout Wipes

Panduan teknis hasil bedah frame-by-frame 4 YouTube Shorts referensi:
1. `rK6t1utoWrc`: Smooth Mask Reveal Transition (After Effects)
2. `XLMHpphSxJQ`: Natural Foreground Occlusion Wipe (3-Layer Mask)
3. `ruwVARuOkqA`: Geometric Split & Angled Mask Wipe (CapCut)
4. `wkbAl3Y2DnM`: Cutout Frame Hold Slide-In (Subject Pop & Snap)

Dokumen ini memetakan rumus visual, timing frame, kurva easing, sound effect (SFX), dan implementasi langsung di studio lokal Option A (WeftCut, OneTake, HyperFrames, FFmpeg).

---

## 1. Anatomi & Bedah 4 Gaya Transisi

### A. Natural Foreground Occlusion Wipe (`XLMHpphSxJQ`)
* **Konsep:** Memanfaatkan objek atau orang di latar depan (foreground) yang melintas penuh menutupi kamera untuk menyapu klip lama dan mengungkap klip baru.
* **Durasi & Timing:** 10 sampai 18 frame (sekitar 0.4s sampai 0.6s).
* **Struktur 3 Layer:**
  * **Layer 3 (Paling Atas):** Masking/rotoskop siluet objek yang melintas (hanya sisi trailing yang perlu presisi).
  * **Layer 2 (Tengah):** Klip A (klip awal yang sedang disapu keluar).
  * **Layer 1 (Paling Bawah):** Klip B (klip baru yang sudah siap di bawahnya).
* **Karakteristik SFX:** Organic passing whoosh (desiran angin, gemerisik pakaian, atau deru mobil) dengan frekuensi mid-low (150Hz sampai 800Hz).

### B. Cutout Frame Hold Slide-In (`wkbAl3Y2DnM`)
* **Konsep:** Membekukan frame pertama dari Klip B (freeze frame), melakukan cutout/isolasi subjek, lalu menggeser siluet subjek masuk ke frame sebelum Klip B dimulai.
* **Durasi & Timing:**
  * Lead-in overlap: 5 sampai 8 frame sebelum Klip B mulai.
  * Motion path: Masuk cepat dari luar frame (off-screen) menuju posisi resting target 1:1.
  * Shutter Angle: 180 derajat (motion blur aktif di sepanjang arah luncuran).
  * Cut point: Pas siluet tiba di koordinat resting, potong langsung ke Klip B yang bergerak normal.
* **Karakteristik SFX:** High-velocity whip whoosh saat meluncur masuk, disambung snap/impact renyah tepat di frame pembuka Klip B.

### C. Smooth Mask Reveal (`rK6t1utoWrc`)
* **Konsep:** Sapuan mask kurva atau diagonal dinamis yang membuka pemandangan baru dengan percepatan agresif di tengah dan directional blur pada bibir garis potongan.
* **Durasi & Timing:** 12 sampai 20 frame. Kecepatan maksimal terjadi di titik 50% durasi.
* **Kurva Easing:** `cubic-bezier(0.7, 0, 0.3, 1)` atau `power3.inOut`.
* **Karakteristik SFX:** Whoosh udara berkecepatan tinggi dengan puncak energi (peak RMS) tepat di frame persilangan tengah.

### D. Angled Feathered Split Wipe (`ruwVARuOkqA`)
* **Konsep:** Garis mask miring (sudut 25 sampai 45 derajat) dengan feathering lembut (20px sampai 40px) dipadukan dengan scale push (Klip A zoom 100% ke 106%, Klip B zoom 108% ke 100%).
* **Durasi & Timing:** Sangat cepat, 8 sampai 12 frame (0.15s sampai 0.25s).
* **Karakteristik SFX:** Swish tajam frekuensi tinggi (1kHz sampai 4kHz) + low sub-drop lembut.

---

## 2. Parameter Teknis & Rumus Easing

| Parameter | Foreground Occlusion | Cutout Slide-In | Smooth Mask Reveal | Angled Split |
|---|---|---|---|---|
| **Frame Window** | 12 - 18 frames | 5 - 8 frames | 14 - 20 frames | 8 - 12 frames |
| **Motion Blur** | Natural shutter (180 deg) | Synthetic directional blur | Horizontal motion blur | Soft edge feather (25px) |
| **Scale Dynamics** | Flat / subtle parallax | Scale 100% to 100% | Push-in 100% -> 105% | Counter-zoom (106% -> 100%) |
| **SFX Layering** | Air displacement + sub | Fast whip + impact snap | Clean air whoosh | Crisp swish + sub drop |
| **Mix Target** | -16 LUFS (-4 dBFS peak) | -16 LUFS (-3 dBFS peak) | -16 LUFS (-4 dBFS peak) | -16 LUFS (-4 dBFS peak) |

---

## 3. Resep Implementasi di Stack Lokal Studio (Option A)

### Resep 1: WeftCut NLE (Multi-Track & Motif)
1. Letakkan Klip A di Track V1.
2. Letakkan Klip B di Track V2, dimajukan 6 frame (overlap).
3. Buat mask atau gunakan WeftCut Motif overlay (`motif.define`) di Track V3 untuk merender animasi clip-path koordinat:
```javascript
// Contoh Motif WeftCut untuk Wipe Transisi (kontrak resmi: motif.define({ setup, frame(t, ctx) }))
motif.define({
  async setup(props, ctx) { /* setup DOM / fonts */ },
  frame(t, ctx) {
    const progress = Math.min(1, Math.max(0, t / Math.max(0.001, ctx.duration)));
    const ease = progress < 0.5
      ? 4 * progress * progress * progress
      : 1 - Math.pow(-2 * progress + 2, 3) / 2;

    const revealPct = (ease * 100).toFixed(2);
    // Terapkan clip-path / alpha matte berdasarkan t saja (pure f(t))
  }
});
```

### Resep 2: OneTake Engine (`lib/motion.js` & `sfx_palette.py`)
Di OneTake, transisi adalah fungsi murni terhadap waktu:
```javascript
// Cutout entrance menggunakan spring physics
import { spring } from './lib/motion.js';

function renderCutout(t, tStart, tDuration) {
  const localT = t - tStart;
  if (localT < 0 || localT > tDuration) return null;
  
  // Spring dari off-screen X (-800px) ke 0px
  const x = spring(localT, {
    from: -800,
    to: 0,
    stiffness: 180,
    damping: 18,
    mass: 0.8
  });
  
  return {
    transform: `translateX(${x}px)`,
    filter: `blur(${Math.max(0, (1 - localT/tDuration) * 12)}px)`
  };
}
```

### Resep 3: HyperFrames Engine (GSAP & SVG ClipPath)
```javascript
// HyperFrames scene transition
import gsap from 'gsap';

export function setupTransition(incomingElement, cutoutElement) {
  const tl = gsap.timeline();
  tl.fromTo(cutoutElement, 
    { x: '-100%', filter: 'blur(16px)' }, 
    { x: '0%', filter: 'blur(0px)', duration: 0.24, ease: 'power3.in' }
  );
}
```

### Resep 4: Pembuatan Asset Cutout Otomatis via FFmpeg & Python
Untuk membekukan frame dan memotong subjek tanpa bayar API:
```bash
# 1. Freeze frame pertama dari Klip B
bin/ffmpeg.exe -y -ss 00:00:00.000 -i clip_b.mp4 -vframes 1 -q:v 2 freeze_frame.png

# 2. Rotoskop lokal via SAM 2 atau rembg lokal
python -c "from rembg import remove; from PIL import Image; remove(Image.open('freeze_frame.png')).save('cutout_subject.png')"
```
