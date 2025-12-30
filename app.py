import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import base64

# 1. KONFIGURACIJA
st.set_page_config(page_title="Toplotna pumpa – PRO ANALIZA", layout="wide")
st.title("🔥 Toplotna pumpa – Analiza (V5.5)")

# TVOJ LINK (Skraćen na bazu radi izbegavanja HTTP 400 greške)
onedrive_url = "https://1drv.ms/x/c/a15c6fc067062efb/IQD5_1Yj9WhfRafvHJ1x3Y-wAYVUR7tP6_uTeZ3gnxYa9o4"

def get_direct_download(url):
    try:
        # Kodiranje linka za direktan pristup fajlu
        s = base64.b64encode(bytes(url, 'utf-8')).decode('utf-8')
        return f"https://api.onedrive.com/v1.1/shares/u!{s.replace('/','_').replace('+','-').rstrip('=')}/root/content"
    except:
        return None

# Učitavanje fajla (Sidebar ili OneDrive)
st.sidebar.header("📁 Izvor podataka")
uploaded_file = st.sidebar.file_uploader("Učitaj Excel fajl direktno", type=["xlsx"])

@st.cache_data(ttl=60)
def load_data(url, file):
    try:
        if file is not None:
            # Koristimo openpyxl motor za stabilnost
            return pd.read_excel(file, engine='openpyxl')
        
        direct_link = get_direct_download(url)
        if direct_link:
            return pd.read_excel(direct_link, engine='openpyxl')
    except Exception as e:
        st.sidebar.error(f"Greška pri čitanju: {e}")
    return None

# 2. IZVRŠAVANJE
df_raw = load_data(onedrive_url, uploaded_file)

if df_raw is not None:
    try:
        df = df_raw.copy()
        df.columns = [c.strip() for c in df.columns]
        
        # Pretvaranje u brojeve i sređivanje zareza
        for col in df.columns:
            if col != "Mesec":
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')

        # 3. KALKULACIJE
        df["COP"] = df["Proizvedena energija (kWh)"] / df["Potrošena struja (kWh)"]
        df["kWh/dan"] = df["Potrošena struja (kWh)"] / df["Dana u mesecu"]
        
        ukupna_proizvedena = df["Proizvedena energija (kWh)"].sum()
        ukupna_struja = df["Potrošena struja (kWh)"].sum()
        prosek_dan = df["kWh/dan"].mean()

        st.success("✅ Podaci uspešno obrađeni!")

        # 4. TABOVI
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📊 Pregled", "🌡 Kriva", "💡 EPS", "📅 Sezona", "🚀 OPTIMIZACIJA", "❄️ DEFROST", "💰 POREĐENJE"
        ])

        with tab1:
            st.dataframe(df.round(2), use_container_width=True)
            c1, c2 = st.columns(2)
            with c1:
                fig1, ax1 = plt.subplots(); ax1.bar(df["Mesec"], df["kWh/dan"], color="#3498db")
                ax1.set_title("Potrošnja po danu"); st.pyplot(fig1); plt.close(fig1)
            with c2:
                fig2, ax2 = plt.subplots(); ax2.plot(df["Mesec"], df["COP"], marker="o", color="#2ecc71")
                ax2.set_title("COP (Mesečno)"); ax2.grid(True); st.pyplot(fig2); plt.close(fig2)

        with tab2:
            st.subheader("🌡 Kriva grejanja (LWT vs Spoljna T)")
            fig3, ax3 = plt.subplots()
            ax3.scatter(df["Spoljna T (°C)"], df["LWT (°C)"], color="red", s=100)
            st.pyplot(fig3); plt.close(fig3)

        with tab3:
            cena = st.number_input("Cena struje (din/kWh)", value=10.5)
            st.metric("Ukupan trošak", f"{int(ukupna_struja * cena)} din")

        with tab4:
            dani = st.number_input("Dana sezone", value=180)
            st.metric("Projektovana sezona", f"{int(prosek_dan * dani)} kWh")

        with tab5:
            smanjenje = st.slider("Smanjenje LWT (°C)", 0, 5, 1)
            st.write(f"Ušteda: {int(prosek_dan * dani * (smanjenje * 0.03))} kWh")

        with tab6:
            st.subheader("❄️ Defrost Analiza")
            v_def = st.slider("Minuti po defrostu", 5, 15, 8)
            st.write(f"Procena gubitka: {int((v_def/60) * 1.0 * 5 * df['Rad kompresora (h)'].sum())} kWh")

        with tab7:
            st.subheader("💰 Poređenje")
            c_drva = st.number_input("Cena drva (din/m3)", value=9000)
            t_drva = (ukupna_proizvedena / (2000 * 0.7)) * c_drva
            st.success(f"Ušteda vs Drva: {int(t_drva - (ukupna_struja * cena))} din")

    except Exception as e:
        st.error(f"⚠️ Proveri nazive kolona u Excelu: {e}")
        st.write("Kolone koje vidim:", list(df_raw.columns))
else:
    st.info("Povežite OneDrive link u kodu ili prevucite Excel fajl u polje sa leve strane.")
