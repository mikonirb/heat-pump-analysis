import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import base64

# 1. KONFIGURACIJA
st.set_page_config(page_title="Toplotna pumpa – PRO ANALIZA", layout="wide")
st.title("🔥 Toplotna pumpa – Analiza (V5.3)")

# TVOJ LINK - Očišćen od dodatnih parametara radi stabilnosti
raw_url = "https://1drv.ms/x/c/a15c6fc067062efb/IQD5_1Yj9WhfRafvHJ1x3Y-wAYVUR7tP6_uTeZ3gnxYa9o4?e=T6GbOQ"

def get_direct_download(url):
    try:
        # Čistimo link ako ima parametre poput ?e=...
        clean_url = url.split('?')[0]
        s = base64.b64encode(bytes(clean_url, 'utf-8')).decode('utf-8')
        return f"https://api.onedrive.com/v1.1/shares/u!{s.replace('/','_').replace('+','-').rstrip('=')}/root/content"
    except:
        return None

@st.cache_data(ttl=60)
def load_data(url):
    direct_link = get_direct_download(url)
    if direct_link:
        # Čitamo Excel i automatski zamenjujemo zareze tačkama za brojeve
        return pd.read_excel(direct_link)
    return None

# 2. UCITAVANJE
try:
    df = load_data(raw_url)
    
    if df is not None:
        # Standardizacija naziva kolona
        df.columns = [c.strip() for c in df.columns]
        
        # Pretvaranje kolona u brojeve (u slučaju da su zarezi napravili problem)
        cols_to_fix = ["Potrošena struja (kWh)", "Proizvedena energija (kWh)", "LWT (°C)", "Spoljna T (°C)"]
        for col in cols_to_fix:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')

        # 3. IZRAČUNAVANJA
        df["COP"] = df["Proizvedena energija (kWh)"] / df["Potrošena struja (kWh)"]
        df["kWh/dan"] = df["Potrošena struja (kWh)"] / df["Dana u mesecu"]
        df["Startova/dan"] = df["Startovi kompresora"] / df["Dana u mesecu"]

        ukupna_proizvedena = df["Proizvedena energija (kWh)"].sum()
        ukupna_struja = df["Potrošena struja (kWh)"].sum()
        prosek_dan = df["kWh/dan"].mean()

        st.success(f"✅ Podaci uspešno učitani! (Pronađeno meseci: {len(df)})")

        # 4. TABOVI
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📊 Pregled", "🌡 Kriva", "💡 EPS", "📅 Sezona", "🚀 OPTIMIZACIJA", "❄️ DEFROST", "💰 POREĐENJE"
        ])

        with tab1:
            st.dataframe(df.round(2), use_container_width=True)
            c1, c2 = st.columns(2)
            with c1:
                fig1, ax1 = plt.subplots(); ax1.bar(df["Mesec"], df["kWh/dan"], color="skyblue")
                ax1.set_title("Potrošnja (kWh/dan)"); st.pyplot(fig1); plt.close(fig1)
            with c2:
                fig2, ax2 = plt.subplots(); ax2.plot(df["Mesec"], df["COP"], marker="o", color="green")
                ax2.set_title("Efikasnost (COP)"); ax2.grid(True); st.pyplot(fig2); plt.close(fig2)

        with tab2:
            st.subheader("🌡 Kriva grejanja")
            fig3, ax3 = plt.subplots()
            ax3.scatter(df["Spoljna T (°C)"], df["LWT (°C)"], color="red", s=100, label="Realni podaci")
            tx = np.linspace(df["Spoljna T (°C)"].min()-2, df["Spoljna T (°C)"].max()+2, 10)
            ty = 38 - 0.4 * tx
            ax3.plot(tx, ty, "--", color="gray", label="Teoretska kriva")
            ax3.set_xlabel("Spoljna Temperatura (°C)"); ax3.set_ylabel("LWT (°C)"); ax3.legend()
            st.pyplot(fig3); plt.close(fig3)

        with tab3:
            cena = st.number_input("Cena kWh (din)", value=10.5)
            st.metric("Ukupan račun", f"{int(ukupna_struja * cena)} din")
            st.bar_chart(df, x="Mesec", y="Potrošena struja (kWh)")

        with tab4:
            dani = st.number_input("Trajanje sezone (dana)", value=180)
            st.metric("Projekcija sezone", f"{int(prosek_dan * dani)} kWh")

        with tab5:
            smanjenje = st.slider("Smanji LWT za (°C)", 0, 5, 1)
            st.info(f"Smanjenjem za {smanjenje}°C štedite oko {int(prosek_dan * dani * (smanjenje * 0.03))} kWh.")

        with tab6:
            v_def = st.slider("Minuta po defrostu", 5, 15, 8)
            n_def = st.slider("Defrosta po satu", 0.5, 3.0, 1.0)
            sati_rada = df["Rad kompresora (h)"].sum()
            st.metric("Gubitak na defrost", f"{int((v_def/60)*n_def*5*sati_rada)} kWh")

        with tab7:
            c_drva = st.number_input("Cena drva (din/m3)", value=9000)
            t_drva = (ukupna_proizvedena / (2000 * 0.7)) * c_drva
            st.success(f"Ušteda u odnosu na drva: {int(t_drva - (ukupna_struja * cena))} din")

    else:
        st.error("Greška: Podaci nisu učitani. Proverite OneDrive link.")

except Exception as e:
    st.error(f"⚠️ Došlo je do greške: {e}")
    if 'df' in locals() and df is not None:
        st.write("Sistem u Excelu vidi ove kolone:", list(df.columns))
