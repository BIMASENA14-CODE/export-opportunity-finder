# Export Opportunity Finder

Dashboard untuk menjawab: **produk Indonesia apa yang paling berpeluang diekspor ke negara mana, dan mengapa.**

## Hasil

- Setiap pasangan negara-produk diberi skor 0-100 dari lima komponen. Bobot dapat diatur pengguna di dashboard.
- Ada 19.049 pasangan negara-produk yang diberi skor; 18.923 di antaranya punya deret lengkap untuk prakiraan.
- Dalam uji mundur, menebak nilai impor sama dengan tahun terakhir lebih akurat daripada ekstrapolasi tren. Karena itu pertumbuhan dipakai sebagai pemeringkat, bukan ramalan.
- Model gravity menunjukkan pasar yang kurang tergarap dibanding pola ekspor Indonesia sendiri.

## Data

| Sumber | Isi | Dipakai untuk |
|---|---|---|
| BACI HS17 (CEPII), 2017-2024 | Perdagangan bilateral per produk | Skor, prakiraan, gravity |
| CEPII Gravity (2020) | Jarak, bahasa, koloni, perbatasan, FTA | Gravity |
| World Bank NY.GDP.MKTP.CD | GDP USD berjalan | Gravity |

Kelompok produk (HS 2 digit): 03 ikan dan udang, 09 kopi/teh/rempah, 15 minyak dan lemak, 18 kakao, 40 karet, 44 kayu, 61 pakaian rajut, 62 pakaian non-rajut, 64 alas kaki.

## Metode

1. **Pemrosesan data.** CSV BACI dibaca dengan DuckDB, disimpan sebagai Parquet. Nilai dikonversi ke USD (BACI dalam ribu USD) dan kode negara ke ISO3.
2. **Skor peluang.** Lima komponen: ukuran pasar, pertumbuhan, persaingan rendah, ruang pangsa, keunggulan Indonesia. Tiap komponen diubah menjadi peringkat persentil (0-1) lalu dirata-ratakan dengan bobot. Persaingan memakai HHI dari pangsa pemasok. Pertumbuhan adalah kemiringan regresi log-linear impor 2017-2024.
3. **Prakiraan.** Dibandingkan tiga metode (nilai terakhir, tren log-linear, tren diredam setengah) lewat uji mundur: dua tahun terakhir disembunyikan dan ditebak. Galat diukur sebagai median |ln(prediksi / nyata)| di semua seri. Dashboard menampilkan skenario dasar (nilai terakhir) dan skenario tren sebagai rentang.
4. **Model gravity.** Regresi Poisson (PPML) pada seluruh pasangan negara per kelompok produk, nol ikut dipakai. Prediksi untuk Indonesia dikalibrasi ke total ekspor Indonesia sendiri.

## Evaluasi prakiraan

Galat median (log) pada uji mundur, seluruh seri:

| Metode | Galat (log) | Kira-kira meleset |
|---|---|---|
| Nilai terakhir | 0,269 | 31% |
| Tren log-linear | 0,354 | 42% |
| Tren diredam | 0,322 | 38% |

Per kelompok produk:

| Kelompok | Nilai terakhir | Tren | Tren diredam |
|---|---|---|---|
| 03 Ikan & udang | 0,283 | 0,379 | 0,344 |
| 09 Kopi, teh, rempah | 0,265 | 0,332 | 0,309 |
| 15 Minyak & lemak | 0,333 | 0,417 | 0,353 |
| 18 Kakao | 0,391 | 0,353 | 0,363 |
| 40 Karet | 0,262 | 0,315 | 0,286 |
| 44 Kayu | 0,295 | 0,374 | 0,331 |
| 61 Pakaian rajut | 0,259 | 0,353 | 0,310 |
| 62 Pakaian non-rajut | 0,246 | 0,346 | 0,326 |
| 64 Alas kaki | 0,258 | 0,334 | 0,309 |

Hanya kakao (18) yang lebih baik dengan tren. Selebihnya nilai terakhir menang.

## Menjalankan

```
pip install -r requirements.txt
streamlit run app.py
```
Atau klik link dasboard berikut: https://export-opportunity-finder-4wzgeafwp9d4mgwtah6ber.streamlit.app/
Data hasil olahan harus ada di `data/hasil/`: `indikator_final.parquet`, `gravity.parquet`, `deret_impor.parquet`, `ringkasan.json` (dibuat oleh notebook sel 12-14).

## Keterbatasan

- Dengan 8 titik tahunan, ekstrapolasi tren tidak lebih akurat daripada nilai terakhir.
- Nilai USD berjalan, belum dikoreksi inflasi. Tahun 2020 memengaruhi kemiringan tren sebagian produk.
- Variabel gravity memakai tahun 2020, perdagangan memakai tahun lebih baru.
- Potensi gravity dikalibrasi ke total ekspor Indonesia, sehingga menunjukkan pembagian pasar, bukan tambahan total ekspor.
- Tarif rinci, hambatan non-tarif, dan kapasitas produksi tidak dimodelkan.
- Hasil bergantung pada bobot. Gunakan untuk eksplorasi, bukan satu-satunya dasar keputusan.
