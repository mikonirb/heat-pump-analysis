import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import base64

# 1. KONFIGURACIJA
st.set_page_config(page_title="Toplotna pumpa – PRO ANALIZA", layout="wide")
st.title("🔥 Toplotna pumpa – Analiza (V5.4)")

# --- OPCIJA 1: OneDrive Link (Zameni link ako ga imaš ispravnog) ---
onedrive_url = "https://1drv.ms/x/c/a15c6fc067062efb/IQD5_1Yj9WhfRafvHJ1x3Y-wAYVUR7tP6_uTeZ3gnxYa9o4?e=0miRww"

def get_direct_download(url):
    try:
        s = base64.b64encode(bytes(url, 'utf-8')).decode('utf-8')
        return f"https://api.onedrive.com/v1.1/shares/u!{s.replace('/','_').replace('+','-').rstrip('=')}/root/content"
    except: return None

# --- OPCIJA 2: Ručno učitavanje ako link ne radi ---
st.sidebar.header("📁 Izvor podataka")
uploaded_file = st.sidebar.file_uploader("Ili učitaj Excel fajl direktno", type=["xlsx"])

@st.cache_data(ttl=60)
def load_data(url, file):
    if file is not None:
        return pd.read_excel(file)
    direct_link = get_direct_download(url)
    if direct_link:
        try:
            return pd.read_excel(direct_link)
        except: return None
    return None

# 2. IZVRŠAVANJE UCITAVANJA
df = load_data(onedrive_url, uploaded_file)

if df is not None:
    try:
        # Čišćenje naziva kolona i podataka
        df.columns = [c.strip() for c in df.columns]
        
        # Popravka zareza u tačke ako su brojevi uvezeni kao tekst
        for col in df.columns:
            if col != "Mesec":
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')

        # 3. IZRAČUNAVANJA
        df["COP"] = df["Proizvedena energija (kWh)"] / df["Potrošena struja (kWh)"]
        df["kWh/dan"] = df["Potrošena struja (kWh)"] / df["Dana u mesecu"]
        
        # Osnovne metrike
        ukupna_proizvedena = df["Proizvedena energija (kWh)"].sum()
        ukupna_struja = df["Potrošena struja (kWh)"].sum()
        prosek_dan = df["kWh/dan"].mean()

        st.success("✅ Podaci su spremni!")

        # 4. TABOVI
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📊 Pregled", "🌡 Kriva", "💡 EPS", "📅 Sezona", "🚀 OPTIMIZACIJA", "❄️ DEFROST", "💰 POREĐENJE"
        ])

        with tab1:
            st.subheader("📊 Tabela i grafikoni")
            st.dataframe(df.round(2), use_container_width=True)
            c1, c2 = st.columns(2)
            with c1:
                fig1, ax1 = plt.subplots(); ax1.bar(df["Mesec"], df["kWh/dan"], color="#3498db")
                ax1.set_title("Dnevna potrošnja (kWh)"); st.pyplot(fig1); plt.close(fig1)
            with c2:
                fig2, ax2 = plt.subplots(); ax2.plot(df["Mesec"], df["COP"], marker="o", color="#2ecc71")
                ax2.set_title("COP (Efikasnost)"); ax2.grid(True); st.pyplot(fig2); plt.close(fig2)

        with tab2:
            st.subheader("🌡 Analiza krive")
            fig3, ax3 = plt.subplots()
            ax3.scatter(df["Spoljna T (°C)"], df["LWT (°C)"], color="red", s=100, label="Tvoj rad")
            tx = np.linspace(df["Spoljna T (°C)"].min()-2, df["Spoljna T (°C)"].max()+2, 10)
            ty = 38 - 0.4 * tx
            ax3.plot(tx, ty, "--", color="gray", label="Idealna kriva")
            ax3.set_xlabel("Spoljna T"); ax3.set_ylabel("LWT"); ax3.legend(); st.pyplot(fig3); plt.close(fig3)

        with tab3:
            cena = st.number_input("Cena struje (din/kWh)", value=10.5)
            st.metric("Ukupan trošak", f"{int(ukupna_struja * cena)} RSD")
            st.bar_chart(df, x="Mesec", y="Potrošena struja (kWh)")

        with tab4:
            dani = st.number_input("Broj dana grejanja", value=180)
            st.metric("Projektovana sezona", f"{int(prosek_dan * dani)} kWh")

        with tab5:
            smanjenje = st.slider("Smanjenje LWT (°C)", 0, 5, 1)
            st.info(f"Potencijalna ušteda: {int(prosek_dan * dani * (smanjenje * 0.03))} kWh")

        with tab6:
            v_def = st.slider("Trajanje defrosta (min)", 5, 15, 8)
            n_def = st.slider("Defrosta po satu", 0.5, 3.0, 1.0)
            st.metric("Gubitak na otapanje", f"{int((v_def/60)*n_def*5*df['Rad kompresora (h)'].sum())} kWh")

        with tab7:
            c_drva = st.number_input("Cena drva (din/m3)", value=9000)
            t_drva = (ukupna_proizvedena / (2000 * 0.7)) * c_drva
            st.success(f"Ušteda u odnosu na drva: {int(t_drva - (ukupna_struja * cena))} din")

    except Exception as e:
        st.error(f"Greška u strukturi tabele: {e}")
        st.write("Proveri da li su nazivi kolona u Excelu tačni.")
else:
    st.info("Povežite se na OneDrive ili prevucite Excel fajl u polje sa leve strane (Sidebar).")
