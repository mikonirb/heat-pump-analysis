import streamlit as st
import pandas as pd
import numpy as np
import base64
import os

# Pokušaj uvoza matplotlib-a
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# 1. KONFIGURACIJA (Mora biti prva)
st.set_page_config(page_title="Toplotna pumpa – PRO ANALIZA", layout="wide")

if not HAS_MATPLOTLIB:
    st.title("⏳ Instalacija komponenti...")
    st.info("Instaliram grafičke module. Osvežite stranicu za 1 minut.")
    st.stop()

st.title("🔥 Toplotna pumpa – Kompletna Analiza (V5.7)")

# --- LINK I IZVOR ---
onedrive_url = "https://1drv.ms/x/c/a15c6fc067062efb/IQD5_1Yj9WhfRafvHJ1x3Y-wAYVUR7tP6_uTeZ3gnxYa9o4"

def get_direct_download(url):
    try:
        clean_url = url.split('?')[0]
        s = base64.b64encode(bytes(clean_url, 'utf-8')).decode('utf-8')
        return f"https://api.onedrive.com/v1.1/shares/u!{s.replace('/','_').replace('+','-').rstrip('=')}/root/content"
    except: return None

st.sidebar.header("📁 Izvor podataka")
uploaded_file = st.sidebar.file_uploader("Ili učitaj Excel ručno", type=["xlsx"])

@st.cache_data(ttl=60)
def load_data(url, file):
    try:
        if file is not None:
            return pd.read_excel(file, engine='openpyxl')
        direct_link = get_direct_download(url)
        if direct_link:
            return pd.read_excel(direct_link, engine='openpyxl')
    except: return None
    return None

# 2. OBRADA PODATAKA
df_raw = load_data(onedrive_url, uploaded_file)

if df_raw is not None:
    try:
        df = df_raw.copy()
        df.columns = [str(c).strip() for c in df.columns]
        
        # Sređivanje brojeva (zarezi u tačke)
        for col in df.columns:
            if col != "Mesec":
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')

        # KALKULACIJE
        df["COP"] = df["Proizvedena energija (kWh)"] / df["Potrošena struja (kWh)"]
        df["kWh/dan"] = df["Potrošena struja (kWh)"] / df["Dana u mesecu"]
        df["Startova/dan"] = df["Startovi kompresora"] / df["Dana u mesecu"]
        
        ukupna_proizvedena = df["Proizvedena energija (kWh)"].sum()
        ukupna_struja = df["Potrošena struja (kWh)"].sum()
        prosek_dan = df["kWh/dan"].mean()

        st.success("✅ Svi podaci su uspešno učitani!")

        # 3. SVIH 7 TABOVA
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📊 Pregled", "🌡 Kriva", "💡 EPS", "📅 Sezona", "🚀 OPTIMIZACIJA", "❄️ DEFROST", "💰 POREĐENJE"
        ])

        with tab1:
            st.subheader("📊 Mesečni izveštaj")
            st.dataframe(df.round(2), use_container_width=True)
            c1, c2 = st.columns(2)
            with c1:
                fig1, ax1 = plt.subplots(); ax1.bar(df["Mesec"], df["kWh/dan"], color="skyblue")
                ax1.set_title("Potrošnja (kWh/dan)"); st.pyplot(fig1); plt.close(fig1)
            with c2:
                fig2, ax2 = plt.subplots(); ax2.plot(df["Mesec"], df["COP"], marker="o", color="green")
                ax2.set_title("Efikasnost (COP)"); ax2.grid(True); st.pyplot(fig2); plt.close(fig2)

        with tab2:
            st.subheader("🌡 Analiza krive grejanja")
            fig3, ax3 = plt.subplots()
            ax3.scatter(df["Spoljna T (°C)"], df["LWT (°C)"], color="red", s=100, label="Realne tačke")
            tx = np.linspace(df["Spoljna T (°C)"].min()-2, df["Spoljna T (°C)"].max()+2, 10)
            ty = 38 - 0.4 * tx # Teoretska kriva 0.4
            ax3.plot(tx, ty, "--", color="gray", label="Kriva 0.4")
            ax3.set_xlabel("Spoljna Temperatura (°C)"); ax3.set_ylabel("Polaz Vode (LWT)"); ax3.legend()
            st.pyplot(fig3); plt.close(fig3)

        with tab3:
            st.subheader("💡 EPS i Troškovi")
            cena = st.number_input("Cena kWh (din)", value=10.5)
            racun = ukupna_struja * cena
            st.metric("Ukupan trošak za struju", f"{int(racun)} RSD")
            st.bar_chart(df, x="Mesec", y="Potrošena struja (kWh)")

        with tab4:
            st.subheader("📅 Projekcija sezone")
            dani_sezone = st.number_input("Trajanje sezone (dana)", value=180)
            st.metric("Predviđena potrošnja (kWh)", f"{int(prosek_dan * dani_sezone)}")

        with tab5:
            st.subheader("🚀 Simulator optimizacije")
            smanjenje = st.slider("Smanji LWT za (°C)", 0, 5, 1)
            usteda = prosek_dan * dani_sezone * (smanjenje * 0.03) # 3% po stepenu
            st.metric("Potencijalna ušteda", f"{int(usteda)} kWh")
            comfort = int(max(0, 100 - (df["Startova/dan"].mean() * 3)))
            st.write(f"**Stabilnost rada (Comfort Index):** {comfort}/100")

        with tab6:
            st.subheader("❄️ Analiza otapanja (Defrost)")
            v_def = st.slider("Minuta po defrostu", 5, 15, 8)
            n_def = st.slider("Defrosta po satu rada", 0.5, 3.0, 1.0)
            sati_kompr = df["Rad kompresora (h)"].sum()
            gubitak = (v_def / 60) * n_def * 5 * sati_kompr # 5kW prosek snage
            st.metric("Gubitak energije na defrost", f"{int(gubitak)} kWh")

        with tab7:
            st.subheader("💰 Poređenje sa drugim energentima")
            c_drva = st.number_input("Cena drva (din/m3)", value=9000)
            t_drva = (ukupna_proizvedena / (2000 * 0.7)) * c_drva
            st.success(f"Ušteda u odnosu na drva: {int(t_drva - racun)} RSD")
            st.info("Računica je bazirana na energetskoj vrednosti drveta i prosečnom COP-u.")

    except Exception as e:
        st.error(f"⚠️ Greška u tabeli: {e}")
        st.write("Proverite da li se kolone u Excelu zovu tačno: Mesec, Proizvedena energija (kWh), Potrošena struja (kWh), Rad kompresora (h), Rad pumpe (h), Startovi kompresora, LWT (°C), Spoljna T (°C), Dana u mesecu")
        st.write("Kolone koje vidim:", list(df_raw.columns))
else:
    st.warning("Čekam na podatke... Proverite OneDrive link ili učitajte Excel fajl.")
