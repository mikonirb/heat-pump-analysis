import streamlit as st
import pandas as pd
import numpy as np
import base64

# Pokušaj uvoza matplotlib-a
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# 1. KONFIGURACIJA
st.set_page_config(page_title="Toplotna pumpa – PRO ANALIZA", layout="wide")

if not HAS_MATPLOTLIB:
    st.title("⏳ Instalacija komponenti...")
    st.info("Sistem instalira grafičke module. Osvežite stranicu za 1 minut.")
    st.stop()

st.title("🔥 Toplotna pumpa – Kompletna Analiza (V5.9)")

# --- LINK KA GOOGLE SHEETS (PUBLISHED AS EXCEL) ---
# Ovde zalepi link koji si dobio preko "Publish to web"
gsheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQHYTvxs0PVenFOa59SezJzHDheIswLZoWzFtotG8N8rpdy7ESgHFIYY_R0Bqr9FA/pub?output=xlsx"

@st.cache_data(ttl=60)
def load_data(url):
    try:
        # Čitamo direktno sa Google Sheets linka koji glumi Excel fajl
        df = pd.read_excel(url, engine='openpyxl')
        return df
    except Exception as e:
        st.error(f"Greška pri povlačenju podataka: {e}")
        return None

# 2. OBRADA PODATAKA
df_raw = load_data(gsheet_url)

# Ako Google link ne radi, dajemo opciju ručnog uploada kao rezervu
st.sidebar.header("📁 Izvor podataka")
uploaded_file = st.sidebar.file_uploader("Ili učitaj Excel ručno", type=["xlsx"])
if uploaded_file:
    df_raw = pd.read_excel(uploaded_file, engine='openpyxl')

if df_raw is not None:
    try:
        df = df_raw.copy()
        df.columns = [str(c).strip() for c in df.columns]
        # Normalizacija naziva kolona
        df = df.rename(columns={
            "Startovi kompresora": "Startovi"
        })

        
        # Sređivanje brojeva (zarezi u tačke)
        for col in df.columns:
            if col != "Mesec":
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')

        # KALKULACIJE
        df["COP"] = df["Proizvedena energija (kWh)"] / df["Potrošena struja (kWh)"]
        df["kWh/dan"] = df["Potrošena struja (kWh)"] / df["Dana u mesecu"]
        
        ukupna_proizvedena = df["Proizvedena energija (kWh)"].sum()
        ukupna_struja = df["Potrošena struja (kWh)"].sum()
        prosek_dan = df["kWh/dan"].mean()

        st.success("✅ Podaci uspešno učitani!")

        # 3. SVIH 7 TABOVA
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📊 Pregled", "🌡 Kriva", "💡 EPS", "📅 Sezona", "🚀 OPTIMIZACIJA", "❄️ DEFROST", "💰 POREĐENJE"
        ])

        with tab1:
            st.subheader("📊 Mesečni izveštaj")
            st.dataframe(df.round(2), use_container_width=True)
            c1, c2 = st.columns(2)
            with c1:
                fig1, ax1 = plt.subplots()
                ax1.bar(df["Mesec"], df["kWh/dan"], color="skyblue")
                ax1.set_title("Potrošnja (kWh/dan)"); st.pyplot(fig1); plt.close(fig1)
            with c2:
                fig2, ax2 = plt.subplots()
                ax2.plot(df["Mesec"], df["COP"], marker="o", color="green")
                ax2.set_title("Efikasnost (COP)"); ax2.grid(True); st.pyplot(fig2); plt.close(fig2)

        with tab2:
            st.subheader("🌡 Analiza krive grejanja")
            fig3, ax3 = plt.subplots()
            ax3.scatter(df["Spoljna T (°C)"], df["LWT (°C)"], color="red", s=100, label="Realne tačke")
            tx = np.linspace(df["Spoljna T (°C)"].min()-2, df["Spoljna T (°C)"].max()+2, 10)
           # Konzervativna idealna kriva za radijatore
            ty = 40 - 0.25 * tx
            ax3.plot(tx, ty, "--", color="gray", label="Referentna kriva")
            ax3.set_xlabel("Spoljna T"); ax3.set_ylabel("LWT"); ax3.legend()
            st.pyplot(fig3); plt.close(fig3)
            odstupanje = df["LWT (°C)"] - (40 - 0.25 * df["Spoljna T (°C)"])
            prosek_odstupanja = odstupanje.mean()

            if prosek_odstupanja > 1.5:
                st.warning("🔺 LWT je u proseku previsok – postoji prostor za smanjenje.")
            elif prosek_odstupanja < -1:
                st.info("🔹 LWT je niži od idealnog – sistem je već optimizovan.")
            else:
                st.success("✅ Kriva grejanja je blizu optimalne.")


        with tab3:
            st.subheader("💡 EPS i Troškovi")
            cena = st.number_input("Cena kWh (din)", value=10.5)
            racun_tp = ukupna_struja * cena
            st.metric("Ukupan račun za struju", f"{int(racun_tp)} RSD")
            st.bar_chart(df, x="Mesec", y="Potrošena struja (kWh)")

            mesecna_proj = prosek_dan * 30

            st.subheader("🚦 EPS status (projekcija)")

            if mesecna_proj > 1200:
                st.error("🔴 Projekcija ulazi u CRVENU zonu")
            elif mesecna_proj > 1000:
                st.warning("🟡 Blizu PLAVE zone")
            else:
                st.success("🟢 Zelena zona – bezbedno")


        with tab4:
            st.subheader("📅 Projekcija sezone")
            dani_sezone = st.number_input("Trajanje sezone (dana)", value=180)
            st.metric("Predviđena potrošnja (kWh)", f"{int(prosek_dan * dani_sezone)}")

        with tab5:
            st.subheader("🚀 Optimizacija rada (V5.x PRO)")

            smanjenje = st.slider("Smanjenje LWT (°C)", 0, 5, 1)
            faktor = smanjenje * 0.03  # 3% po °C – konzervativno

            nova_dnevna = prosek_dan * (1 - faktor)
            nova_sezona = nova_dnevna * dani_sezone
            usteda_kwh = prosek_dan * dani_sezone - nova_sezona

            st.metric("Nova procenjena potrošnja (kWh/sezona)", int(nova_sezona))
            st.metric("Ušteda energije (kWh)", int(usteda_kwh))
            st.metric("Ušteda u dinarima", int(usteda_kwh * cena))

            if smanjenje >= 3:
                st.warning("⚠️ Smanjenje ≥3°C – proveri komfor u najhladnijim danima.")
            else:
                st.success("✅ Smanjenje je u bezbednoj zoni.")
            st.subheader("🛋 Comfort Index")

            startovi_dan = df["Startovi"].sum() / df["Dana u mesecu"].sum()
            comfort = max(60, 100 - startovi_dan * 0.7)

            st.metric("Comfort Index", f"{int(comfort)} / 100")

            if comfort > 85:
                st.success("Komfor vrlo stabilan – optimizacija bez rizika.")
            elif comfort > 75:
                st.info("Komfor dobar – male korekcije su moguće.")
            else:
                st.warning("Komfor na granici – ne preporučuje se dalje smanjenje LWT.")


        with tab6:
            st.subheader("❄️ Analiza otapanja (Defrost)")
            v_def = st.slider("Minuta po defrostu", 5, 15, 8)
            n_def = st.slider("Defrosta po satu rada", 0.5, 3.0, 1.0)
            gubitak = (v_def / 60) * n_def * 5 * df["Rad kompresora (h)"].sum()
            st.metric("Gubitak na defrost", f"{int(gubitak)} kWh")

        with tab7:
            st.subheader("💰 Poređenje troškova grejanja")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("### 🪵 Drva")
                cena_drva = st.number_input("Cena drva (din/m3)", value=9000)
                t_drva = (ukupna_proizvedena / 1400) * cena_drva
                st.metric("Trošak", f"{int(t_drva)} RSD")
                st.write(f"Ušteda: **{int(t_drva - racun_tp)} RSD**")
            with c2:
                st.markdown("### 🪵 Pelet")
                cena_peleta = st.number_input("Cena peleta (din/kg)", value=32)
                t_peleta = (ukupna_proizvedena / 4.8) * cena_peleta
                st.metric("Trošak", f"{int(t_peleta)} RSD")
                st.write(f"Ušteda: **{int(t_peleta - racun_tp)} RSD**")
            with c3:
                st.markdown("### 💨 Gas")
                cena_gasa = st.number_input("Cena gasa (din/m3)", value=55)
                t_gas = (ukupna_proizvedena / 9.5) * cena_gasa
                st.metric("Trošak", f"{int(t_gas)} RSD")
                st.write(f"Ušteda: **{int(t_gas - racun_tp)} RSD**")

                st.divider()
                st.info("Obračun koristi prosečne energetske vrednosti: Drva ~1400kWh/m3, Pelet ~4.8kWh/kg, Gas ~9.5kWh/m3.")

    except Exception as e:
        st.error(f"⚠️ Došlo je do greške u kolonama: {e}")
        st.write("Sistem u tabeli vidi ove kolone:", list(df_raw.columns))
else:
    st.warning("Čekam podatke... Unesi Google Sheets link u kod ili učitaj fajl ručno levo.")
