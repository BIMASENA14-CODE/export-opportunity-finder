# Export Opportunity Finder

Dashboard interaktif untuk menjawab satu pertanyaan: **produk Indonesia apa yang paling berpeluang diekspor ke negara mana, dan mengapa.**

**[Buka dashboard](https://GANTI-DENGAN-LINK-ANDA.streamlit.app)**

## Yang bisa dilakukan di dashboard

- Mengatur bobot lima komponen skor (ukuran pasar, pertumbuhan, persaingan, ruang pangsa, keunggulan Indonesia) dan melihat peringkat berubah langsung.
- Klik negara di peta untuk melihat produk terbaiknya; klik titik di grafik untuk melihat detail satu peluang.
- Melihat prakiraan impor dua skenario, hasil uji akurasi, dan model gravity beserta pengaruh tiap variabel.
- Menghitung margin ekspor dan membandingkan harga tiba dengan harga pasar tujuan.
- Halaman *Ringkasan dan metode* berisi data, algoritma, interpretasi, dan keterbatasan.

## Hasil utama

- 19.049 pasangan negara-produk diberi skor 0-100; 18.923 di antaranya punya deret lengkap untuk prakiraan.
- Pada uji mundur, menebak nilai impor sama dengan tahun terakhir lebih akurat daripada ekstrapolasi tren. Karena itu pertumbuhan dipakai sebagai pemeringkat, bukan ramalan.
- Model gravity (PPML) menunjukkan pasar yang kurang tergarap dibanding pola ekspor Indonesia sendiri.

## Data

| Sumber | Isi | Dipakai untuk |
|---|---|---|
| [BACI HS17](http://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37) (CEPII), 2017-2024 | Perdagangan bilateral per produk | Skor, prakiraan, gravity |
| [CEPII Gravity](http://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=8) (tahun 2020) | Jarak, bahasa, koloni, perbatasan, FTA | Gravity |
| [World Bank](https://data.worldbank.org/indicator/NY.GDP.MKTP.CD) NY.GDP.MKTP.CD | GDP USD berjalan | Gravity |

Kelompok produk (HS 2 digit): 03 ikan dan udang, 09 kopi/teh/rempah, 15 minyak dan lemak, 18 kakao, 40 karet, 44 kayu, 61 pakaian rajut, 62 pakaian non-rajut, 64 alas kaki.

## Metode

1. **Pemrosesan data.** CSV BACI dibaca dengan DuckDB dan disimpan sebagai Parquet. Nilai dikonversi ke USD (BACI dalam ribu USD) dan kode negara ke ISO3.
2. **Skor peluang.** Tiap komponen diubah menjadi peringkat persentil (0-1) lalu dirata-ratakan dengan bobot. Persaingan memakai HHI dari pangsa pemasok. Pertumbuhan adalah kemiringan regresi log-linear impor 2017-2024.
3. **Prakiraan.** Tiga metode dibandingkan lewat uji mundur: nilai terakhir, tren log-linear, tren diredam setengah. Dua tahun terakhir disembunyikan dan ditebak; galat diukur sebagai median |ln(prediksi / nyata)| di semua seri.
4. **Model gravity.** Regresi Poisson (PPML) pada seluruh pasangan negara per kelompok produk, nol ikut dipakai. Prediksi untuk Indonesia dikalibrasi ke total ekspor Indonesia sendiri.

## Akurasi prakiraan

| Metode | Galat median (log) | Kira-kira meleset |
|---|---|---|
| Nilai terakhir | 0,269 | 31% |
| Tren log-linear | 0,354 | 42% |
| Tren diredam | 0,322 | 38% |

Per kelompok produk (galat log):

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

Hanya kakao (18) yang lebih baik dengan tren; selebihnya nilai terakhir menang.

## Struktur repositori

```
app.py              dashboard Streamlit
requirements.txt    dependensi
Code_fixed.ipynb    pengolahan data, skor, gravity, prakiraan
.streamlit/         tema
data/hasil/         hasil olahan yang dibaca dashboard
```

Data mentah (CSV BACI, Parquet antara) tidak disertakan karena ukurannya besar.

## Menjalankan di komputer sendiri

```
pip install -r requirements.txt
streamlit run app.py
```

## Mereproduksi dari data mentah

1. Unduh BACI HS17 dan CEPII Gravity dari tautan di atas, simpan di folder `data/`.
2. Jalankan `Code_fixed.ipynb` dari atas ke bawah. Sel 12-14 menulis file ke `data/hasil/`. Sel World Bank butuh koneksi internet.

## Keterbatasan

- Dengan 8 titik tahunan, ekstrapolasi tren tidak lebih akurat daripada nilai terakhir.
- Nilai USD berjalan, belum dikoreksi inflasi. Tahun 2020 memengaruhi kemiringan tren sebagian produk.
- Variabel gravity memakai tahun 2020, perdagangan memakai tahun lebih baru.
- Potensi gravity dikalibrasi ke total ekspor Indonesia, jadi menunjukkan pembagian pasar, bukan tambahan total ekspor.
- Tarif rinci, hambatan non-tarif, dan kapasitas produksi tidak dimodelkan.
- Hasil bergantung pada bobot. Gunakan untuk eksplorasi, bukan satu-satunya dasar keputusan bisnis.

## Sumber

Gaulier, G. dan Zignago, S. (2010), BACI: International Trade Database at the Product-Level, CEPII Working Paper 2010-23. Conte, M., Cotterlaz, P. dan Mayer, T. (2022), The CEPII Gravity Database, CEPII Working Paper 2022-05. World Bank, World Development Indicators.
