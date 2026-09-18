import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import date, timedelta

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

# --- 1. LINKOVI KA GOOGLE SHEETS ---
# Tekuća sezona
LINK_TEKUCA_SEZONA = "https://docs.google.com/spreadsheets/d/17KazEx-_lCzilvrxHwt8V7WMltRmEEXj/edit?gid=239587151#gid=239587151"

# Prošla sezona (AKO SU U ISTOM FAJLU, ZAMJENI SAMO GID NAKON gid=)
# Ako je druga tabela, provjeri da li je ID tačan i postaviti "Anyone with the link can view"
LINK_PROSLA_SEZONA = "https://docs.google.com/spreadsheets/d/1biFB6MgHp6e2gq5l-Kr0Ey1ynrOjnas0/edit?gid=239587151#gid=239587151"


def build_csv_export_url(url):
    """Generiše čist CSV export link."""
    try:
        if "/export?" in url:
            return url
        sheet_id = url.split("/d/")[1].split("/")[0]
        gid = "0"
        if "gid=" in url:
            gid = url.split("gid=")[1].split("#")[0].split("&")[0]
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    except Exception:
        return url

gsheet_url_tekuca = build_csv_export_url(LINK_TEKUCA_SEZONA)
gsheet_url_prosla = build_csv_export_url(LINK_PROSLA_SEZONA)


@st.cache_data(ttl=60)
def load_data(url):
    try:
        df = pd.read_csv(url)
        return df
    except Exception as e:
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


def clean_dataframe(df_raw):
    """Pomoćna funkcija za čišćenje i formatiranje tabele sa zaštitom od NaN vrednosti."""
    if df_raw is None:
        return None
    df = df_raw.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(columns={"Startovi kompresora": "Startovi"})
    
    # Uklanjanje praznih redova i sumarnih redova
    df = df[df["Mesec"].notna()]
    df = df[~df["Mesec"].astype(str).str.lower().str.contains("ukupno|suma|total")]
    
    for col in df.columns:
        if col != "Mesec":
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
            
    # Kalkulacije
    df["COP"] = df["Proizvedena energija (kWh)"] / df["Potrošena struja (kWh)"]
    df["kWh/dan"] = df["Potrošena struja (kWh)"] / df["Dana u mesecu"]
    df["Rad Komp %"] = (df["Rad kompresora (h)"] / df["Rad pumpe (h)"]) * 100
    df["Snaga (kW)"] = df["Proizvedena energija (kWh)"] / df["Rad kompresora (h)"]
    return df


# 2. UČITAVANJE PODATAKA
df_raw = load_data(gsheet_url_tekuca)
df_raw_prosla = load_data(gsheet_url_prosla)

# Ako je greška pri ucitavanju prosle sezone, obavijesti u sidebar-u
if df_raw_prosla is None:
    st.sidebar.warning("⚠️ Tabela za prošlu sezonu nije pronađena (provjerite link/prostorije u LINK_PROSLA_SEZONA).")

# Sidebar podešavanja
st.sidebar.header("📁 Izvor podataka")
uploaded_file = st.sidebar.file_uploader("Ili učitaj Excel ručno", type=["xlsx"])

st.sidebar.header("📍 Lokacija (za prognozu)")
lat = st.sidebar.number_input("Geografska širina", value=43.3)
lon = st.sidebar.number_input("Geografska dužina", value=21.9)

if uploaded_file:
    df_raw = pd.read_excel(uploaded_file, engine='openpyxl')

df = clean_dataframe(df_raw)
df_prosla = clean_dataframe(df_raw_prosla)

if df is not None:
    try:
        # Sigurne kalkulacije bez int(NaN) greške
        ukupna_proizvedena = np.nan_to_num(df["Proizvedena energija (kWh)"].sum())
        ukupna_struja = np.nan_to_num(df["Potrošena struja (kWh)"].sum())
        prosek_dan = np.nan_to_num(df["kWh/dan"].mean())

        st.success("✅ Podaci za tekuću sezonu uspešno učitani!")

        # TABOVI
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
            "📊 Pregled", "🌡 Kriva", "💡 EPS", "📅 Sezona",
            "🚀 OPTIMIZACIJA", "❄️ DEFROST", "💰 POREĐENJE",
            "📈 DNEVNA PROGNOZA", "🌦 Vremenska prognoza i preporučeni LWT",
            "🔄 POREĐENJE SEZONA"
        ])

        with tab1:
            st.subheader("📊 Mesečni i Sezonski izveštaj")
            sezonski_cop = ukupna_proizvedena / ukupna_struja if ukupna_struja > 0 else 0
            
            # Uzimanje poslednjeg popunjenog reda
            df_popunjeno = df.dropna(subset=["Potrošena struja (kWh)"])
            poslednji_red = df_popunjeno.iloc[-1] if not df_popunjeno.empty else df.iloc[-1]
            
            m0, m1, m2, m3 = st.columns(4)
            m0.metric("SEZONSKI COP (Sveukupno)", f"{sezonski_cop:.2f}")
            m1.metric("Opterećenje (Komp/Pumpa)", f"{poslednji_red.get('Rad Komp %', 0):.1f} %")
            m2.metric("Prosečna Snaga", f"{poslednji_red.get('Snaga (kW)', 0):.2f} kW")
            m3.metric("Trenutni Mesečni COP", f"{poslednji_red.get('COP', 0):.2f}")
            
            st.divider()
            st.write("### 📋 Pregled podataka po mesecima")
            st.dataframe(df.round(2), use_container_width=True)
            st.divider()
            
            c1, c2 = st.columns(2)
            with c1:
                fig1, ax1 = plt.subplots()
                ax1.bar(df["Mesec"], df["kWh/dan"].fillna(0), color="skyblue")
                ax1.set_title("Potrošnja (kWh/dan)")
                st.pyplot(fig1); plt.close(fig1)
            
            with c2:
                fig2, ax2 = plt.subplots()
                ax2.plot(df["Mesec"], df["COP"], marker="o", color="green", label="Mesečni COP")
                ax2.axhline(y=sezonski_cop, color='r', linestyle='--', label=f"Sezonski prosek ({sezonski_cop:.2f})")
                ax2.set_title("Efikasnost (COP)")
                ax2.legend(); ax2.grid(True)
                st.pyplot(fig2); plt.close(fig2)

        with tab2:
            st.subheader("🌡 Analiza krive grejanja")
            fig3, ax3 = plt.subplots()
            ax3.scatter(df["Spoljna T (°C)"], df["LWT (°C)"], color="red", s=100, label="Realne tačke")
            min_t = df["Spoljna T (°C)"].min() if not pd.isna(df["Spoljna T (°C)"].min()) else -5
            max_t = df["Spoljna T (°C)"].max() if not pd.isna(df["Spoljna T (°C)"].max()) else 15
            tx = np.linspace(min_t-2, max_t+2, 10)
            ty = 40 - 0.25 * tx
            ax3.plot(tx, ty, "--", color="gray", label="Referentna kriva")
            ax3.set_xlabel("Spoljna T"); ax3.set_ylabel("LWT"); ax3.legend()
            st.pyplot(fig3); plt.close(fig3)

        with tab3:
            st.subheader("💡 EPS Analiza i Granice")
            cena = st.number_input("Cena kWh (din)", value=10.5)
            racun_tp = ukupna_struja * cena
            
            df_popunjeno = df.dropna(subset=["Potrošena struja (kWh)"])
            poslednji_red = df_popunjeno.iloc[-1] if not df_popunjeno.empty else df.iloc[-1]
            potrosnja_trenutna = float(np.nan_to_num(poslednji_red.get("Potrošena struja (kWh)", 0)))
            
            danasnji_dan_br = date.today().day
            dnevni_prosek = potrosnja_trenutna / danasnji_dan_br if danasnji_dan_br > 0 else 0
            
            c1, c2 = st.columns(2)
            c1.metric("Ukupan račun (sezona)", f"{int(racun_tp)} RSD")
            granica = 1200
            
            if potrosnja_trenutna < granica:
                preostalo_kwh = granica - potrosnja_trenutna
                dana_do_granice = preostalo_kwh / dnevni_prosek if dnevni_prosek > 0 else 99
                datum_prelaska = date.today() + timedelta(days=int(dana_do_granice))
                
                if (dnevni_prosek * 30) > granica:
                    c2.metric("Projektovan prelazak praga", datum_prelaska.strftime("%d. %b"))
                    st.error(f"🚨 **ALARM:** Preći ćete granicu od {granica} kWh oko **{datum_prelaska.strftime('%d. %m. %Y.')}**")
                else:
                    c2.metric("Status praga", "Bezbedno")
                    st.success(f"✅ Sa potrošnjom od {int(dnevni_prosek * 30)} kWh/mesec, ostajete u plavoj zoni.")
            else:
                st.error(f"⚠️ Već ste prešli limit od {granica} kWh!")

            st.divider()
            st.bar_chart(df, x="Mesec", y="Potrošena struja (kWh)")

        with tab4:
            st.subheader("📅 Projekcija sezone")
            dani_sezone = st.number_input("Trajanje sezone (dana)", value=180)
            st.metric("Predviđena potrošnja (kWh)", f"{int(prosek_dan * dani_sezone)}")

        with tab5:
            st.subheader("🚀 Optimizacija rada (V5.x PRO)")
            smanjenje = st.slider("Smanjenje LWT (°C)", 0, 5, 1)
            faktor = smanjenje * 0.03
            nova_dnevna = prosek_dan * (1 - faktor)
            nova_sezona = nova_dnevna * dani_sezone
            usteda_kwh = prosek_dan * dani_sezone - nova_sezona

            st.metric("Nova procenjena potrošnja (kWh/sezona)", int(nova_sezona))
            st.metric("Ušteda energije (kWh)", int(usteda_kwh))
            st.metric("Ušteda u dinarima", int(usteda_kwh * cena))

        with tab6:
            st.subheader("❄️ Analiza otapanja (Defrost)")
            v_def = st.slider("Minuta po defrostu", 5, 15, 8)
            n_def = st.slider("Defrosta po satu rada", 0.5, 3.0, 1.0)
            rad_komp = np.nan_to_num(df["Rad kompresora (h)"].sum())
            gubitak = (v_def / 60) * n_def * 5 * rad_komp
            st.metric("Gubitak na defrost", f"{int(gubitak)} kWh")

        with tab7:
            st.subheader("💰 Poređenje troškova grejanja")
            c1, c2, c3 = st.columns(3)
            with c1:
                cena_drva = st.number_input("Cena drva (din/m3)", value=9000)
                t_drva = (ukupna_proizvedena / 1400) * cena_drva
                st.metric("Drva", f"{int(t_drva)} RSD", delta=f"{int(t_drva - racun_tp)} RSD")
            with c2:
                cena_peleta = st.number_input("Cena peleta (din/kg)", value=36)
                t_peleta = (ukupna_proizvedena / 4.8) * cena_peleta
                st.metric("Pelet", f"{int(t_peleta)} RSD", delta=f"{int(t_peleta - racun_tp)} RSD")
            with c3:
                cena_gasa = st.number_input("Cena gasa (din/m3)", value=55)
                t_gas = (ukupna_proizvedena / 9.5) * cena_gasa
                st.metric("Gas", f"{int(t_gas)} RSD", delta=f"{int(t_gas - racun_tp)} RSD")

        with tab8:
            st.subheader("📈 Prognoza potrošnje na 30 dana")
            meseci = df["Mesec"].astype(str).unique().tolist()
            izabrani_mesec = st.selectbox("Izaberi mesec", meseci, index=len(meseci)-1)
            red_iz_baze = df[df["Mesec"].astype(str) == izabrani_mesec].iloc[0]
            trenutna_potrosnja = float(np.nan_to_num(red_iz_baze.get("Potrošena struja (kWh)", 0)))
            
            prognoza_30_dana = (trenutna_potrosnja / danasnji_dan_br) * 30 if danasnji_dan_br > 0 else 0
            st.metric("PROGNOZA (30 DANA)", f"{int(prognoza_30_dana)} kWh")

        with tab9:
            st.subheader("🌦 Vremenska prognoza i preporučeni LWT")
            try:
                prog = get_weather_forecast(lat, lon)
                prog["Preporučeni LWT (°C)"] = 40 - 0.25 * prog["Spoljna T (°C)"]
                st.dataframe(prog.round(1), use_container_width=True)
            except Exception as e:
                st.error("Nije moguće učitati prognozu.")

        with tab10:
            st.subheader("🔄 Poređenje: Tekuća vs Prethodna Sezona")
            
            if df_prosla is not None:
                redosled_meseci = ["Oktobar", "Novembar", "Decembar", "Januar", "Februar", "Mart", "April", "Maj"]

                df_tekuca_clean = df.dropna(subset=["Potrošena struja (kWh)"]).copy()
                df_prosla_clean = df_prosla.dropna(subset=["Potrošena struja (kWh)"]).copy()

                struja_tekuca = np.nan_to_num(df_tekuca_clean["Potrošena struja (kWh)"].sum())
                struja_prosla = np.nan_to_num(df_prosla_clean["Potrošena struja (kWh)"].sum())
                
                proizvedeno_tekuca = np.nan_to_num(df_tekuca_clean["Proizvedena energija (kWh)"].sum())
                proizvedeno_prosla = np.nan_to_num(df_prosla_clean["Proizvedena energija (kWh)"].sum())
                
                cop_tekuca = proizvedeno_tekuca / struja_tekuca if struja_tekuca > 0 else 0
                cop_prosla = proizvedeno_prosla / struja_prosla if struja_prosla > 0 else 0
                
                rad_tekuca = np.nan_to_num(df_tekuca_clean["Rad kompresora (h)"].sum())
                rad_prosla = np.nan_to_num(df_prosla_clean["Rad kompresora (h)"].sum())
                
                c1, c2, c3 = st.columns(3)
                c1.metric(
                    "Ukupna Potrošnja Struje", 
                    f"{int(struja_tekuca)} kWh", 
                    delta=f"{int(struja_tekuca - struja_prosla)} kWh u odnosu na prošlu",
                    delta_color="inverse"
                )
                c2.metric(
                    "Sezonski COP", 
                    f"{cop_tekuca:.2f}", 
                    delta=f"{cop_tekuca - cop_prosla:.2f} u odnosu na prošlu"
                )
                c3.metric(
                    "Rad Kompresora", 
                    f"{int(rad_tekuca)} h", 
                    delta=f"{int(rad_tekuca - rad_prosla)} h u odnosu na prošlu",
                    delta_color="inverse"
                )
                
                st.divider()
                st.write("### 📊 Mesečno poređenje potrošnje (kWh)")
                
                merged_df = pd.merge(
                    df_tekuca_clean[["Mesec", "Potrošena struja (kWh)", "COP"]], 
                    df_prosla_clean[["Mesec", "Potrošena struja (kWh)", "COP"]], 
                    on="Mesec", 
                    how="outer", 
                    suffixes=(" (Tekuća)", " (Prošla)")
                )

                merged_df['Mesec_Cat'] = pd.Categorical(merged_df['Mesec'], categories=redosled_meseci, ordered=True)
                merged_df = merged_df.sort_values('Mesec_Cat').drop(columns=['Mesec_Cat'])
                
                merged_df_display = merged_df.dropna(how='all', subset=["Potrošena struja (kWh) (Tekuća)", "Potrošena struja (kWh) (Prošla)"])
                
                st.dataframe(merged_df_display.fillna("-").round(2), use_container_width=True)
                
                fig_comp, ax_comp = plt.subplots(figsize=(10, 4))
                x = np.arange(len(merged_df_display["Mesec"]))
                width = 0.35
                
                y_tekuca = merged_df_display["Potrošena struja (kWh) (Tekuća)"].fillna(0)
                y_prosla = merged_df_display["Potrošena struja (kWh) (Prošla)"].fillna(0)
                
                ax_comp.bar(x - width/2, y_tekuca, width, label="Tekuća Sezona", color="skyblue")
                ax_comp.bar(x + width/2, y_prosla, width, label="Prethodna Sezona", color="orange")
                
                ax_comp.set_xticks(x)
                ax_comp.set_xticklabels(merged_df_display["Mesec"], rotation=0)
                ax_comp.set_ylabel("kWh")
                ax_comp.set_title("Poređenje potrošnje struje po mesecima")
                ax_comp.legend()
                ax_comp.grid(True, linestyle="--", alpha=0.5)
                
                st.pyplot(fig_comp)
                plt.close(fig_comp)
            else:
                st.warning("⚠️ Podaci za prošlu sezonu nisu učitani. Proverite link u `LINK_PROSLA_SEZONA` (mora biti dostupan javno preko opcije Share).")

    except Exception as e:
        st.error(f"⚠️ Došlo je do greške u obradi podataka: {e}")
        st.write("Sistem u tabeli vidi ove kolone:", list(df_raw.columns))
else:
    st.warning("Čekam podatke... Proverite da li je glavni Google Sheets link ispravno postavljen.")
