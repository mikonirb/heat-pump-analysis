import streamlit as st
import pandas as pd
import numpy as np
import base64
import requests


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

st.title("🔥 Toplotna pumpa – Kompletna Analiza Daikin EBLQ16")

# --- NOVI PRISTUP (Direktno čitanje taba Potrosnja) ---
# --- PROVERENI LINK FORMAT ---
SHEET_ID = "1NGaf83t82G9tjsL_5wsvYNYvKii8A0biUXJkzsm9Bf8"  # Ubaci ID tvoje Google tabele
SHEET_NAME = "Potrosnja"

# Ovaj link direktno izvozi tab u CSV format
gsheet_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=344695767"

# NAPOMENA: Ako "Potrosnja" nije prvi tab u tabeli, moramo naći njegov GID.
# GID vidiš u URL-u brauzera kada klikneš na taj tab (piše na kraju: gid=123456)
@st.cache_data(ttl=60)
def load_data(url):
    try:
        # Čitamo kao CSV jer je brže i pouzdanije za Streamlit
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Greška pri povlačenju podataka: {e}")
        return None
@st.cache_data(ttl=3600)
def get_weather_forecast(lat, lon):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&daily=temperature_2m_min,temperature_2m_max"
        "&forecast_days=7&timezone=auto"
    )
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()
    
    df_w = pd.DataFrame({
        "Dan": data["daily"]["time"],
        "T_min (°C)": data["daily"]["temperature_2m_min"],
        "T_max (°C)": data["daily"]["temperature_2m_max"]
    })
    
    df_w["Spoljna T (°C)"] = (df_w["T_min (°C)"] + df_w["T_max (°C)"]) / 2
    return df_w


# 2. OBRADA PODATAKA
df_raw = load_data(gsheet_url)

# Ako Google link ne radi, dajemo opciju ručnog uploada kao rezervu
st.sidebar.header("📁 Izvor podataka")
uploaded_file = st.sidebar.file_uploader("Ili učitaj Excel ručno", type=["xlsx"])

st.sidebar.header("📍 Lokacija (za prognozu)")
lat = st.sidebar.number_input("Geografska širina", value=43.3)
lon = st.sidebar.number_input("Geografska dužina", value=21.9)

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
        df["Rad Komp %"] = (df["Rad kompresora (h)"] / df["Rad pumpe (h)"]) * 100
        df["Snaga (kW)"] = df["Proizvedena energija (kWh)"] / df["Rad kompresora (h)"]
        
        ukupna_proizvedena = df["Proizvedena energija (kWh)"].sum()
        ukupna_struja = df["Potrošena struja (kWh)"].sum()
        prosek_dan = df["kWh/dan"].mean()

        st.success("✅ Podaci uspešno učitani!")

        # 3. SVIH 7 TABOVA
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
            "📊 Pregled", "🌡 Kriva", "💡 EPS", "📅 Sezona",
            "🚀 OPTIMIZACIJA", "❄️ DEFROST", "💰 POREĐENJE",
            "📈 DNEVNA PROGNOZA", "🌦 Vremenska prognoza i preporučeni LWT"
        ])

        with tab1:
            st.subheader("📊 Mesečni i Sezonski izveštaj")
        
            # --- NOVO: KALKULACIJA SEZONSKOG COP-a ---
            sezonski_cop = df["Proizvedena energija (kWh)"].sum() / df["Potrošena struja (kWh)"].sum()
            poslednji_red = df.iloc[-1]
            
            # Prikaz ključnih metrika u redu
            m0, m1, m2, m3 = st.columns(4)
            m0.metric("SEZONSKI COP (Sveukupno)", f"{sezonski_cop:.2f}", help="Ukupna proizvedena energija / Ukupna potrošena struja")
            m1.metric("Opterećenje (Komp/Pumpa)", f"{poslednji_red['Rad Komp %']:.1f} %")
            m2.metric("Prosečna Snaga", f"{poslednji_red['Snaga (kW)']:.2f} kW")
            m3.metric("Trenutni Mesečni COP", f"{poslednji_red['COP']:.2f}")
            
            st.divider()
        
            # Tabela sa podacima
            st.write("### 📋 Pregled podataka po mesecima")
            st.dataframe(df.round(2), use_container_width=True)
            
            st.divider()
        
            # Grafikoni
            c1, c2 = st.columns(2)
            with c1:
                fig1, ax1 = plt.subplots()
                ax1.bar(df["Mesec"], df["kWh/dan"], color="skyblue")
                ax1.set_title("Potrošnja (kWh/dan)")
                st.pyplot(fig1)
                plt.close(fig1)
            
            with c2:
                fig2, ax2 = plt.subplots()
                ax2.plot(df["Mesec"], df["COP"], marker="o", color="green", label="Mesečni COP")
                # Dodajemo liniju za Sezonski COP na grafikon radi poređenja
                ax2.axhline(y=sezonski_cop, color='r', linestyle='--', label=f"Sezonski prosek ({sezonski_cop:.2f})")
                ax2.set_title("Efikasnost (COP)")
                ax2.legend()
                ax2.grid(True)
                st.pyplot(fig2)
                plt.close(fig2)
            
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
                cena_peleta = st.number_input("Cena peleta (din/kg)", value=46)
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
                
            from datetime import date, timedelta
            

        with tab8:
            st.subheader("📈 Prognoza potrošnje na 30 dana (EPS Granica)")
            
            from datetime import date
            
            # 1. Izbor meseca iz baze
            meseci = df["Mesec"].astype(str).unique().tolist()
            izabrani_mesec = st.selectbox("Izaberi mesec", meseci, index=len(meseci)-1)
            
            # 2. Podaci o potrošnji iz reda koji si izabrao
            red_iz_baze = df[df["Mesec"].astype(str) == izabrani_mesec].iloc[0]
            trenutna_potrosnja = float(red_iz_baze["Potrošena struja (kWh)"])
            
            # --- KLJUČNA MATEMATIKA ---
            
            # Broj proteklih dana (Danas je 7. januar, dakle 7)
            danasnji_dan = date.today().day
            
            # Dnevni prosek (npr. 386 / 7 = 55.14)
            dnevni_prosek = trenutna_potrosnja / danasnji_dan
            
            # PROGNOZA NA 30 DANA (Fiksno 30 dana kako si tražio)
            prognoza_30_dana = dnevni_prosek * 30
            
            # --- PRIKAZ ---
            st.info(f"Obračun: {trenutna_potrosnja} kWh / {danasnji_dan} dana × 30 dana")
            
            col1, col2, col3 = st.columns(3)
            
            col1.metric("Dnevni prosek", f"{dnevni_prosek:.2f} kWh")
            col2.metric("Potrošeno (7 dana)", f"{int(trenutna_potrosnja)} kWh")
            
            # Očekivani rezultat: (386 / 7) * 30 = 1654 kWh
            col3.metric("PROGNOZA (30 DANA)", f"{int(prognoza_30_dana)} kWh")

            st.divider()

            # PROVERA GRANICE OD 1200 kWh (Plava/Crvena zona)
            granica = 1200
            if prognoza_30_dana > granica:
                razlika = prognoza_30_dana - granica
                st.error(f"🚨 ALARM: Sa ovim prosekom prelaziš granicu od {granica} kWh!")
                st.warning(f"Projektovana potrošnja je **{int(razlika)} kWh iznad** limita za plavu zonu.")
            else:
                st.success(f"✅ STATUS: Prognoza ({int(prognoza_30_dana)} kWh) je unutar granice od {granica} kWh.")
            
        with tab9:
            st.subheader("🌦 Vremenska prognoza i preporučeni LWT (V6.1)")
            
            try:
                prog = get_weather_forecast(lat, lon)
            
                # konzervativna kriva
                prog["Preporučeni LWT (°C)"] = 40 - 0.25 * prog["Spoljna T (°C)"]
            
                st.dataframe(prog.round(1), use_container_width=True)
            
                # grafikon
                fig, ax = plt.subplots()
                ax.plot(prog["Dan"], prog["Preporučeni LWT (°C)"], marker="o")
                ax.set_ylabel("LWT (°C)")
                ax.set_title("Preporučeni LWT za narednih 7 dana")
                ax.grid(True)
                st.pyplot(fig); plt.close(fig)
            
                # defrost upozorenje
                if (prog["T_min (°C)"] < 2).any():
                    st.warning("❄️ Najavljene minimalne temperature ispod 2 °C – mogući češći defrosti.")
                else:
                    st.success("✅ Nema povećanog rizika od defrosta.")
            
            except Exception as e:
                st.error("Nije moguće učitati prognozu – koristi ručni unos.")
                st.write(e)
            
                # fallback – ručni unos
                fallback = st.data_editor(
                    pd.DataFrame({
                        "Dan": ["D+1", "D+2", "D+3"],
                        "Spoljna T (°C)": [5, 4, 3]
                    }),
                    use_container_width=True
                )
                fallback["Preporučeni LWT (°C)"] = 40 - 0.25 * fallback["Spoljna T (°C)"]
                st.dataframe(fallback.round(1), use_container_width=True)


    
    except Exception as e:
        st.error(f"⚠️ Došlo je do greške u kolonama: {e}")
        st.write("Sistem u tabeli vidi ove kolone:", list(df_raw.columns))
else:
    st.warning("Čekam podatke... Unesi Google Sheets link u kod ili učitaj fajl ručno levo.")
