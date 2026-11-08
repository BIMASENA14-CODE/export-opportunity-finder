import html
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Export Opportunity Finder", layout="wide")

NAMA_BAB = {"03": "Ikan & udang", "09": "Kopi, teh, rempah", "15": "Minyak & lemak (sawit)", "18": "Kakao & cokelat",
            "40": "Karet", "44": "Kayu", "61": "Pakaian rajut", "62": "Pakaian non-rajut", "64": "Alas kaki"}
KOMPONEN = {
    "skor_ukuran_v2": ("Ukuran pasar", "Nilai impor negara tujuan untuk produk ini."),
    "skor_tumbuh_v2": ("Pertumbuhan", "Laju kenaikan impor per tahun, 2017-2024."),
    "skor_persaingan": ("Persaingan rendah", "Makin tersebar pemasoknya (HHI rendah), makin mudah ditembus."),
    "skor_ruang": ("Ruang pangsa", "Makin kecil porsi Indonesia saat ini, makin besar ruang tumbuh."),
    "skor_unggul": ("Keunggulan Indonesia", "Pangsa Indonesia di ekspor dunia untuk produk ini."),
}
PRESET = {"Seimbang": [5, 5, 5, 5, 5], "Pasar besar": [10, 3, 4, 3, 5], "Tumbuh cepat": [3, 10, 4, 5, 4],
          "Mudah ditembus": [4, 4, 10, 8, 3], "Produk unggulan": [4, 4, 4, 4, 10]}
AKSEN, AQUA, ABU = "#f2b705", "#5fd0c9", "#8fb3cc"     # kuning pelampung, air dangkal, biru kabut
SKALA = ["#1b4a73", "#3c8dbc", "#9fd8e8", "#f2b705"]

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@600;800&family=Instrument+Sans:wght@400;500;600&display=swap');
html, body, .stApp, [data-testid="stMarkdownContainer"], label, p, li, td, th {font-family: 'Instrument Sans', system-ui, sans-serif;}
h1, h2, h3, [data-testid="stMetricValue"] {font-family: 'Bricolage Grotesque', 'Instrument Sans', sans-serif !important; letter-spacing: -0.02em;}
.stApp {background:
  repeating-linear-gradient(0deg, rgba(255,255,255,.035) 0 1px, transparent 1px 96px),
  repeating-linear-gradient(90deg, rgba(255,255,255,.035) 0 1px, transparent 1px 96px),
  radial-gradient(ellipse 80% 50% at 12% -8%, #1d5b8c 0%, transparent 70%), #0b2540;}
[data-testid="stHeader"] {background: transparent;}
[data-testid="stSidebar"] {background: #08192e; border-right: 1px solid rgba(255,255,255,.1);}
.block-container {padding-top: 2.2rem; max-width: 1280px;}
h1 {font-weight: 800 !important; font-size: 3rem !important; line-height: 1.05 !important; margin-bottom: .2rem;}
h2, h3 {font-weight: 600 !important;}
.ombak {height: 14px; margin: 2px 0 10px 0; background: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='56' height='14' viewBox='0 0 56 14'><path d='M0 7 Q14 -1 28 7 T56 7' fill='none' stroke='%23f2b705' stroke-width='2'/></svg>") repeat-x; max-width: 220px;}
div[data-testid="stMetric"] {background: transparent; border: 0; border-top: 1px solid rgba(255,255,255,.28); border-radius: 0; padding: 10px 0 0 0;}
div[data-testid="stMetricValue"] {font-size: 2rem; font-weight: 800;}
div[data-testid="stMetricLabel"] p {color: #9db8cc; font-size: .9rem;}
.rk {display: grid; grid-template-columns: 1fr 96px; gap: 14px; align-items: center; padding: 9px 0; border-bottom: 1px solid rgba(255,255,255,.1);}
.rk b {display: block; font-weight: 600; line-height: 1.25;}
.rk small {color: #9db8cc; font-size: .82rem;}
.rk .tr {height: 6px; background: rgba(255,255,255,.12); border-radius: 3px; overflow: hidden;}
.rk .tr i {display: block; height: 100%; background: #f2b705;}
.rk em {font-style: normal; font-size: .8rem; color: #eaf2f7;}
.rkjudul {font-family: 'Bricolage Grotesque', sans-serif; font-weight: 600; font-size: 1.15rem; margin-bottom: 2px;}
</style>""", unsafe_allow_html=True)


def rapikan(fig, h=None):
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color="#eaf2f7", size=13, family="Instrument Sans, sans-serif"),
                      margin=dict(l=10, r=10, t=45, b=10), legend=dict(title=None))
    fig.update_xaxes(gridcolor="rgba(255,255,255,.08)", zerolinecolor="rgba(255,255,255,.2)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,.08)", zerolinecolor="rgba(255,255,255,.2)")
    if h:
        fig.update_layout(height=h)
    return fig


def titik_terpilih(evt):
    try:
        pts = evt["selection"]["points"]
        return int(pts[0]["point_index"]) if pts else None
    except Exception:
        return None


def cari(nama):
    for p in [Path("data/hasil"), Path(__file__).parent / "data/hasil", Path(__file__).parent.parent / "data/hasil"]:
        if (p / nama).exists():
            return p / nama
    return None


@st.cache_data
def muat():
    t = pd.read_parquet(cari("indikator_final.parquet"))
    g = pd.read_parquet(cari("gravity.parquet"))
    t["bab_nama"] = t["bab"].map(NAMA_BAB)
    g["bab_nama"] = g["bab"].map(NAMA_BAB)
    return t, g


@st.cache_data
def muat_opsional(nama):
    p = cari(nama)
    if p is None:
        return None
    return json.load(open(p, encoding="utf-8")) if nama.endswith(".json") else pd.read_parquet(p)


if cari("indikator_final.parquet") is None or cari("gravity.parquet") is None:
    st.error("File data/hasil tidak ditemukan. Jalankan notebook sampai sel 12.")
    st.stop()
tabel, grav = muat()
RING = muat_opsional("ringkasan.json")


def peringkat(bobot, bab, min_pasar, mode):
    d = tabel[tabel["bab"].isin(bab) & (tabel["impor_terakhir"] >= min_pasar * 1e6) & tabel["skor_v2"].notna()].copy()
    if mode == "Sudah dimasuki":
        d = d[d["pangsa_indo"] > 0]
    elif mode == "Belum dimasuki":
        d = d[d["pangsa_indo"] == 0]
    tot = max(sum(bobot.values()), 1)
    d["skor_dash"] = sum(d[k] * w for k, w in bobot.items()) / tot * 100
    d["status"] = d["pangsa_indo"].gt(0).map({True: "Sudah dimasuki", False: "Belum dimasuki"})
    return d.sort_values("skor_dash", ascending=False)


def filter_aktif():
    return st.session_state.get("_f", ({k: 5 for k in KOMPONEN}, list(NAMA_BAB), 20, "Semua"))


def label_peluang(d):
    return d["negara"] + " - " + d["produk"] + "  " + d["deskripsi"].str[:45]


# ================= halaman 1: peluang =================
def hal_peluang():
    st.title("Peluang ekspor Indonesia")
    st.markdown('<div class="ombak"></div>', unsafe_allow_html=True)
    st.caption("Skor 0-100 untuk tiap pasangan negara-produk. Ubah bobot di sidebar, semua grafik mengikuti.")

    def terapkan():
        for k, v in zip(KOMPONEN, PRESET[st.session_state["preset"]]):
            st.session_state[f"w_{k}"] = v

    for k in KOMPONEN:
        st.session_state.setdefault(f"w_{k}", 5)
    sb = st.sidebar
    sb.subheader("Bobot skor")
    sb.selectbox("Pengaturan cepat", list(PRESET), key="preset", on_change=terapkan)
    bobot = {k: sb.slider(n, 0, 10, key=f"w_{k}", help=i) for k, (n, i) in KOMPONEN.items()}
    if sum(bobot.values()) == 0:
        sb.warning("Minimal satu bobot harus di atas 0.")
        st.stop()
    sb.subheader("Saringan")
    bab = sb.multiselect("Kelompok produk", list(NAMA_BAB), default=list(NAMA_BAB), format_func=lambda b: f"{b} {NAMA_BAB[b]}")
    min_pasar = sb.slider("Impor minimum (juta USD)", 1, 500, 20, help="Pasar kecil sering tampak tumbuh cepat karena basisnya kecil.")
    mode = sb.radio("Jenis pasar", ["Semua", "Sudah dimasuki", "Belum dimasuki"])
    st.session_state["_f"] = (bobot, bab, min_pasar, mode)

    df = peringkat(bobot, bab, min_pasar, mode)
    if df.empty:
        st.warning("Tidak ada data dengan saringan ini. Longgarkan saringan di sidebar.")
        return
    t1 = df.iloc[0]
    c = st.columns(4)
    c[0].metric("Peluang", f"{len(df):,}")
    c[1].metric("Nilai pasar", f"{df['impor_terakhir'].sum() / 1e9:,.0f} miliar USD")
    c[2].metric("Negara", df["importir"].nunique())
    c[3].metric("Teratas", t1["negara"], t1["bab_nama"], delta_color="off")
    st.write("")

    peta = df.groupby("importir").head(10).groupby(["importir", "negara"], as_index=False)["skor_dash"].mean()
    kiri, kanan = st.columns([5, 3])
    with kiri:
        fig = px.choropleth(peta, locations="importir", locationmode="ISO-3", color="skor_dash", hover_name="negara",
                            color_continuous_scale=SKALA, labels={"skor_dash": "Skor"})
        fig.update_traces(marker_line_color="#0b2540", marker_line_width=.5)
        fig.update_geos(showframe=False, landcolor="#17406a", showocean=True, oceancolor="#0a2038", showlakes=False,
                        showcountries=True, countrycolor="#0b2540", projection_type="natural earth", bgcolor="rgba(0,0,0,0)")
        fig.update_layout(coloraxis_colorbar=dict(title="Skor", thickness=10, len=.55))
        evt = st.plotly_chart(rapikan(fig, 500).update_layout(margin=dict(l=0, r=0, t=0, b=0)), key="peta",
                              on_select="rerun", selection_mode="points", width="stretch")
        st.caption("Klik sebuah negara untuk melihat produk terbaiknya. Skor negara = rata-rata 10 produk terbaiknya.")
    ip = titik_terpilih(evt)
    iso = peta.iloc[ip]["importir"] if ip is not None and ip < len(peta) else None
    with kanan:
        if iso:
            dn = df[df["importir"] == iso].head(8)
            st.markdown(f'<div class="rkjudul">Produk terbaik di {html.escape(dn.iloc[0]["negara"])}</div>', unsafe_allow_html=True)
        else:
            dn = df.head(8)
            st.markdown('<div class="rkjudul">Peluang teratas</div>', unsafe_allow_html=True)
        baris = ""
        for _, r in dn.iterrows():
            utama, sub = (r["deskripsi"][:46], r["bab_nama"]) if iso else (r["negara"], r["deskripsi"][:46])
            baris += (f'<div class="rk"><div><b>{html.escape(str(utama))}</b><small>{html.escape(str(sub))}</small></div>'
                      f'<div><div class="tr"><i style="width:{max(min(r["skor_dash"], 100), 2):.0f}%"></i></div><em>{r["skor_dash"]:.0f}</em></div></div>')
        st.markdown(baris, unsafe_allow_html=True)

    st.subheader("Ukuran pasar dan pertumbuhan")
    st.caption("Klik sebuah titik untuk melihat detailnya di bawah. Titik kuning adalah pasar yang belum dimasuki Indonesia. Titik besar berarti skor tinggi.")
    s = df.head(150).reset_index(drop=True)
    s["tren"] = s["cagr_tren"] * 100
    ukuran = 7 + (s["skor_dash"] - s["skor_dash"].min()) / max(s["skor_dash"].max() - s["skor_dash"].min(), 1e-9) * 17
    warna = np.where(s["status"] == "Belum dimasuki", AKSEN, ABU)
    fig = go.Figure(go.Scatter(
        x=s["impor_terakhir"], y=s["tren"], mode="markers", showlegend=False,
        marker=dict(size=ukuran, color=warna, opacity=.88, line=dict(color="#0b2540", width=1)),
        customdata=np.stack([s["negara"], s["deskripsi"].str[:50], s["skor_dash"].round(1)], axis=-1),
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>Skor %{customdata[2]}<extra></extra>"))
    for nama, w in [("Belum dimasuki", AKSEN), ("Sudah dimasuki", ABU)]:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=nama, marker=dict(color=w, size=10)))
    fig.update_xaxes(type="log", title="Impor tahun terakhir (USD, skala log)",
                     tickvals=[2e7, 5e7, 1e8, 2e8, 5e8, 1e9, 2e9], ticktext=["20 jt", "50 jt", "100 jt", "200 jt", "500 jt", "1 M", "2 M"])
    fig.update_yaxes(title="Tren pertumbuhan (%/tahun)")
    fig.add_hline(y=0, line_color="rgba(255,255,255,.3)")
    evt2 = st.plotly_chart(rapikan(fig, 470), key="matriks", on_select="rerun", selection_mode="points", width="stretch")
    i2 = titik_terpilih(evt2)
    r = s.iloc[i2] if i2 is not None and i2 < len(s) else s.iloc[0]

    st.subheader(f"{r['negara']}: {r['deskripsi'][:60]}")
    if i2 is None:
        st.caption("Menampilkan peluang teratas. Klik titik pada grafik untuk mengganti.")
    m = st.columns(4)
    m[0].metric("Impor tahunan", f"{r['impor_terakhir'] / 1e6:,.0f} juta USD")
    m[1].metric("Tren", f"{r['cagr_tren'] * 100:+.1f}% / tahun")
    m[2].metric("Pangsa Indonesia", f"{r['pangsa_indo'] * 100:.2f}%")
    m[3].metric("HHI pemasok", f"{r['hhi']:.2f}" if pd.notna(r.get("hhi")) else "-")
    tot = sum(bobot.values())
    kb = pd.DataFrame({"Komponen": [v[0] for v in KOMPONEN.values()], "Poin": [float(r[k]) * bobot[k] / tot * 100 for k in KOMPONEN]})
    fig = px.bar(kb, x="Poin", y="Komponen", orientation="h", color_discrete_sequence=[AQUA],
                 title=f"Sumbangan tiap komponen ke skor {r['skor_dash']:.1f}")
    st.plotly_chart(rapikan(fig, 280), width="stretch")


# ================= halaman 2: prakiraan =================
def hal_prakiraan():
    st.title("Prakiraan permintaan impor")
    st.markdown('<div class="ombak"></div>', unsafe_allow_html=True)
    st.caption("Garis hitam adalah data nyata. Dua skenario di sebelah kanan membentuk rentang, bukan satu angka pasti.")
    deret = muat_opsional("deret_impor.parquet")
    if deret is None:
        st.info("File deret_impor.parquet belum ada. Jalankan sel 13 di notebook.")
        return
    d_all = peringkat(*filter_aktif())
    top = d_all.head(60)
    lab = label_peluang(top)
    pil = st.selectbox("Peluang", lab.index, format_func=lambda i: lab[i])
    r = top.loc[pil]
    d = deret[(deret["importir"] == r["importir"]) & (deret["produk"] == r["produk"])].sort_values("tahun")
    h = np.arange(1, 4)
    if len(d) >= 5:
        x, y = d["tahun"].to_numpy(float), d["nilai_usd"].to_numpy(float) / 1e6
        sl, ic = np.polyfit(x, np.log(y), 1)
        xf = np.r_[x[-1], x[-1] + h]
        dasar = np.r_[y[-1], np.repeat(y[-1], 3)]
        tren = np.r_[y[-1], np.exp(ic + sl * (x[-1] + h))]
        fig = go.Figure()
        fig.add_scatter(x=x, y=y, name="Nyata", line=dict(color="#eaf2f7", width=2.5))
        fig.add_scatter(x=xf, y=dasar, name="Skenario dasar (nilai terakhir)", line=dict(color=AQUA, width=2.5))
        fig.add_scatter(x=xf, y=tren, name="Skenario tren", line=dict(color=AKSEN, width=2.5, dash="dash"),
                        fill="tonexty", fillcolor="rgba(242,183,5,.14)")
        fig.update_layout(title=f"{r['negara']} - {r['deskripsi'][:50]}", yaxis_title="Juta USD")
        st.plotly_chart(rapikan(fig, 420), width="stretch")
        c = st.columns(3)
        c[0].metric("Impor terakhir", f"{y[-1]:,.1f} juta USD")
        c[1].metric(f"Skenario tren {int(xf[-1])}", f"{tren[-1]:,.1f} juta USD", f"{(tren[-1] / y[-1] - 1) * 100:+.0f}%")
        c[2].metric("Tren historis", f"{(np.exp(sl) - 1) * 100:+.1f}% / tahun")
    else:
        st.info("Data historis seri ini kurang dari 5 tahun.")

    st.subheader("Per kelompok produk")
    kunci = d_all.head(300)[["importir", "produk", "bab_nama"]]
    mat = deret.merge(kunci, on=["importir", "produk"]).pivot_table(index=["importir", "produk"], columns="tahun", values="nilai_usd").dropna()
    mat = mat[(mat > 0).all(axis=1)]
    if len(mat) >= 10:
        xs = np.array(mat.columns, float)
        L = np.log(mat.to_numpy(float))
        xc = xs - xs.mean()
        sl = (L - L.mean(1, keepdims=True)) @ xc / (xc @ xc)
        proy = np.exp(L.mean(1) + sl * (xs[-1] - xs.mean()) + sl * 3)
        babs = kunci.set_index(["importir", "produk"])["bab_nama"].reindex(mat.index).values
        rb = pd.DataFrame({"bab": babs, "akhir": mat.iloc[:, -1].to_numpy(), "tren": proy}).groupby("bab", as_index=False).sum()
        rb["perubahan"] = (rb["tren"] / rb["akhir"] - 1) * 100
        rb = rb.sort_values("perubahan")
        fig = px.bar(rb, x="perubahan", y="bab", orientation="h", color_discrete_sequence=[AQUA],
                     labels={"perubahan": "Perubahan (%)", "bab": ""}, title="Perubahan nilai pasar 3 tahun ke depan jika tren berlanjut (300 peluang teratas)")
        st.plotly_chart(rapikan(fig, 360), width="stretch")

    if RING and "backtest_global" in RING:
        st.subheader("Akurasi (uji mundur)")
        bg = RING["backtest_global"]
        nm = {"naif": "Nilai terakhir", "tren": "Tren log-linear", "tren_redam": "Tren diredam"}
        tb = pd.DataFrame({"Metode": [nm[k] for k in bg], "Galat median (log)": [round(v, 3) for v in bg.values()],
                           "Kira-kira meleset": [f"{(np.exp(v) - 1) * 100:.0f}%" for v in bg.values()]})
        st.dataframe(tb, hide_index=True, width="stretch")
        st.caption("Dua tahun terakhir disembunyikan, ditebak dari data sebelumnya, lalu dibandingkan dengan data nyata. "
                   "Metode dengan galat terkecil dipakai sebagai skenario dasar.")


# ================= halaman 3: model gravity =================
def hal_gravity():
    st.title("Model gravity")
    st.markdown('<div class="ombak"></div>', unsafe_allow_html=True)
    st.caption("Memperkirakan ekspor Indonesia ke tiap negara dari ukuran ekonomi, jarak, bahasa, dan perjanjian dagang.")
    bb = st.selectbox("Kelompok produk", list(NAMA_BAB), format_func=lambda k: f"{k} {NAMA_BAB[k]}")
    g = grav[grav["bab"] == bb].nlargest(15, "selisih")
    fig = go.Figure([go.Bar(name="Nyata", x=g["negara"], y=g["aktual"], marker_color=ABU),
                     go.Bar(name="Perkiraan model", x=g["negara"], y=g["potensi"], marker_color=AKSEN)])
    fig.update_layout(barmode="group", yaxis_title="Juta USD", title="15 pasar dengan selisih perkiraan terbesar")
    st.plotly_chart(rapikan(fig, 420), width="stretch")
    st.caption("Perkiraan dikalibrasi ke total ekspor Indonesia, jadi menunjukkan pembagian pasar yang wajar, bukan tambahan total ekspor.")

    if not (RING and "koefisien" in RING and bb in RING["koefisien"]):
        st.info("Koefisien model belum tersimpan. Jalankan sel 14 di notebook.")
        return
    b = RING["koefisien"][bb]
    st.subheader("Kalau variabelnya berubah, ekspor berubah berapa?")
    pct = st.slider("Perubahan variabel (%)", 1, 50, 10)
    f = 1 + pct / 100
    baris = [(f"GDP negara tujuan naik {pct}%", (f ** b["ln_gdp_i"] - 1) * 100),
             (f"GDP Indonesia naik {pct}%", (f ** b["ln_gdp_e"] - 1) * 100),
             (f"Jarak naik {pct}%", (f ** b["ln_dist"] - 1) * 100),
             ("Berbahasa resmi sama", (np.exp(b["comlang_off"]) - 1) * 100),
             ("Pernah berhubungan kolonial", (np.exp(b["comcol"]) - 1) * 100),
             ("Berbatasan darat", (np.exp(b["contig"]) - 1) * 100),
             ("Ada perjanjian dagang (FTA)", (np.exp(b["fta_wto"]) - 1) * 100)]
    tb = pd.DataFrame(baris, columns=["Kondisi", "Perubahan ekspor (%)"]).round(1)
    st.dataframe(tb, hide_index=True, width="stretch")
    st.caption("Angka ini hubungan rata-rata dari data, bukan jaminan sebab-akibat. Variabel lain dianggap tetap.")


# ================= halaman 4: simulator =================
def hal_simulator():
    st.title("Simulator margin")
    st.markdown('<div class="ombak"></div>', unsafe_allow_html=True)
    st.caption("Bandingkan harga tiba di pembeli dengan harga impor rata-rata di pasar tujuan.")
    kand = peringkat(*filter_aktif()).head(100)
    lab = label_peluang(kand)
    pil = st.selectbox("Pasar dan produk", lab.index, format_func=lambda i: lab[i])
    hp = float(kand.loc[pil, "harga_kg"]) if pd.notna(kand.loc[pil, "harga_kg"]) else 1.0
    st.caption(f"Harga impor rata-rata di pasar ini: {hp:.2f} USD/kg")
    c1, c2 = st.columns(2)
    with c1:
        fob = st.number_input("Harga jual FOB (USD/kg)", min_value=0.0, value=round(hp * .9, 2), step=.1, help="Harga di pelabuhan Indonesia.")
        prod = st.number_input("Biaya produksi (USD/kg)", min_value=0.0, value=round(hp * .6, 2), step=.1)
        logi = st.number_input("Logistik dan dokumen (USD/kg)", min_value=0.0, value=round(hp * .05, 2), step=.01)
    with c2:
        frt = st.number_input("Freight dan asuransi (USD/kg)", min_value=0.0, value=round(hp * .05, 2), step=.01)
        tarif = st.number_input("Bea masuk (%)", min_value=0.0, value=5.0, step=.5)
        vol = st.number_input("Volume (ton)", min_value=0.0, value=100.0, step=10.0)
    margin = fob - prod - logi
    landed = (fob + frt) * (1 + tarif / 100)
    sel = (landed / hp - 1) * 100
    m = st.columns(3)
    m[0].metric("Margin per kg", f"{margin:.2f} USD", f"{(margin / fob * 100 if fob else 0):.1f}%")
    m[1].metric("Laba total", f"{margin * vol * 1000:,.0f} USD")
    m[2].metric("Harga tiba vs pasar", f"{sel:+.1f}%", "lebih murah" if sel < 0 else "lebih mahal", delta_color="inverse")
    wf = go.Figure(go.Waterfall(x=["Harga FOB", "Produksi", "Logistik", "Margin"], measure=["absolute", "relative", "relative", "total"],
                                y=[fob, -prod, -logi, margin], increasing=dict(marker=dict(color=AQUA)),
                                decreasing=dict(marker=dict(color="#ff6b6b")), totals=dict(marker=dict(color="#eaf2f7"))))
    wf.update_layout(title="Dari harga jual ke margin (USD/kg)", showlegend=False)
    st.plotly_chart(rapikan(wf, 340), width="stretch")


# ================= halaman 5: ringkasan & metode =================
def hal_ringkasan():
    st.title("Ringkasan hasil dan metode")
    st.markdown('<div class="ombak"></div>', unsafe_allow_html=True)
    R = RING or {}
    tahun = R.get("tahun_data", [])
    rentang = f"{min(tahun)}-{max(tahun)}" if tahun else "2017-2024"

    st.header("Hasil utama")
    d = peringkat({k: 5 for k in KOMPONEN}, list(NAMA_BAB), 20, "Semua")
    t3 = d.head(3)
    baris = "; ".join(f"{r['deskripsi'][:40]} ke {r['negara']}" for _, r in t3.iterrows())
    st.markdown(f"- Dengan bobot seimbang, tiga peluang teratas: {baris}.")
    n_baru = (d.head(50)["pangsa_indo"] == 0).mean() * 100
    st.markdown(f"- {n_baru:.0f}% dari 50 peluang teratas adalah pasar yang belum dimasuki Indonesia.")
    if "backtest_global" in R:
        bg = R["backtest_global"]
        st.markdown(f"- Dalam uji mundur, menebak nilai impor sama dengan tahun terakhir (meleset sekitar {(np.exp(bg['naif']) - 1) * 100:.0f}%) "
                    f"lebih akurat daripada memperpanjang tren (sekitar {(np.exp(bg['tren']) - 1) * 100:.0f}%). Maka pertumbuhan dipakai sebagai pemeringkat, bukan ramalan.")
    st.markdown("- Model gravity menunjukkan pasar yang kurang tergarap dibanding pola ekspor Indonesia sendiri (halaman Model gravity).")

    st.header("Data")
    st.dataframe(pd.DataFrame([
        ["BACI HS17 (CEPII)", f"Perdagangan bilateral, {rentang}", "Skor peluang, prakiraan, model gravity"],
        ["CEPII Gravity", "Jarak, bahasa, koloni, perbatasan, FTA (tahun 2020)", "Model gravity"],
        ["World Bank (NY.GDP.MKTP.CD)", "GDP USD berjalan per negara", "Model gravity"]],
        columns=["Sumber", "Isi", "Dipakai untuk"]), hide_index=True, width="stretch")
    info = [f"Kelompok produk (HS 2 digit): {', '.join(NAMA_BAB)}."]
    if R.get("jumlah_seri_skor"):
        info.append(f"{R['jumlah_seri_skor']:,} pasangan negara-produk diberi skor; {R.get('jumlah_seri_forecast', 0):,} punya deret lengkap untuk prakiraan.")
    if R.get("tahun_model_gravity"):
        info.append(f"Model gravity memakai perdagangan tahun {R['tahun_model_gravity']}.")
    st.markdown("\n".join(f"- {i}" for i in info))

    st.header("Metode")
    st.markdown("""
**1. Skor peluang.** Lima komponen (ukuran pasar, pertumbuhan, persaingan, ruang pangsa, keunggulan Indonesia) diubah menjadi peringkat persentil 0-1 lalu dirata-ratakan dengan bobot pengguna. Persaingan memakai indeks HHI dari pangsa pemasok. Pertumbuhan adalah kemiringan regresi log-linear impor tahunan.

**2. Prakiraan.** Dua pendekatan dibandingkan lewat uji mundur: nilai terakhir (naif) dan tren log-linear (penuh dan diredam). Dua tahun terakhir disembunyikan, ditebak, lalu galatnya diukur sebagai median |ln(prediksi / nyata)| di semua seri. Skenario dasar memakai metode terbaik; skenario tren ditampilkan sebagai batas atas atau bawah.

**3. Model gravity.** Regresi Poisson (PPML) pada seluruh pasangan negara untuk tiap kelompok produk, nol ikut dipakai. Prediksi untuk Indonesia dikalibrasi ke total ekspor Indonesia sendiri.
""")

    if "backtest_per_bab" in R:
        st.header("Galat prakiraan per kelompok produk")
        pb = pd.DataFrame(R["backtest_per_bab"]).T
        pb.index = [f"{i} {NAMA_BAB.get(i, '')}" for i in pb.index]
        pb = pb.rename(columns={"naif": "Nilai terakhir", "tren": "Tren", "tren_redam": "Tren diredam"}).round(3)
        st.dataframe(pb, width="stretch")
        st.caption("Galat median dalam log. Nilai 0,25 kira-kira berarti meleset 28%. Makin kecil makin akurat.")

    st.header("Cara membaca")
    st.markdown("""
- Skor tinggi berarti pasar itu besar, tumbuh, pemasoknya tidak terkonsentrasi, porsi Indonesia masih kecil, dan Indonesia kuat di produk tersebut, sesuai bobot yang dipilih.
- Selisih gravity positif berarti ekspor nyata lebih kecil daripada perkiraan model untuk negara sebesar itu, sedekat itu.
- Rentang prakiraan adalah dua skenario, bukan selang kepercayaan statistik.
""")
    st.header("Keterbatasan")
    st.markdown("""
- Pertumbuhan adalah tren historis. Dengan 8 titik tahunan, ekstrapolasi tren tidak lebih akurat daripada nilai terakhir.
- Nilai USD berjalan, belum dikoreksi inflasi. Tahun 2020 (COVID) memengaruhi kemiringan tren sebagian produk.
- Variabel gravity memakai tahun 2020, sedangkan perdagangan memakai tahun lebih baru.
- Tarif rinci, hambatan non-tarif, kapasitas produksi, dan selera pasar tidak dimodelkan.
- Hasil bergantung pada bobot. Gunakan untuk eksplorasi, bukan satu-satunya dasar keputusan.
""")


pg = st.navigation([st.Page(hal_peluang, title="Peluang", default=True), st.Page(hal_prakiraan, title="Prakiraan"),
                    st.Page(hal_gravity, title="Model gravity"), st.Page(hal_simulator, title="Simulator margin"),
                    st.Page(hal_ringkasan, title="Ringkasan dan metode")])
pg.run()
