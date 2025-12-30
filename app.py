import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import base64

# 1. KONFIGURACIJA
st.set_page_config(page_title="Toplotna pumpa – PRO ANALIZA", layout="wide")
st.title("🔥 Toplotna pumpa – Automatska Analiza (V5.2)")

https://1drv.ms/x/c/a15c6fc067062efb/IQD5_1Yj9WhfRafvHJ1x3Y-wAYVUR7tP6_uTeZ3gnxYa9o4?e=nhMfy3
onedrive_url = "https://1drv.ms/x/c/a15c6fc067062efb/IQD5_1Yj9WhfRafvHJ1x3Y-wAYVUR7tP6_uTeZ3gnxYa9o4?e=WDMEXv"

def get_direct_download(url):
    try:
        # Kodiranje za Microsoft Graph API
        s = base64.b64encode(bytes(url, 'utf-8')).decode('utf-8')
        return f"https://api.onedrive.com/v1.1/shares/u!{s.replace('/','_').replace('+','-').rstrip('=')}/root/content"
    except:
        return None

@st.cache_data(ttl=300)
def load_data(url):
    direct_link = get_direct_download(url)
    if direct_link:
        # Čitanje Excela - direktno, bez dodatnih komplikacija
        return pd.read_excel(direct_link)
    return None

# 2. UCITAVANJE
try:
    df = load_data(onedrive_url)
    
    if df is not None:
        # Standardizacija: brisanje praznih mesta u nazivima kolona
        df.columns = [c.strip() for c in df.columns]
        
        st.success("✅ Podaci uspešno učitani iz mesečne baze!")
        
        # PROVERA KOLONA: Ako se kolona zove 'Mesec', aplikacija nastavlja normalno
        # Ako tvoj Excel ima drugačija imena, ovde će pući, ali će ispisati poruku ispod
        
        # 3. IZRAČUNAVANJA
        df["COP"] = df["Proizvedena energija (kWh)"] / df["Potrošena struja (kWh)"]
        df["kWh/dan"] = df["Potrošena struja (kWh)"] / df["Dana u mesecu"]
        df["Startova/dan"] = df["Startovi kompresora"] / df["Dana u mesecu"]

        ukupna_proizvedena = df["Proizvedena energija (kWh)"].sum()
        ukupna_struja = df["Potrošena struja (kWh)"].sum()
        prosek_dan = df["kWh/dan"].mean()

        # 4. PRIKAZ TABOVA
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📊 Pregled", "🌡 Kriva", "💡 EPS", "📅 Sezona", "🚀 OPTIMIZACIJA", "❄️ DEFROST", "💰 POREĐENJE"
        ])

        with tab1:
            st.subheader("📊 Mesečni podaci")
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
            ax3.scatter(df["Spoljna T (°C)"], df["LWT (°C)"], color="red", label="Realni podaci")
            # Crtanje teoretske krive
            tx = np.linspace(df["Spoljna T (°C)"].min()-2, df["Spoljna T (°C)"].max()+2, 10)
            ty = 38 - 0.4 * tx
            ax3.plot(tx, ty, "--", color="gray", label="Teoretska kriva")
            ax3.set_xlabel("Spoljna T"); ax3.set_ylabel("LWT"); ax3.legend()
            st.pyplot(fig3); plt.close(fig3)

        with tab3:
            st.subheader("💡 EPS i Troškovi")
            cena = st.number_input("Cena kWh (din)", value=10.5)
            st.metric("Ukupan račun (period)", f"{int(ukupna_struja * cena)} din")
            st.bar_chart(df, x="Mesec", y="Potrošena struja (kWh)")

        with tab4:
            st.subheader("📅 Sezonska projekcija")
            dani = st.number_input("Trajanje sezone (dana)", value=180)
            st.metric("Predviđena potrošnja", f"{int(prosek_dan * dani)} kWh")

        with tab5:
            st.subheader("🚀 Optimizacija")
            smanjenje = st.slider("Smanji LWT za (°C)", 0, 5, 1)
            st.info(f"Smanjenjem za {smanjenje}°C štedite oko {int(prosek_dan * dani * (smanjenje * 0.03))} kWh.")
            avg_starts = df["Startova/dan"].mean()
            st.write(f"**Comfort Index:** {int(max(0, 100 - (avg_starts * 3)))}/100")

        with tab6:
            st.subheader("❄️ Defrost")
            v_def = st.slider("Minuta po defrostu", 5, 15, 8)
            n_def = st.slider("Defrosta po satu", 0.5, 3.0, 1.0)
            sati_rada = df["Rad kompresora (h)"].sum()
            st.metric("Procenjen gubitak na defrost", f"{int((v_def/60)*n_def*5*sati_rada)} kWh")

        with tab7:
            st.subheader("💰 Poređenje energenata")
            c_drva = st.number_input("Cena drva (din/m3)", value=9000)
            t_drva = (ukupna_proizvedena / (2000 * 0.7)) * c_drva
            st.success(f"Ušteda u odnosu na drva: {int(t_drva - (ukupna_struja * cena))} din")

    else:
        st.error("Greška: Link nije dostupan.")

except Exception as e:
    st.error(f"⚠️ Došlo je do greške u kolonama: {e}")
    if 'df' in locals() and df is not None:
        st.write("Kolone koje sistem vidi u tvom Excelu su:", list(df.columns))
    st.info("Savet: Proveri da li se prva kolona zove 'Mesec' (sa velikim M).")
