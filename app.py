import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np  # DODATO: Neophodno za računanje krive

st.set_page_config(page_title="Toplotna pumpa – ALL IN ONE", layout="wide")
st.title("🔥 Toplotna pumpa – kompletna analiza (V4.1)")
st.caption("Jedan unos • Više tabova • EPS • Spoljna temperatura • Projekcija")

# ================== JEDINSTVEN UNOS PODATAKA ==================
data = {
    "Mesec": ["Novembar", "Decembar"],
    "Proizvedena energija (kWh)": [3065, 4432],
    "Potrošena struja (kWh)": [500, 1201],
    "Rad kompresora (h)": [514, 628],
    "Rad pumpe (h)": [683, 678],
    "Startovi kompresora": [1179, 418],
    "LWT (°C)": [32.4, 36.5],
    "Spoljna T (°C)": [8.0, 2.0],
    "Dana u mesecu": [30, 29],
}

df = pd.DataFrame(data)

st.subheader("📥 Mesečni podaci (zajednički za sve tabove)")
df = st.data_editor(df, num_rows="dynamic")

# ================== IZRAČUNAVANJA ==================
df["COP"] = df["Proizvedena energija (kWh)"] / df["Potrošena struja (kWh)"]
df["kWh/dan"] = df["Potrošena struja (kWh)"] / df["Dana u mesecu"]
df["Startova/dan"] = df["Startovi kompresora"] / df["Dana u mesecu"]

# ================== TABOVI ==================
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Pregled sistema", "🌡 Spoljna T & kriva", "💡 EPS zone", "📅 Sezona", "OPTIMIZACIJA"]
)

# ... (KOD ZA TAB 1, 2, 3 OSTAJE ISTI KAO TVOJ) ...

with tab1:
    st.subheader("📊 Osnovni pokazatelji")
    st.dataframe(df.round(2), use_container_width=True)
    avg_cop = df["COP"].mean()
    avg_start = df["Startova/dan"].mean()
    avg_lwt = df["LWT (°C)"].mean()
    # ... ostatak koda za tab1

with tab2:
    st.subheader("🌡 Analiza u odnosu na spoljnu temperaturu")
    # ... ostatak koda za tab2

with tab3:
    st.subheader("💡 EPS obračun po zonama")
    # Definisanje cena radi kasnijeg korišćenja u Tabu 5
    col1, col2, col3 = st.columns(3)
    with col1:
        green_limit = st.number_input("Zelena limit (kWh)", 0, 5000, 350)
        green_price = st.number_input("Cena zelene (din/kWh)", 0.0, 50.0, 6.0)
    with col2:
        blue_limit = st.number_input("Plava limit (kWh)", 0, 5000, 1600)
        blue_price = st.number_input("Cena plave (din/kWh)", 0.0, 50.0, 9.0)
    with col3:
        red_price = st.number_input("Cena crvene (din/kWh)", 0.0, 100.0, 18.0)
    
    def eps_cost(kwh):
        green = min(kwh, green_limit)
        blue = min(max(kwh - green_limit, 0), blue_limit - green_limit)
        red = max(kwh - blue_limit, 0)
        cost = green * green_price + blue * blue_price + red * red_price
        return green, blue, red, cost

    results = df["Potrošena struja (kWh)"].apply(eps_cost)
    df_eps = df.copy()
    df_eps["Zelena (kWh)"] = results.apply(lambda x: x[0])
    df_eps["Plava (kWh)"] = results.apply(lambda x: x[1])
    df_eps["Crvena (kWh)"] = results.apply(lambda x: x[2])
    df_eps["Račun (din)"] = results.apply(lambda x: x[3])
    st.dataframe(df_eps.round(0), use_container_width=True)

with tab4:
    st.subheader("📅 Sezonski pregled")
    sezona_dana = st.number_input("Trajanje sezone (dana)", 90, 200, 150)
    # ... ostatak koda za tab4
    do_sada = df["Potrošena struja (kWh)"].sum()
    prosek_kwh_dan = df["kWh/dan"].mean()
    projekcija_sezona = prosek_kwh_dan * sezona_dana

# =====================================================
# TAB 5 – OPTIMIZACIJA (KORIGOVANO)
# =====================================================
with tab5:
    st.subheader("1️⃣ Idealna kriva grejanja (konzervativna)")

    # Generisanje idealne krive pomoću numpy-a
    x_range = np.linspace(-10, 15, 50)
    ideal_y = 38 - 0.4 * x_range  # Primer nagiba krive

    fig, ax = plt.subplots()
    # Koristimo DF podatke za tvoju krivu
    ax.plot(df["Spoljna T (°C)"], df["LWT (°C)"], "ro", label="Tvoji podaci")
    ax.plot(x_range, ideal_y, "--", color="gray", label="Preporučena kriva")
    ax.set_xlabel("Spoljna T (°C)")
    ax.set_ylabel("LWT (°C)")
    ax.legend()
    st.pyplot(fig)

    st.subheader("2️⃣ LWT simulator uštede")

    delta = st.slider("Smanjenje LWT (°C)", 0, 5, 1)
    usteda_pct = delta * 0.03  # 3% uštede po stepenu nižem LWT
    # Koristimo projekciju iz Tab-a 4
    potencijalna_usteda_kwh = projekcija_sezona * usteda_pct
    
    # Uzimamo prosečnu cenu iz Tab-a 3 (plava zona kao reper)
    cena_reper = blue_price if 'blue_price' in locals() else 9.0

    c1, c2 = st.columns(2)
    c1.metric("Potencijalna ušteda (kWh/sezona)", int(potencijalna_usteda_kwh))
    c2.metric("Procena uštede (RSD)", f"{int(potencijalna_usteda_kwh * cena_reper)} din")

    st.subheader("3️⃣ EPS pametni alarm")

    mesecna_proj = prosek_kwh_dan * 30

    if mesecna_proj > 1600:
        st.error(f"⚠️ Projekcija: {int(mesecna_proj)} kWh - Ulazak u CRVENU zonu!")
    elif mesecna_proj > 350:
        st.warning(f"🟡 Projekcija: {int(mesecna_proj)} kWh - Nalazite se u PLAVOJ zoni.")
    else:
        st.success(f"🟢 Projekcija: {int(mesecna_proj)} kWh - Bezbedno u ZELENOJ zoni.")

    st.subheader("4️⃣ Comfort Index")

    avg_starts_dan = df["Startova/dan"].mean()
    comfort = max(0, min(100, 100 - (avg_starts_dan * 2))) # Kazna 2 poena po startu

    st.metric("Comfort Index (Stabilnost rada)", f"{int(comfort)} / 100")

    if comfort > 80:
        st.success("Sistem radi stabilno sa malo startova. Odlično!")
    elif comfort > 50:
        st.info("Sistem ima učestale startove. Razmislite o povećanju histereze.")
    else:
        st.warning("Prevelik broj startova! Proverite protok ili snagu pumpe.")

st.sidebar.info("Savet: Smanjenjem LWT za samo 1°C povećavate COP za oko 3%.")
