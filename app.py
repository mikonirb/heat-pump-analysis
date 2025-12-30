import streamlit as st
import pandas as pd
import numpy as np
import base64
import os

# Pokušaj uvoza matplotlib-a (čeka se instalacija iz requirements.txt)
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# 1. OSNOVNA PODEŠAVANJA (Mora biti prva Streamlit komanda)
st.set_page_config(page_title="Toplotna pumpa – PRO ANALIZA", layout="wide")

# 2. PROVERA INSTALACIJE
if not HAS_MATPLOTLIB:
    st.title("⏳ Instalacija u toku...")
    st.info("Streamlit instalira potrebne dodatke (matplotlib, pandas...). Osvežite stranicu za 1 minut.")
    st.stop()

st.title("🔥 Toplotna pumpa – Analiza (V5.6)")

# --- KONFIGURACIJA IZVORA ---
onedrive_url = "https://1drv.ms/x/c/a15c6fc067062efb/IQD5_1Yj9WhfRafvHJ1x3Y-wAYVUR7tP6_uTeZ3gnxYa9o4"

def get_direct_download(url):
    try:
        # Čišćenje linka od parametara i enkodiranje
        clean_url = url.split('?')[0]
        s = base64.b64encode(bytes(clean_url, 'utf-8')).decode('utf-8')
        return f"https://api.onedrive.com/v1.1/shares/u!{s.replace('/','_').replace('+','-').rstrip('=')}/root/content"
    except:
        return None

# Sidebar za ručni upload
st.sidebar.header("📁 Podešavanja")
uploaded_file = st.sidebar.file_uploader("Učitaj Excel ručno", type=["xlsx"])

@st.cache_data(ttl=60)
def load_data(url, file):
    try:
        if file is not None:
            return pd.read_excel(file, engine='openpyxl')
        
        direct_link = get_direct_download(url)
        if direct_link:
            return pd.read_excel(direct_link, engine='openpyxl')
    except Exception as e:
        st.sidebar.warning(f"OneDrive nije povezan: {e}")
    return None

# 3. PROCESIRANJE PODATAKA
df_raw = load_data(onedrive_url, uploaded_file)

if df_raw is not None:
    try:
        df = df_raw.copy()
        # Čišćenje naziva kolona (uklanjanje nevidljivih razmaka)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Konverzija zareza u tačke i pretvaranje u brojeve
        for col in df.columns:
            if col != "Mesec":
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')

        # Izračunavanja
        df["COP"] = df["Proizvedena energija (kWh)"] / df["Potrošena struja (kWh)"]
        df["kWh/dan"] = df["Potrošena struja (kWh)"] / df["Dana u mesecu"]
        
        st.success("✅ Podaci uspešno učitani!")

        # 4. PRIKAZ ANALIZE
        tab1, tab2, tab3 = st.tabs(["📊 Analitika", "🌡 Tehnički parametri", "💰 Ekonomska ušteda"])

        with tab1:
            st.dataframe(df.round(2), use_container_width=True)
            col1, col2 = st.columns(2)
            with col1:
                fig1, ax1 = plt.subplots(); ax1.bar(df["Mesec"], df["kWh/dan"], color="skyblue")
                ax1.set_ylabel("kWh/dan"); ax1.set_title("Potrošnja po danu"); st.pyplot(fig1); plt.close(fig1)
            with col2:
                fig2, ax2 = plt.subplots(); ax2.plot(df["Mesec"], df["COP"], marker="o", color="green")
                ax2.set_ylabel("COP"); ax2.set_title("Efikasnost"); st.pyplot(fig2); plt.close(fig2)

        with tab2:
            st.subheader("Odnos spoljne temperature i polaza vode (LWT)")
            fig3, ax3 = plt.subplots()
            ax3.scatter(df["Spoljna T (°C)"], df["LWT (°C)"], color="red", s=100)
            ax3.set_xlabel("Spoljna T (°C)"); ax3.set_ylabel("LWT (°C)"); st.pyplot(fig3); plt.close(fig3)

        with tab3:
            cena_kwh = st.sidebar.number_input("Cena kWh (din)", value=10.5)
            ukupna_struja = df["Potrošena struja (kWh)"].sum()
            ukupna_toplota = df["Proizvedena energija (kWh)"].sum()
            
            st.metric("Ukupna potrošnja struje", f"{int(ukupna_struja)} kWh")
            st.metric("Prosečan sezonski COP", f"{round(df['COP'].mean(), 2)}")
            
            # Poređenje sa drvima (procenjena energetska vrednost)
            t_drva = (ukupna_toplota / 1400) * 9000  # 1400kWh po m3 drva
            st.info(f"Približna ušteda u odnosu na drva: {int(t_drva - (ukupna_struja * cena_kwh))} dinara.")

    except Exception as e:
        st.error(f"⚠️ Problem sa tabelom: {e}")
        st.write("Sistem vidi ove kolone u Excelu:", list(df_raw.columns))
else:
    st.warning("Nisu pronađeni podaci. Proverite OneDrive link ili učitajte .xlsx fajl preko bočnog menija.")
