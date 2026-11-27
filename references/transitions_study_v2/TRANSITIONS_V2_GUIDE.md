# Panduan Referensi Transisi v2: Layer Manipulation & GLSL Optical Shaders

Dokumen ini mendokumentasikan empat teknik transisi lanjutan hasil bedah referensi video YouTube Shorts beserta padanannya di engine lokal studio. Penyusunan memakai register semiformal standar tanpa kalibrasi suara pribadi.

Empat referensi transisi baru yang dibedah adalah:
1. `9c9PVAQXiLU`: Multi-layer `Null Rig`, dua *Adjustment Layer* lintas *cut*, rotasi-skala *match cut*, dan *radial optical blur*.
2. `AkvzW2O0UeA`: *Pop-Up Cutout Effect* dengan rotoscope subjek di atas *clean plate*, *anchor point* di dasar objek, dan overshoot *Easy Ease*.
3. `dHAx3HSVDLA`: *Varo Flash Cutout Transition* memakai precomp siluet putih ber-Gaussian blur, kedipan opasitas ritmis, dan pulsa *Tint/Invert/Scale*.
4. `uSFLQ5bfKps`: *Motion Tile Seamless Transition* dengan `Mirror Edges: ON`, keyframe `Tile Center` berpola kecepatan `F9`, dan motion blur.

---

## 1. Anatomi Teknis & Rumus Keyframe

### A. Pop-Up Anchor Overshoot (`AkvzW2O0UeA`)
* **Syarat Layer**: Wajib memisahkan *clean plate* latar kosong di layer bawah dan objek hasil cutout di layer atas (`build_popup_bundle`).
* **Aturan Anchor**: Titik jangkar (`transform-origin` atau `anchor`) dipindah dari tengah layar ke dasar objek bagian bawah (`compute_bottom_center_anchor` menghasilkan `[cx, bottomY]`).
* **Kurva Keyframe (`popOvershootTrack`)**: Skala naik cepat dari `0.0` ke `1.06` (`68%` durasi transisi) memakai `aeWhipOut`, lalu turun halus ke `1.00`. Bayangan kontak ikut tumbuh bersama skala objek.

### B. Varo Flash Cutout Strobe (`dHAx3HSVDLA`)
* **Susunan Sandwich 4 Lapis**: Klip keluar diletakkan di bawah, Adjustment Layer pulsa (*Tint + Invert + Scale*) di tengah, dan *freeze cutout* 10 frame pertama di posisi teratas. Setelah kedipan berakhir, klip baru berjalan normal.
* **Strobe Timing (`flashStrobeEval`)**: Siluet diisi warna putih penuh (`whiteFillMix`) dengan `GaussianBlur` sekitar `5px`. Opasitas berkedip cepat (`100 -> 12 -> 100 -> 12 -> 100`) selama `0.32s`. Setelah itu siluet memudar memperlihatkan subjek asli disertai *scale punch* `1.06x`.

### C. Motion Tile Mirror Whip (`uSFLQ5bfKps`)
* **Mekanika Shader (`MotionTileWhipShader`)**: Ruang UV diperluas memakai lipatan cermin (`Mirror Edges`), sehingga tepi frame tidak pernah tampak hitam saat bergeser cepat menembus batas antarklip yang bersebelahan.
* **Integrasi Kecepatan**: Pergeseran `uOffset` mengikuti kurva lonceng simetris `aeWhipInOut` (`[0.78, 0, 0.18, 1]`) yang memicu turunan `trackVelocity` untuk menggerakkan vektor `uBlurVec` pada `9-tap` directional shader pass.

### D. Null-Rig Optical Radial Match (`9c9PVAQXiLU`)
* **Prinsip Seam Overlap**: Dua klip tidak dipotong mentah. Klip masuk mulai lebih awal sekitar `0.15s` melintasi klip keluar dengan arah rotasi dan zoom yang disamakan oleh satu `cameraRig` (`resolveCameraState`).
* **Efek Lensa (`OpticalRadialMatchShader`)**: Di titik puncak kecepatan potong, shader menambah radial zoom blur, sudut `uAngleRad`, serta pembiasan kanal merah-biru (`uChromatic`) agar kedua adegan menyatu secara optik.

---

## 2. Tabel Pilihan Transisi Menurut Jenis Konten

| Gaya Konten | Transisi Paling Pas | Parameter Kunci | Target SFX (`studio_kit/sfx/`) |
|---|---|---|---|
| **Product Showcase** | `Pop-Up Anchor Scale` | `anchor [0.5, bottom]`, overshoot `1.06`, durasi `0.34s` | `pop.ogg` tepat di puncak `1.06` |
| **Montage & Hype Reel** | `Varo Flash Cutout` | 3 kedipan strobe, blur `5px`, tint + invert `0.32s` | `impact.ogg` + `tick.ogg` sinkron kedipan |
| **Talking-Head & Explainer** | `Motion Tile Mirror Whip` | `Mirror Edges: 1`, curve `aeWhipInOut`, blur `9-tap` | `whoosh.ogg` berpusat di `50%` seam |
| **Travel & Match-Cut** | `Optical Radial Match` | Overlap `0.15s`, rotasi + zoom match, chromatic subtle | `riser.ogg` -> `whoosh.ogg` -> `click.ogg` |
