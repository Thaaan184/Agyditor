# Panduan Tipografi Naratif dan Zona Aman UI Platform (v5)

Catatan penyusunan: dokumen ini memakai suara semiformal netral tanpa kalibrasi suara pribadi penulis, sebab tidak ada contoh tulisan dari pengguna yang dilampirkan.

Banyak suntingan video yang rapi secara visual justru kehilangan keterbacaan setelah tayang di YouTube Shorts, TikTok, atau Instagram Reels karena masalah penempatan yang muncul di dua format utama. Pada video vertikal `9:16`, takarir sering turun terlalu rendah sehingga tertutup bilah deskripsi bawah (`30%`) atau kolom tombol kanan. Pada video lanskap `16:9`, penjelasan panjang kerap tampil datar sebagai satu baris teks tanpa permainan ukuran maupun bantuan diagram. Akibatnya, inti pesan terlewat.

Panduan ini merangkum temuan dari tiga video rujukan serta penerapannya pada `studio_kit/`. Rujukan pertama adalah video Editor Keling (`RhVB8WPLJAI`, `28,0 detik`, `1080x1920`) yang mengulas gaya tipografi `@wirilett`, `@raymondchins`, dan `@gawxboi`. Rujukan kedua adalah kelas tipografi aayusucks (`BWRdNeNkph4`, `1.039 detik`, `3840x2160`, 11 bab) yang menguraikan rasio emas dan sistem grid `8pt`. Rujukan ketiga adalah tutorial kamera tipografi 2D dari PeeJ ENT (`G-DHQAzulyU`, `226,0 detik`, `1920x1080`) yang menggeser sudut pandang sebelum kata terucap.

---

## 1. Kontrak Zona Aman UI Platform (`studio_kit/safe_zones.py`)

Tiap aplikasi video menumpuk antarmuka bawaan di atas frame akhir yang telah dirender. Ukuran zona tertutup itu berbeda sedikit di tiap kanal, sehingga batas paling aman untuk konten vertikal lintas platform adalah irisan terketat dari ketiganya. Karena `studio_kit/safe_zones.py` menyimpan batas tersebut dalam pecahan ternormalisasi `[0..1]`, aturan yang sama langsung berlaku pada resolusi penuh `1080x1920`, pratinjau `540x960`, maupun lanskap `1920x1080`. Skala kanvas tidak lagi menggeser margin.

| Target Platform | Batas Kiri Aman | Batas Kanan Aman | Batas Atas Aman | Batas Bawah Aman | Area Tertutup Utama |
|---|---|---|---|---|---|
| `yt_shorts` | `>= 5,5%` | `<= 84,3%` | `>= 11,5%` | `<= 77,1%` | Bilah atas `11,5%`, tombol kanan `15,7%`, meta bawah `22,9%` |
| `tiktok` | `>= 5,5%` | `<= 83,3%` | `>= 13,0%` | `<= 70,8%` | Navigasi atas `13,0%`, tombol kanan `16,7%`, takarir bawah `29,2%` |
| `ig_reels` | `>= 5,5%` | `<= 84,3%` | `>= 12,5%` | `<= 71,9%` | Header atas `12,5%`, tombol kanan `15,7%`, akun bawah `28,1%` |
| `universal_vertical` | `>= 5,5%` | `<= 83,0%` | `>= 13,5%` | `<= 70,2%` | Gabungan ketat semua UI vertikal (bawah `29,8%`, kanan `17,0%`) |
| `youtube_16x9` | `>= 6,0%` | `<= 94,0%` | `>= 8,0%` | `<= 88,5%` | Judul hover atas `8,0%`, bilah pemutar bawah `11,5%` |

Pada rekaman `RhVB8WPLJAI`, tidak ada satu pun teks yang jatuh melewati batas bawah `70%`. Kelompok kata selalu berkumpul di area dada pembicara (`y = 49%` sampai `64%`). Saat wajah mengambil bagian bawah layar, teks akan berpindah ke sisi kiri atas (`y = 28%` sampai `36%`).

Kontrak zona aman itu dijalankan otomatis oleh `studio_kit/narrative_composer.py` sebelum proses render dimulai. Fungsi `audit_html_safe_zones(...)` membuka `studio_kit/tactile_scene_kit.html` lewat Chromium, lalu mengukur kotak batas `getBoundingClientRect()` tiap elemen aktif pada beberapa titik waktu yang telah dijadwalkan di lini masa. Jika satu kotak menyentuh zona merah UI, proses render berhenti seketika dan mencetak koordinat pelanggarannya. Celah penempatan tertangkap sebelum video diekspor.

Pemeriksaan visual cepat juga tersedia di pipeline yang sama. Opsi `--debug-safe-zone` menampilkan garis hijau batas aman bersama pita merah semi-transparan langsung di kanvas. Untuk lembar bukti, fungsi `draw_platform_ui_ghost()` dapat menumpuk bayangan tombol asli platform di atas gambar.

---

## 2. Tiga Mesin Tipografi Naratif di `studio_kit/`

Satu gaya teks tidak mungkin cocok untuk seluruh jenis tayangan. Kebutuhan klip vertikal berdurasi setengah menit sangat berbeda dari video penjelasan berdurasi belasan menit. Untuk itu, `studio_kit/motion_primitives.js` dan `studio_kit/tactile_scene_kit.html` menyediakan tiga mesin tipografi yang bekerja sebagai fungsi murni terhadap waktu `t`.

### A. `narrative_cluster` (Acuan Editor Keling `RhVB8WPLJAI`)

Mesin ini memecah satu klausa kunci menjadi kumpulan kata bertingkat di zona dada (`y = 49%` sampai `65%`). Tiap kata muncul berurutan mengikuti ucapan, lalu bertahan bersama hingga akhir kalimat. Marginnya dikunci pada `left: 6,5%` dan `right: 18%` agar tidak pernah bersenggolan dengan tombol kanan layar ponsel.

Hirarki baca dibentuk melalui pembedaan peran huruf (*Mixed-Voice*), sehingga mata penonton langsung menangkap inti pembicaraan:

* `connector`: kata sambung berukuran kecil (`Inter Tight` bobot `500`) untuk mengantar makna tanpa mencuri fokus.
* `bold` dan `cobalt`: kata utama memakai `Inter Tight` tebal (`900`, *tracking* `-0.035em` sampai `-0.04em`) berwarna putih gading `#FAF7F0` atau biru kobalt `#3B82F6`.
* `serif`: aksen miring memakai `Instrument Serif` untuk memberi tekanan halus pada tuturan.
* `brush_red` dan `oval_red`: sorotan kuas merah `#DC2626` atau garis oval merah miring (`-1,5` sampai `-2 derajat`) yang dibatasi hanya untuk satu kata jangkar di tiap klausa.

Setiap huruf tanpa latar blok diberi garis tepi gelap tipis (`paint-order: stroke fill`) dan bayangan berlapis. Tambahan tersebut menjaga teks tetap tajam walaupun jatuh di atas kemeja putih terang. Pada sisi gerak, fungsi `AGYMotion.narrativeClusterWord(t, wordStartS)` mengatur durasi masuk `0,22 detik` serta sapuan sorotan `0,24 detik`.

### B. `camera_2d_canvas` (Acuan PeeJ ENT `G-DHQAzulyU`)

Pada mesin ini, teks tidak sekadar berganti di tengah layar seperti salindia presentasi. Potongan `2` sampai `3` kata disebar di berbagai titik koordinat pada satu papan datar yang luas. Kamera virtual kemudian bergerak menggeser posisi (`camX`, `camY`), mengubah pembesaran (`zoom`), dan memutar sudut (`rotateDeg`) di antara titik berhenti. Garis putus-putus SVG turut menghubungkan jalur antartitik agar arah baca terlihat jelas.

Keunggulan ritme dari metode PeeJ ENT datang dari pergeseran waktu (*pre-beat lead*). Primitif `AGYMotion.camera2DTypographyState(t, stops, { preBeatLeadS: 0.083 })` memulai gerak kamera `83 ms` (`2` hingga `3` frame pada `30 fps`) lebih cepat sebelum kata terucap karena mata manusia perlu jeda singkat untuk mengikuti perpindahan ruang. Kamera berhenti tepat saat suara masuk. Buram gerak halus pun aktif selama perpindahan berlangsung lalu lenyap begitu posisi terkunci.

### C. `explainer_visual_diagram` (Acuan aayusucks `BWRdNeNkph4`)

Penonton video panjang cepat jenuh jika layar hanya menampilkan wajah pembicara dan teks kecil di bawah selama menit demi menit. Kelas `BWRdNeNkph4` menegaskan bahwa keterbacaan muncul dari kontras ukuran yang tegas dan pembagian ruang yang lega. Fungsi `AGYMotion.goldenTypeScale(basePx)` menghitung tangga ukuran berbasis rasio `1.618x` yang dibulatkan ke kelipatan `8pt`. Standarnya memakai *leading* `1.2x` untuk judul, `1.5x` untuk teks isi, dan lebar baris maksimal `65ch`.

Di `tactile_scene_kit.html`, prinsip itu dipecah menjadi tiga templat visual:

1. `anatomy_ruler`: kartu kertas kraft (`#F4EFE6`) bergaris ukur putus-putus dengan label monospace untuk menjelaskan konsep atau perbandingan rasio.
2. `flanking_word_field`: tata letak dua kolom di tepi kiri dan kanan (`width: 86%`, `height: 74%`) yang menyisakan ruang tengah sepenuhnya kosong bagi wajah pembicara. Kata kunci menyala bergantian mengikuti tuturan tanpa pernah menutup mata subjek.
3. `chapter_slam`: pemisah bab layar penuh bernuansa merah marun (`#B91C1C`), kertas kraft, atau arang gelap (`#141417`) untuk menandai perpindahan topik utama.

---

## 3. Disiplin Penekanan Sesuai Konteks (`studio_kit/beat_sheet.py`)

Tipografi yang kuat tetap harus menyesuaikan suasana cerita. Aturan kaku yang memaksa tiap kalimat memakai animasi besar justru akan merusak ketenangan esai sinematik. Sebaliknya, menyorot hampir seluruh kata dalam satu kalimat juga menghilangkan kontras, sebab mata tidak tahu kata mana yang paling penting.

Karena alasan itu, `studio_kit/beat_sheet.py` memisahkan galat keras dari peringatan kontekstual:

* **Galat keras (menghentikan render)**: irisan elemen dengan zona bahaya `safe_zones.py`, nilai `target_platform` yang tidak sah, kemunculan tanda pisah em dash atau en dash, serta pemakaian jargon klise terlarang.
* **Peringatan teks datar (*flat text warning*)**: hanya berlaku pada profil penjelasan dan klip pendek (`creator-editorial`, `podcast-collage-short`, `kinetic-reel-typography`). Peringatan muncul jika tiga beat berturut-turut memuat minimal enam kata tanpa `emphasis_words` dan tanpa mode tipografi visual, sedangkan profil `cinematic-essay` tetap bebas memakai takarir mikro polos.
* **Peringatan sorotan berlebih (*highlight overuse*)**: aktif pada semua profil apabila lebih dari `60%` kata dalam satu beat masuk ke `emphasis_words`. Satu klausa cukup menonjolkan `1` sampai `2` kata kunci.

---

## 4. Lembar Bukti Visual dan Verifikasi

Kalibrasi lintas rasio direkam pada dua lembar bukti yang lulus audit DOM otomatis (`0` pelanggaran pada `universal_vertical` dan `youtube_16x9`):

* Bukti vertikal `9:16` dengan bayangan UI platform: `studio_kit/renders/safe_zone_typo_proof_9x16.jpg` yang menampilkan dua variasi `narrative_cluster`, `maciekCaptions` di atas batas `30%` bawah, dan `ludaLetterbox` yang menjaga kepala pembicara tetap utuh.
* Bukti lanskap `16:9` untuk narasi panjang: `studio_kit/renders/narrative_typo_longform_proof_16x9.jpg` yang menampilkan `anatomy_ruler`, `flanking_word_field` tanpa menutup wajah, `chapter_slam`, serta `camera_2d_canvas`.

Seluruh fungsi gerak, aturan zona aman, keseimbangan penekanan, dan berkas bukti tersebut diverifikasi otomatis di `tests/test_option_a_stack.py`.
