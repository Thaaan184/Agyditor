# Panduan Referensi Gerak Teks dan Takarir Studio Lokal

Dokumen ini merangkum analisis enam video YouTube Shorts yang memakai teknik tipografi kinetik, teks tiga dimensi (*3D text*), gerak per huruf, guliran silinder (*rolling text*), dan jejak buram halus (*ghost echo blur*). Catatan tersebut disusun sebagai acuan dasar untuk memperbaiki mutu teks serta takarir (*subtitle*) di studio lokal Option A agar tidak terbaca seperti elemen halaman web yang ditempelkan di atas rekaman. Kalibrasi suara pribadi tidak dilakukan pada berkas ini karena belum tersedia contoh tulisan milik penulis, sehingga penyusunan memakai register semiformal yang wajar.

Enam sumber referensi yang telah diperiksa per frame dan alur audionya adalah:
1. `ZcmcHeWWAuI`: *How to Make 3D Text in DaVinci Resolve* (Daniel Do, 1080x1920, 30 fps, 88 detik).
2. `hRjZf_sg9GQ`: *Apple Text Animation Tutorial in Davinci Resolve* (Daniel Do, 720x1280, 24 fps, 51 detik).
3. `BU64zlrW1Ik`: *Smooth Text Animation Premiere Pro* (Novela Film Academy, 1080x1920, 29,97 fps, 60 detik).
4. `L3HeXpHpxaY`: *Rolling Text Animation in After Effects* (ZeeFX, 1080x1920, 30 fps, 11 detik).
5. `4tx33YWabuE`: *20 Inspirasi Animasi Teks Keren Cuma Pakai AI!* (Digify Product atau Digify Motion, 1080x1920, 60 fps, 33 detik).
6. `NyOTPC5aQog`: *Text animation AM quick tutorial* (Drager Studio, 1440x2560, 60 fps, 48 detik).

---

## 1. Diagnosis Masalah Teks Studio Saat Ini

Jika melihat komponen bawaan di dalam repositori saat ini (`DESIGN.md`, `claude-shorts/remotion/src/components/`, dan templat standar HTML), terdapat lima penyebab utama mengapa hasil teks kita terlihat seperti antarmuka web biasa:

1. **Huruf terjatuh ke font bawaan Windows (`Segoe UI`).** Berkas `DESIGN.md` dan `video-design-tokens.json` menuliskan tumpukan font `Plus Jakarta Sans`, `Inter`, serta `Montserrat`. Pemeriksaan folder `C:\Windows\Fonts` membuktikan bahwa huruf itu tidak terpasang secara lokal pada sistem Windows ini. Jika HTML atau Motif tidak memuat `@font-face` lokal atau memanggil `document.fonts.load()`, Chromium akan memakai `Segoe UI` secara diam-diam. Hal tersebut langsung membuat teks tampak seperti kotak dialog desktop, bukan tipografi video. Padahal berkas `.woff2` dan `.ttf` yang kita perlukan sudah tersimpan di `.agents/skills/ghost-editor/templates/fonts/` dan `.agents/skills/onetake/looks/fonts/`.
2. **Satu blok kotak DOM bergerak serentak** pada komponen dasar seperti `CleanCaptions.tsx` dan `BoldCaptions.tsx`, sebab keduanya hanya menggeser nilai `opacity` atau `scale` untuk seluruh kotak teks sekaligus. Sebaliknya, referensi seperti `hRjZf_sg9GQ` dan `BU64zlrW1Ik` memecah gerak hingga tingkat huruf dengan jeda 2 frame antarhuruf.
3. **Kurva kecepatan datar tanpa buram rana (*shutter motion blur*).** Pergerakan teks pada kode HTML sering memakai satu kurva standar yang lambat di awal dan di akhir tanpa buram gerak searah. Hasilnya, huruf yang berpindah cepat tampak patah di mata penonton. Kontras sekali terlihat jika kita membandingkannya dengan sudut rana 180 derajat hingga 360 derajat pada `ZcmcHeWWAuI`, `BU64zlrW1Ik`, dan `L3HeXpHpxaY`.
4. **Satu suara tipografi per blok tanpa kedalaman kamera.** Takarir dalam satu layar sering memakai jenis huruf dan bobot yang nyaris seragam. Sebaliknya, pada `ZcmcHeWWAuI`, satu kalimat memadukan huruf tanpa kait tegas dengan huruf berkait miring (*italic serif*). Posisi kata-kata itu pun ditempatkan pada jarak sumbu Z yang berbeda sehingga buram fokus kamera (*lens blur*) bekerja secara alami.
5. **Komponen canggih yang sudah ada belum menjadi standar bawaan.** Teknik tersebut sebenarnya sudah tersedia di dalam `hyperframes-registry` (`motion-blur`, `slot-machine-roll`, `caption-parallax-layers`, `caption-kinetic-slam`, `text-match-cut`) dan di `ghost-editor/scripts/lib/kinetic.mjs` (`drum`, `spring`, `scramble`, `headline`, `flipstack`). Kemampuan integral rana 180 derajat pun sudah ada di `onetake/scripts/render.py`, namun alur kerja kita masih sering jatuh ke kode HTML dasar.

---

## 2. Bedah Teknik dan Alur Kerja 6 Video Referensi

Setiap referensi membawa mekanika khusus yang membedakan animasi penyuntingan video profesional dari tempelan CSS biasa. Tabel 1 merangkum mekanika inti dan padanannya di studio lokal.

| ID Video | Gaya Utama | Mekanika NLE Asli | Kunci Rasa Kinetik | Implementasi Studio Lokal |
|---|---|---|---|---|
| `ZcmcHeWWAuI` | Ruang Teks 3D dan Fokus Kamera | DaVinci Fusion: `Text+` ke `ImagePlane3D`, `Merge3D`, `Camera3D` dorong sumbu Z (*Spline Ease In 85%*), `LensBlur` | Kata berada pada jarak Z berbeda, bergerak mengikuti kurva kepala, dan buram saat berada di luar titik fokus | Three.js `PerspectiveCamera` atau `fly3d` pada `motion.mjs`, memakai paduan font serif miring + sans tebal berjarak huruf `-0.04em` |
| `hRjZf_sg9GQ` | Teks Muncul Ala Apple (*Follower Reveal*) | DaVinci Fusion `Text+` (font *SF Pro Text Bold*, *tracking* rapat) + modifier *Follower* kiri ke kanan, jeda 2 frame, *Out Cubic* 10 frame | Setiap huruf naik dari Y `-0.3` disertai pembukaan buram tipis dan bayangan yang menempel pada huruf tanpa memantul | `per-word-rise` atau pemisahan `<span>` per karakter di HyperFrames atau Motif memakai kurva `cubic-bezier(0.16, 1, 0.3, 1)` dan filter `blur(6px)` ke `0px` |
| `BU64zlrW1Ik` | Geser Halus per Huruf + Rana 360 Derajat | Premiere Pro: efek `Transform` pada posisi dan opasitas, matikan *comp shutter* lalu set *Shutter Angle 360*, *Nest + Crop* tiap huruf berjeda 2 frame | Sudut rana 360 derajat membuat huruf yang melesat cepat meninggalkan jejak kabur vertikal yang alami | Aktifkan `data-motion-blur="on"` serta `data-motion-blur-shutter="360"` di HyperFrames atau gunakan integral rana di `render.py` pada OneTake |
| `L3HeXpHpxaY` | Guliran Teks Silinder (*Slot Machine Roll*) | After Effects: `Motion Tile` vertikal, *blur* arah vertikal, grafik kecepatan menanjak di tengah, jeda waktu per huruf | Kolom huruf terasa seperti rol mekanis berkecepatan tinggi dengan sebagian huruf diberi satu warna aksen | Komponen `slot-machine-roll` di `hyperframes-registry` atau blok `drum` di `kinetic.mjs` dengan pemotongan kotak `overflow: hidden` |
| `4tx33YWabuE` | Katalog 20 Gramatika Gerak dan Panggung Terpadu | 20 variasi gerak (*3D Extrude*, *Liquid Fill*, *Split Reveal*, *Decode Marker*, *Outline Extrude*, *Rise Squiggle*, *Strike Rotate*) di panggung bokeh gelap | Setiap gagasan kalimat memilih teknik gerak yang tepat sehingga warna aksen menyala lembut menyatu bersama cahaya panggung | Gabungkan katalog `hyperframes-registry` (`text-match-cut`, `morph-text`, `stitched-text-draw`, `caption-highlight`) bersama `shader-layer.mjs` |
| `NyOTPC5aQog` | Jejak Bayangan Ganda (*Ghost Echo Slide*) | Alight Motion: font *Coolvetica Rg*, duplikat layer teks dasar beropasitas 20%, animasikan duplikat dengan bezier `0.38, 0.00, 0.00, 1.00` + *Gaussian Blur* | Lapisan lama meninggalkan jejak bayangan 20% yang memudar kabur sementara kata baru menyalip dari samping | Buat dua layer tersinkron: layer residu berskala membesar beropasitas 0,2 dengan buram, serta layer utama yang mengunci titik fokus |

---

## 3. Aturan Implementasi di PC Ini (Ryzen 5 5500, RAM 16 GB, GTX 1650)

Hasil pemeriksaan lingkungan lokal lewat `nvidia-smi` dan pustaka Python menunjukkan batas perangkat keras yang harus kita patuhi:

1. **GPU GTX 1650 dimanfaatkan lewat Chromium, bukan PyTorch.** Saat ini `torch.cuda.is_available()` serta `onnxruntime` di Python masih berjalan pada jalur CPU (`torch_cuda: False`). Sebaliknya, Chromium headless dan Three.js dapat langsung memakai GPU GTX 1650 melalui akselerasi WebGL. Jalur ini cocok untuk rendering 3D, `Paper Shaders`, transformasi 3D, dan pemburaman rana. Efek teks 3D (`ZcmcHeWWAuI`), guliran silinder (`L3HeXpHpxaY`), serta rana 360 derajat (`BU64zlrW1Ik`) paling cepat berjalan lewat HyperFrames, OneTake, atau WeftCut Motif.
2. **Pemisahan objek (*text behind subject*) dibatasi durasinya.** Meskipun `rembg` dan `faster_whisper` sudah terpasang, pemrosesan masker video per frame pada CPU berjalan jauh lebih lambat. Untuk menaruh teks di belakang kepala pembicara seperti gaya `step-deck`, batasi rentang potongnya hanya 1 sampai 3 detik pada pembuka video (*hook*), kecuali kita memasang PyTorch CUDA terlebih dahulu.
3. **Font lokal wajib disematkan secara eksplisit** agar kita tidak bergantung pada nama font sistem di CSS. Setiap proyek HyperFrames, OneTake, dan WeftCut Motif harus menyalin berkas `.woff2` dari `.agents/skills/ghost-editor/templates/fonts/` atau `.ttf` dari `.agents/skills/onetake/looks/fonts/`. Setelah itu, panggil `await document.fonts.load(...)` sebelum frame ke-0 direkam.
4. **Draf pratinjau dirender pada resolusi 1080p.** Kita cukup memakai 60 fps saat menguji animasi teks cepat seperti *Apple Follower*, *Rolling Text*, atau *Ghost Echo*, sedangkan klip biasa dapat memakai 30 fps agar iterasi pratinjau berjalan cepat.

---

## 4. Pengembangan Pipeline Studio Berikutnya

Alur penyuntingan video di studio kita bergerak menuju arsitektur empat lapis yang menjaga kejelasan serta rasa NLE:

1. **Lapis 1: Pemetaan Suara dan Emosi Kata (Sebelum Desain Visual).** Selain mengambil cap waktu per kata dari `faster-whisper`, sistem perlu menandai peran kata itu sebagai kata isi, kata kunci penekan (*punch word*), atau angka terukur. Tanpa pemetaan peran ini, takarir cenderung memperlakukan seluruh kata dengan bobot dan ukuran yang sama.
2. **Lapis 2: Kontrak Tipografi Bertingkat (*Mixed Voice Typography*).** Pemakaian satu jenis huruf datar perlu dihentikan. Kita akan memasangkan huruf tanpa kait tebal berjarak rapat (`-0.03em` hingga `-0.04em`) untuk kata kunci dengan huruf berkait miring (*Instrument Serif* atau *Playfair Display Italic*) untuk nuansa ekspresif. Sementara itu, bobot tipis (`300` atau `400`) kita berikan untuk kata penghantar.
3. **Lapis 3: Pemilihan Primitif Gerak Berbasis Fisika dan Rana Blur.** Setiap jenis video memakai primitif yang sudah mendukung gerak per huruf dan buram rana:
   * Untuk rekaman pembicara (*talking head*), kita memakai gerak *Follower* ala Apple (`per-word-rise` dengan pembukaan buram), *Ghost Echo 20%* (`NyOTPC5aQog`), atau teks di belakang subjek pada bagian *hook*.
   * Untuk *motion graphics* dan penjelas produk (*explainer*), kita memakai ruang 3D (`Three.js` atau `fly3d`) agar kamera mengejar kata aktif. Di dalamnya, kita bisa memadukan `slot-machine-roll`, *split reveal*, atau `text-match-cut` dari `hyperframes-registry`.
   * Untuk klip gim (*gaming*), templat CSS tebal yang kaku sebaiknya dihindari. Kita cukup memakai 1 sampai 2 kata singkat sesuai jeda napas atau ketukan drum (`librosa`), disertai *micro zoom-shake* atau *decode* cepat di momen klimaks.
4. **Lapis 4: Panggung Terpadu dan Pemeriksaan Gambar Diam.** Setiap komposisi wajib mempunyai satu pengikat visual antara teks dan latar, seperti bayangan terarah pada tingkat huruf, *radial scrim* halus, atau cahaya bokeh hangat seperti pada `4tx33YWabuE`. Sebelum render akhir dimulai, kita memeriksa potongan gambar diam (*snapshot strip*) tepat di puncak kecepatan gerakan. Pemeriksaan ini memastikan efek buram rana bekerja dan tidak ada huruf yang keluar dari batas aman (*title-safe 80%*).
