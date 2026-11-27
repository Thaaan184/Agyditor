# Panduan Editorial Class-Up v4: Pacing, Konteks, Tipografi, Grading Filmic, dan Tonal SFX

Dokumen ini menyatukan hasil bedah empat belas video rujukan lintas gaya, mencakup esai sinematik `2,39:1` serta suntingan kolase vertikal. Seluruh ukuran ritme potongan, dinamika suara `ebur128`, dan sebaran warna diukur lewat skrip lokal pada drive `D:`. Pada dokumen ini tidak dilakukan kalibrasi suara pribadi pengguna, sehingga tulisannya memakai laras teknis netral (*semiformal*).

---

## 1. Pemilihan Gaya Editing Sesuai Konteks (`studio_kit/context_router.py`)

Kesalahan umum pada alur otomatis muncul ketika satu target loudness dan satu kecepatan potong dipaksakan ke semua jenis video. Pengukuran empat belas video rujukan membuktikan rentang rasa tiap genre berjauhan.

| Konteks (`profile`) | Rujukan Terukur | Pacing & Dinamika Audio | Identitas Visual & Warna |
|---|---|---|---|
| `cinematic-essay` | `Luda` (`NFm2Xjx61Q8`, `g_UpY8VNwa0`), `Jacob Nordin` (`I66_LmOTlSk`) | `-19,9` sampai `-23,2 LUFS`, `LRA 6,2-11,6 LU`, `CV 0,52-1,69`, tahan shot `5-10s` bergantian montase `1,8s` | Kanvas anamorfik `2,39:1` atau kotak vertikal hitam dengan takarir merah tipis tanpa kotak latar; grading `luda_filmic_warm` |
| `podcast-collage-short` | `marksoy` (`MoVlt-ptxIk`) | `-8,7 LUFS`, `LRA 2,9 LU`, `mud 20,24%`, `air 10,05%`, potong cepat tiap `1,5-3,3s` | Selingan bicara bersih bersama kartu penuh warna krem `#ECEAD8`, biru kobalt `#0B1A8A`, kliping koran dilingkari merah, dan sorotan stabilo merah |
| `creator-editorial` | `Gaku Lange` (`EWqrpI1IAyI`, `RAWhQycgvNY`, `SmsNAtaLR9I`), `Herman Huang` (`FZS0olGLPIw`), `Andrew` (`pdLEHfkwgV8`) | `-14,8` hingga `-16,4 LUFS`, `LRA 2,3-5,3 LU`, `CV 0,96-1,89` | Pembuka tunjuk langsung (*Show First*), papan potong hijau, lencana gelombang NLE, gelembung pesan iMessage atau catatan IG, serta grading `gaku_filmic_teal` |
| `kinetic-reel-typography` | `Maciek Sulima` (`yRsK2JyfMGM`) | `-15,9 LUFS`, `LRA 4,4 LU`, teks bergeser mulus di sumbu tunggal | Kurva S terbelah antar dua teks (*Split-S-Curve*) plus takarir asimetris tiga tingkat (`lead` kecil, `HERO` besar miring, `tail` kecil) |

Modul `studio_kit/context_router.py` membaca brief maupun nama profil secara langsung agar rasio layar, target `LUFS`/`LRA`, preset LUT, serta batas audit spektral di `studio_kit/acoustic_audit.py` langsung terkunci sesuai genre. Satu resep untuk semua jenis video pun resmi ditinggalkan.

---

## 2. Alur Gerak, Pengendalian Transisi, dan Teks Split-S-Curve

### 2.1 Tiga Pilar Alur Gerak (`EWqrpI1IAyI`) & Disiplin Transisi (`FZS0olGLPIw`)

Gaku Lange menunjukkan bahwa kelancaran suntingan lahir saat mata penonton dipandu rapi tanpa lompatan liar. Empat aturan geraknya kini tercatat ke dalam gerbang `studio_kit/beat_sheet.py`:

1. **Arah Gerak Konsisten (*Directional Flow*)**: dua klip bergerak berurutan disambung searah (`pan_left` menuju `pan_left` atau `push_in` menuju `push_in`), sedangkan pembalikan arah perlu dijeda oleh satu shot diam netral (`static_reset`) sebagai penyegar mata.
2. **Potong di Puncak Gerak (*Motion-to-Motion*)**: potong klip keluar saat kecepatan kamera berada di puncak lalu mulai klip masuk tepat di tengah gerakan searah. Potongan terasa tak terlihat.
3. **Jejak Mata (*Eye Trace*)**: dekatkan titik fokus subjek klip baru ke posisi fokus klip sebelumnya agar pandangan penonton tidak lelah mencari pusat gambar.
4. **Transisi Wajib Berjasa (*Earn Its Spot*)**: Herman Huang menegaskan bahwa transisi berlebihan justru membuat seluruh video terasa datar, sehingga `beat_sheet.py` memberi peringatan otomatis bila lebih dari `55%` beat memakai transisi mencolok.

### 2.2 Kurva S Terbelah (`yRsK2JyfMGM`) & Tren Visual (`SmsNAtaLR9I`)

Maciek Sulima memecah satu kurva S menjadi dua tahap pada primitif `splitSCurveHandoff` di `studio_kit/motion_primitives.js`. Teks keluar berakselerasi menuju titik tukar (`u^3.2`), lalu teks masuk melambat halus sesudahnya (`1-(1-u)^3.6`) pada satu sumbu gerak. Selain itu, tiga tren visual dari `SmsNAtaLR9I` (*Freeze-Frame Roto*, *Clean-Plate Object Grow*, dan *Match-Cut Split Screen*) kini masuk ke `motion_primitives.js` serta `narrative_composer.py`. Ketiganya siap dipakai saat cerita membutuhkan aksen visual tambahan.

---

## 3. Grading Filmic Lokal Tanpa Ketergantungan Berbayar (`studio_kit/color_grade.py`)

Analisis terhadap `-14_cGVgV20`, `f31-WqH7izk`, `PuoI9paASys`, dan `NFm2Xjx61Q8` menyingkap alur warna film yang ringan dijalankan secara lokal memakai FFmpeg `lut3d`:

* **Aturan Piringan Bersih (`PuoI9paASys`)**: warna diterapkan pada rekaman murni `[base_raw]` sebelum overlay teks ditempel. Tipografi tetap tajam tanpa ikut berwarna kuning atau kabur.
* **Kepadatan HSV Kanal 2 (`-14_cGVgV20`)**: saturasi dinaikkan pada ruang warna HSV disertai penurunan tipis kecerahan warna pekat (*subtractive film density*). Merah dan biru tampak dalam seperti pita film, jauh dari warna neon digital.
* **Lapisan Filmic 3D LUT + Halation (`f31-WqH7izk`)**: lantai hitam diangkat lembut (`L5` sekitar `4,5` sampai `7,0`) bersama peredaman putih puncak. Bayangan dingin cyan-teal dipisah bersih dari sorotan hangat agar warna kulit di midtone tetap alami. Pendar merah-jingga (*halation*) hanya muncul di sumber cahaya terang di atas ambang `222`, lengkap bersama vinyet halus. Kelima preset `.cube` (`luda_filmic_warm`, `gaku_filmic_teal`, `editorial_tungsten_clean`, `collage_punch_clean`, `neutral_rec709`) dibuat otomatis di `studio_kit/luts/`.

---

## 4. Tonal SFX Selaras Nada Lagu & Tata Suara Spasial (`studio_kit/sound_engine.py`)

Dari `c01Oqf69CC4` (*Multiply Sound*), `I66_LmOTlSk` (*Jacob Nordin*), dan `b9hBHt317mw` (*Haseeb Ahsan*), tata suara studio memperoleh tiga peningkatan utama:

1. **Bank 24 Tonal SFX Gratis Terindeks**: seluruh `24` berkas WAV bebas hak cipta (`12` nada `Atlantic Major_Minor` dan `12` nada `Ping Boom Major_Minor`) tersimpan di `studio_kit/sfx/tonal_pack/` dan tercatat di `studio_kit/sound_palette_index.json` (total `173` aset luring).
2. **Deteksi Nada Otomatis untuk Lagu Apa Pun**: fungsi `detect_musical_key` membaca kromatik `librosa` dari lagu pilihan pengguna maupun underscore lokal. Fungsi `add_tonal_sfx` menarik drone atau impact pada nada selaras. Lagu tetap dipilih sesuai konteks.
3. **Sapuan Filter EQ & Panning Spasial**: fungsi `add_filter_sweep` menjalankan sapuan *low-pass* dan *high-pass* untuk perpindahan ruang. Fitur ini melengkapi panning gerak stereo serta J-cut dan L-cut pada bus lima jalur.
