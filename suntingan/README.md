# Suntingan video ulasan buku — #MERZ: Anak Penoreh Kini Pilot

Skrip dan aset untuk menyunting `RAW VIDEO.mp4` (rakaman ulasan buku, ~4:40) menjadi video korporat.
Fail video (mentah, pratonton, akhir) **tidak** disimpan dalam repo kerana saiznya besar.

## Susunan kerja
Letakkan fail dalam satu folder kerja (`S`) dengan struktur:

```
S/src/raw.mp4          # rakaman asal
S/assets/              # dijana oleh make_assets.py + make_cards.py (salinan ada di suntingan/assets)
S/broll/sky_plane.mp4  # dijana oleh make_sky.py
S/audio/               # dijana oleh make_audio.py (muzik + kesan bunyi, disintesis sendiri, bebas hak cipta)
S/grade.txt            # rantaian pembetulan warna/cahaya
```

1. `python3 make_assets.py sumber/logo_jata_jnnt.webp S/assets` — logo lutsinar + lower-third nama/jawatan
2. `python3 make_cards.py S/assets sumber/kulit_buku_merz.jpg` — kad pembuka/penutup, panel split-screen, bingkai B-roll, tera air
3. `python3 make_sky.py S/broll` — B-roll langit + pesawat (grafik ilustrasi)
4. `python3 make_audio.py S/audio` kemudian loudnorm ke `music.wav` (lihat build.py untuk aras)
5. `python3 build.py preview` — pratonton 960x540 bertera air "PRATONTON"
6. `python3 build.py final` — eksport akhir 1920x1080 (hanya selepas pratonton diluluskan)

## Ringkasan suntingan (build.py)
- Pembetulan cahaya: sorotan tingkap direndahkan + "cahaya isian" setempat pada wajah/badan (`fillmask.png`).
- Logo Jata/JNNT di kanan atas sepanjang video; nama & jawatan di bawah (0:04.5–0:12).
- Zoom buku lancar (smoothstep 0.7 s) pada saat buku ditunjukkan: 0:22, 0:42, 1:02, 1:55, 3:36, 3:46, 4:34 (masa rakaman asal).
- Variasi paparan: lebar / sederhana (1.3×) / dekat (1.6×) daripada rakaman asal sahaja.
- Split-screen kulit buku 0:26.5–0:33.5; panel B-roll pesawat 0:46–0:52.
- Audio: suara dibersihkan (highpass, denoise, EQ, kompresor, -16 LUFS); muzik ~18 dB di bawah suara; whoosh/chime lembut.
