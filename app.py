import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import base64

# 1. KONFIGURACIJA I LINK
st.set_page_config(page_title="Toplotna pumpa – PRO ANALIZA", layout="wide")
st.title("🔥 Toplotna pumpa – Automatska Analiza (V5.1)")

# --- OVDE UNESI SVOJ LINK SA ONEDRIVE-A ---
onedrive_share_url = "OVDE_ZALEPI_TVOJ_ONEDRIVE_LINK" 

# 2. FUNKCIJE ZA POVEZIVANJE
def create_onedrive_directdownload(onedrive_link):
    try:
        data_bytes64 = base64.b64encode(bytes(onedrive_link, 'utf-8'))
        data_bytes64_string = data_bytes64.decode('utf-8').replace('/','_').replace('+','-').rstrip("=")
        return f"https://api.onedrive.com/v1.1/shares/u!{data_bytes64_string}/root/content"
    except:
        return None

@st.cache_data(ttl=600) # Osvežava podatke svakih 10 minuta
def load_excel_data(url):
    direct_url = create_onedrive_directdownload(url)
    # Čita Excel fajl direktno sa oblaka
    return pd.read_excel(direct_url)

# 3. UČITAVANJE I OBRADA PODATAKA
try:
    if onedrive_share_url == "OVDE_ZALEPI_TVOJ_ONEDRIVE_LINK":
        st.warning("👈 Molimo unesite ispravan OneDrive link u kod da biste videli svoje podatke.")
        # Prikazujemo demo podatke dok ne ubaciš link
        df = pd.DataFrame({
            "Mesec": ["Novembar", "Decembar"],
            "Proizvedena energija (kWh)": [3065, 4432],
            "Potrošena struja (kWh)": [500, 1201],
            "Rad kompresora (h)": [514, 628],
            "Rad pumpe (h)": [683, 678],
            "Startovi kompresora": [1179, 418],
            "LWT (°C)": [32.4, 36.5],
            "Spoljna T (°C)": [8.0, 2.0],
            "Dana u mesecu": [30, 29],
        })
    else:
        df_raw = load_excel_data(onedrive_share_url)
        
        # Ako Excel ima kolonu "Datum", grupišemo ga na mesece
        if 'Datum' in df_raw.columns:
            df_raw['Datum'] = pd.to_datetime(df_raw['Datum'])
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
            df.rename(columns={'index': 'Mesec'}, inplace=True)
        else:
            df = df_raw
        st.success("✅ Podaci su uspešno povučeni sa OneDrive-a!")

except Exception as e:
    st.error(f"Greška pri povezivanju sa Excelom: {e}")
    st.info("Proverite da li su nazivi kolona u Excelu identični kao u aplikaciji.")
    st.stop()

# 4. IZRAČUNAVANJA
df["COP"] = df["Proizvedena energija (kWh)"] / df["Potrošena struja (kWh)"]
df["kWh/dan"] = df["Potrošena struja (kWh)"] / df["Dana u mesecu"]
df["Startova/dan"] = df["Startovi kompresora"] / df["Dana u mesecu"]

prosek_kwh_dan = df["kWh/dan"].mean()
ukupna_proizvedena = df["Proizvedena energija (kWh)"].sum()
ukupna_potrosnja_struje = df["Potrošena struja (kWh)"].sum()

# 5. TABOVI
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Pregled", "🌡 Kriva", "💡 EPS", "📅 Sezona", "🚀 OPTIMIZACIJA", "❄️ DEFROST", "💰 UŠTEDA VS DRUGI"
])

# --- TAB 1: PREGLED ---
with tab1:
    st.subheader("📊 Mesečni izveštaj")
    st.dataframe(df.round(2), use_container_width=True)
    colA, colB = st.columns(2)
    with colA:
        fig1, ax1 = plt.subplots(); ax1.bar(df.iloc[:,0], df["kWh/dan"], color="skyblue")
        ax1.set_title("Dnevna potrošnja (kWh/dan)"); st.pyplot(fig1); plt.close(fig1)
    with colB:
        fig2, ax2 = plt.subplots(); ax2.plot(df.iloc[:,0], df["COP"], marker="o", color="green")
        ax2.set_title("Efikasnost (COP)"); ax2.grid(True); st.pyplot(fig2); plt.close(fig2)

# --- TAB 2: KRIVA ---
with tab2:
    st.subheader("🌡 Kriva grejanja")
    fig3, ax3 = plt.subplots()
    ax3.scatter(df["Spoljna T (°C)"], df["LWT (°C)"], color="red", label="Realni podaci")
    tx = np.linspace(df["Spoljna T (°C)"].min()-2, df["Spoljna T (°C)"].max()+2, 10)
    ty = 38 - 0.4 * tx
    ax3.plot(tx, ty, "--", color="gray", label="Teoretska kriva")
    ax3.set_xlabel("Spoljna T"); ax3.set_ylabel("LWT"); ax3.legend()
    st.pyplot(fig3); plt.close(fig3)

# --- TAB 3: EPS ---
with tab3:
    st.subheader("💡 EPS i Troškovi")
    cena_kwh = st.number_input("Prosečna cena kWh sa mrežarinom (din)", value=10.5)
    st.bar_chart(df, x=df.columns[0], y="Potrošena struja (kWh)")
    trenutni_racun = ukupna_potrosnja_struje * cena_kwh
    st.metric("Ukupan trošak za struju (period)", f"{int(trenutni_racun)} din")

# --- TAB 4: SEZONA ---
with tab4:
    st.subheader("📅 Projekcija sezone")
    sezona_dana = st.number_input("Trajanje grejne sezone (dana)", value=180)
    projekcija_kwh = prosek_kwh_dan * sezona_dana
    st.metric("Predviđena potrošnja sezone", f"{int(projekcija_kwh)} kWh")

# --- TAB 5: OPTIMIZACIJA ---
with tab5:
    st.subheader("🚀 Simulator uštede")
    smanjenje = st.slider("Smanji LWT za (°C)", 0, 5, 1)
    usteda_kwh = projekcija_kwh * (smanjenje * 0.03)
    st.metric("Potencijalna ušteda", f"{int(usteda_kwh)} kWh")
    
    avg_starts = df["Startova/dan"].mean()
    comfort = int(max(0, 100 - (avg_starts * 3)))
    st.write(f"**Comfort Index (Stabilnost):** {comfort}/100")
    st.progress(comfort/100)

# --- TAB 6: DEFROST ---
with tab6:
    st.subheader("❄️ Analiza otapanja (Defrost)")
    v_def = st.slider("Minuta po defrostu", 5, 15, 8)
    n_def = st.slider("Defrosta po satu rada", 0.5, 3.0, 1.0)
    snaga = (ukupna_potrosnja_struje / df["Rad kompresora (h)"].sum()) if df["Rad kompresora (h)"].sum() > 0 else 5
    gubitak = (v_def / 60) * n_def * snaga * df["Rad kompresora (h)"].sum()
    st.metric("Gubitak na defrost", f"{int(gubitak)} kWh")

# --- TAB 7: POREĐENJE ---
with tab7:
    st.subheader("💰 Ušteda u odnosu na druge")
    c_drva = st.number_input("Cena drva (din/m3)", value=9000)
    c_gas = st.number_input("Cena gasa (din/m3)", value=55)
    
    t_drva = (ukupna_proizvedena / (2000 * 0.7)) * c_drva
    t_gas = (ukupna_proizvedena / (10 * 0.9)) * c_gas
    
    uporedni_data = pd.DataFrame({
        "Energent": ["Toplotna pumpa", "Drva", "Gas"],
        "Trošak (RSD)": [int(trenutni_racun), int(t_drva), int(t_gas)]
    })
    st.bar_chart(uporedni_data, x="Energent", y="Trošak (RSD)")
    st.success(f"Uštedeli ste {int(t_drva - trenutni_racun)} din u odnosu na drva!")

st.caption("Verzija 5.1 | Podaci se povlače sa OneDrive Excel-a")
