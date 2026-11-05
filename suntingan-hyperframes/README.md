# Suntingan HyperFrames — ulasan buku #MERZ: Anak Penoreh Kini Pilot

Projek [HyperFrames](https://hyperframes.heygen.com) (HTML → video) untuk versi kedua suntingan.
`index.html` dan `compositions/` dijana oleh `gen.py`; masa setiap visual diambil daripada
`transcript.json` (transkripsi bertanda masa perkataan, `hyperframes transcribe --model medium --language ms`).

## Fail yang tidak disimpan dalam repo (terlalu besar)
- `assets/footage/review_graded.mp4` — rakaman asal yang telah dibetulkan cahayanya
  (cahaya isian setempat + sorotan tingkap direndahkan; lihat `../suntingan/grade.txt`), crop 1920×1080, keyframe setiap 1 s.
- `assets/audio/voice.wav` — suara dibersihkan (highpass 80 Hz, denoise, EQ 3 kHz, kompresor, −16 LUFS).

## Bina semula
```bash
npm install
python3 gen.py . --preview     # tanpa --preview untuk versi akhir (tiada tera air)
npx hyperframes check --json
npx hyperframes render -q delivery -o renders/akhir.mp4
```

## Garis masa (masa rakaman asal + 3 s kad pembuka)
- Lower-third nama/jawatan pada "Salam jemaah Nazir" (0:04).
- Panel buku split-screen pada tajuk buku (0:15); zoom buku pada "ini bukunya" (0:22.5) dan setiap kali buku ditunjukkan.
- B-roll langit/pesawat pada "juruterbang… pesawat" (0:33, 1:44).
- Kad: pekerjaan awal + 26,000 permohonan (1:17–1:33), tiga pengajaran (1:56, 2:13, 2:35 dengan langkah perjalanan),
  "murid hari ini" (3:20), petikan penutup (3:58), tiga nilai (4:21).
- Logo Jata/JNNT di kanan atas sepanjang video; kad penutup "Terima kasih".
