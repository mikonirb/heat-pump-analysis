import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import base64

# 1. KONFIGURACIJA
st.set_page_config(page_title="Toplotna pumpa – PRO ANALIZA", layout="wide")
st.title("🔥 Toplotna pumpa – Automatska Analiza (V5.1)")

https://1drv.ms/x/c/a15c6fc067062efb/IQD5_1Yj9WhfRafvHJ1x3Y-wAYVUR7tP6_uTeZ3gnxYa9o4?e=WDMEXv
# Mora biti unutar navodnika: "link"
onedrive_share_url = "ZALEPI_OVDE_SVOJ_LINK_IZ_ONEDRIVEA" 

# 2. FUNKCIJE ZA KONVERZIJU LINKA
def create_onedrive_directdownload(onedrive_link):
    try:
        # Kodiranje linka u Base64 format koji Microsoft Graph API prepoznaje
        data_bytes64 = base64.b64encode(bytes(onedrive_link, 'utf-8'))
        data_bytes64_string = data_bytes64.decode('utf-8').replace('/','_').replace('+','-').rstrip("=")
        return f"https://api.onedrive.com/v1.1/shares/u!{data_bytes64_string}/root/content"
    except Exception as e:
        st.error(f"Greška u formatu linka: {e}")
        return None

@st.cache_data(ttl=300) # Osvežava na 5 minuta
def load_excel_data(url):
    direct_url = create_onedrive_directdownload(url)
    if direct_url:
        # Čitamo Excel fajl direktno
        return pd.read_excel(direct_url)
    return None

# 3. GLAVNA LOGIKA UCITAVANJA
if onedrive_share_url == "ZALEPI_OVDE_SVOJ_LINK_IZ_ONEDRIVEA":
    st.info("💡 Molim vas unesite vaš OneDrive Share link u kod da biste videli podatke iz tabele 'baza za TP streamlit app.xlsx'.")
    st.stop()
else:
    try:
        df_raw = load_excel_data(onedrive_share_url)
        
        if df_raw is not None:
            # Ako unosiš dnevno (kolona Datum postoji)
            if 'Mesec' in df_raw.columns:
                df_raw['Mesec'] = pd.to_datetime(df_raw['Mesec'])
                # Grupišemo po mesecu (strftime %B izvlači ime meseca)
                df = df_raw.groupby(df_raw['Datum'].dt.strftime('%B'), sort=False).agg({
                    "Proizvedena energija (kWh)": "sum",
                    "Potrošena struja (kWh)": "sum",
                    "Rad kompresora (h)": "sum",
                    "Rad pumpe (h)": "sum",
                    "Startovi kompresora": "sum",
                    "LWT (°C)": "mean",
                    "Spoljna T (°C)": "mean",
                    "Dana u mesecu": "max"
                }).reset_index()
                df.rename(columns={'Datum': 'Mesec'}, inplace=True)
            else:
                df = df_raw
            
            st.success("✅ Podaci uspešno učitani iz fajla 'baza za TP streamlit app.xlsx'")
        else:
            st.error("Nije moguće dohvatiti podatke. Proverite link.")
            st.stop()

    except Exception as e:
        st.error(f"Kritična greška: {e}")
        st.warning("Savet: Proverite da li se kolone u Excelu zovu IDENTIČNO kao u kodu (velika/mala slova, razmaci, kWh u zagradi).")
        st.stop()

# --- DALJE IDU PRORAČUNI I TABOVI (Sve ostaje isto) ---
df["COP"] = df["Proizvedena energija (kWh)"] / df["Potrošena struja (kWh)"]
df["kWh/dan"] = df["Potrošena struja (kWh)"] / df["Dana u mesecu"]
df["Startova/dan"] = df["Startovi kompresora"] / df["Dana u mesecu"]

ukupna_proizvedena = df["Proizvedena energija (kWh)"].sum()
ukupna_struja = df["Potrošena struja (kWh)"].sum()
prosek_dan = df["kWh/dan"].mean()

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Pregled", "🌡 Kriva", "💡 EPS", "📅 Sezona", "🚀 OPTIMIZACIJA", "❄️ DEFROST", "💰 POREĐENJE"
])

with tab1:
    st.dataframe(df.round(2), use_container_width=True)
    c1, c2 = st.columns(2)
    with c1:
        fig1, ax1 = plt.subplots(); ax1.bar(df.iloc[:,0], df["kWh/dan"], color="skyblue")
        ax1.set_title("Potrošnja (kWh/dan)"); st.pyplot(fig1); plt.close(fig1)
    with c2:
        fig2, ax2 = plt.subplots(); ax2.plot(df.iloc[:,0], df["COP"], marker="o", color="green")
        ax2.set_title("COP"); ax2.grid(True); st.pyplot(fig2); plt.close(fig2)

with tab2:
    st.subheader("🌡 Kriva grejanja")
    fig3, ax3 = plt.subplots()
    ax3.scatter(df["Spoljna T (°C)"], df["LWT (°C)"], color="red", label="Realni podaci")
    tx = np.linspace(df["Spoljna T (°C)"].min()-2, df["Spoljna T (°C)"].max()+2, 10)
    ty = 38 - 0.4 * tx
    ax3.plot(tx, ty, "--", color="gray", label="Teoretska kriva")
    ax3.set_xlabel("Spoljna T"); ax3.set_ylabel("LWT"); ax3.legend()
    st.pyplot(fig3); plt.close(fig3)

with tab3:
    st.subheader("💡 EPS i Troškovi")
    cena = st.number_input("Cena kWh (din)", value=10.5)
    st.metric("Ukupan račun", f"{int(ukupna_struja * cena)} din")
    st.bar_chart(df, x=df.columns[0], y="Potrošena struja (kWh)")

with tab4:
    dani = st.number_input("Trajanje sezone (dana)", value=180)
    st.metric("Projekcija sezone", f"{int(prosek_dan * dani)} kWh")

with tab5:
    smanjenje = st.slider("Smanji LWT za (°C)", 0, 5, 1)
    st.metric("Potencijalna ušteda", f"{int(prosek_dan * dani * (smanjenje * 0.03))} kWh")

with tab6:
    v_def = st.slider("Minuta po defrostu", 5, 15, 8)
    n_def = st.slider("Defrosta po satu", 0.5, 3.0, 1.0)
    sati = df["Rad kompresora (h)"].sum()
    snaga = (ukupna_struja / sati) if sati > 0 else 5
    st.metric("Gubitak na defrost", f"{int((v_def/60)*n_def*snaga*sati)} kWh")

with tab7:
    c_drva = st.number_input("Cena drva (din/m3)", value=9000)
    t_drva = (ukupna_proizvedena / (2000 * 0.7)) * c_drva
    st.metric("Trošak na drva (za istu toplotu)", f"{int(t_drva)} din")
    st.metric("Ušteda sa pumpom", f"{int(t_drva - (ukupna_struja * cena))} din")
