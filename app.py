import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Toplotna pumpa – V5.0", layout="wide")

st.title("Analiza rada toplotne pumpe – V5.0 (Konzervativna)")

# =========================
# JEDINSTVEN UNOS PODATAKA
# =========================
st.sidebar.header("📥 Unos mesečnih podataka")

data = st.sidebar.data_editor(
    pd.DataFrame({
        "Mesec": ["Novembar", "Decembar"],
        "Spoljna T (°C)": [8, 2],
        "Proizvedena energija (kWh)": [3065, 4188],
        "Potrošnja (kWh)": [500, 1041],
        "COP": [6.18, 3.81],
        "LWT (°C)": [32.4, 36.5],
        "Startovi": [1179, 402],
        "Dani": [30, 28]
    }),
    num_rows="dynamic"
)

data["kWh/dan"] = data["Potrošnja (kWh)"] / data["Dani"]
data["Startovi/dan"] = data["Startovi"] / data["Dani"]

# =========================
# TABOVI
# =========================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Pregled sistema",
    "🌡 Spoljna T & COP",
    "💡 EPS trošak",
    "📅 Sezona",
    "⚙️ Optimizacija (V5.0)"
])

# -------------------------
# TAB 1 – Pregled sistema
# -------------------------
with tab1:
    st.subheader("Osnovni pokazatelji")
    st.dataframe(data)

    fig, ax = plt.subplots()
    ax.bar(data["Mesec"], data["kWh/dan"])
    ax.set_ylabel("kWh/dan")
    st.pyplot(fig)

# -------------------------
# TAB 2 – Spoljna T & COP
# -------------------------
with tab2:
    fig, ax1 = plt.subplots()
    ax1.plot(data["Spoljna T (°C)"], data["COP"], marker="o")
    ax1.set_xlabel("Spoljna temperatura (°C)")
    ax1.set_ylabel("COP")
    st.pyplot(fig)

# -------------------------
# TAB 3 – EPS trošak
# -------------------------
with tab3:
    cena = 13.5  # RSD/kWh aproksimacija
    data["Trošak (RSD)"] = data["Potrošnja (kWh)"] * cena

    st.metric("Ukupan trošak (RSD)", int(data["Trošak (RSD)"].sum()))
    st.dataframe(data[["Mesec", "Potrošnja (kWh)", "Trošak (RSD)"]])

# -------------------------
# TAB 4 – Sezona
# -------------------------
with tab4:
    sezona = data["Potrošnja (kWh)"].sum()
    st.metric("Potrošnja do sada (kWh)", int(sezona))

    projekcija = sezona / data["Dani"].sum() * 180
    st.metric("Projekcija cele sezone (kWh)", int(projekcija))

# =====================================================
# TAB 5 – OPTIMIZACIJA (V5.0)
# =====================================================
with tab5:
    st.subheader("1️⃣ Idealna kriva grejanja (konzervativna)")

    # idealna kriva za radijatore (sigurna)
    x = np.linspace(-10, 15, 50)
    ideal_lwt = 38 - 0.2 * x  # konzervativna

    fig, ax = plt.subplots()
    ax.plot(data["Spoljna T (°C)"], data["LWT (°C)"], "o-", label="Tvoja kriva")
    ax.plot(x, ideal_lwt, "--", label="Idealna kriva")
    ax.set_xlabel("Spoljna T (°C)")
    ax.set_ylabel("LWT (°C)")
    ax.legend()
    st.pyplot(fig)

    st.subheader("2️⃣ LWT simulator uštede")

    delta = st.slider("Smanjenje LWT (°C)", 0, 3, 1)
    usteda_pct = delta * 0.03  # 3% po °C (konzervativno)
    usteda_kwh = sezona * usteda_pct

    st.metric("Potencijalna ušteda (kWh/sezona)", int(usteda_kwh))
    st.metric("Ušteda (RSD)", int(usteda_kwh * cena))

    st.subheader("3️⃣ EPS pametni alarm")

    dnevno = data["kWh/dan"].mean()
    mesecna_proj = dnevno * 30

    if mesecna_proj > 1200:
        st.error("⚠️ Ulazak u CRVENU zonu!")
    elif mesecna_proj > 1000:
        st.warning("🟡 Blizu PLAVE zone")
    else:
        st.success("🟢 Bezbedno u ZELENOJ zoni")

    st.subheader("4️⃣ Comfort Index")

    startovi = data["Startovi/dan"].mean()
    comfort = max(60, 100 - startovi * 0.8)

    st.metric("Comfort Index", f"{int(comfort)} / 100")

    if comfort > 85:
        st.success("Komfor stabilan – postoji prostor za optimizaciju.")
    else:
        st.warning("Smanjenje LWT nije preporučeno.")

