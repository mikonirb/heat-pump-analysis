import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Toplotna pumpa – analiza V3.0", layout="wide")
st.title("🔥 Analiza rada toplotne pumpe – V3.0")
st.caption("Spoljna temperatura • COP • Dijagnoza krive")

# Default podaci (primer)
data = {
    "Mesec": ["Novembar", "Decembar"],
    "Proizvedena energija (kWh)": [3065, 4188],
    "Potrošena struja (kWh)": [500, 1041],
    "Rad kompresora (h)": [514, 606],
    "Startovi kompresora": [1179, 402],
    "LWT (°C)": [32.4, 36.5],
    "Spoljna T (°C)": [8.0, 2.0],
    "Dana u mesecu": [30, 31],
}

df = pd.DataFrame(data)

st.subheader("📥 Mesečni podaci")
df = st.data_editor(df, num_rows="dynamic")

# Izračunavanja
df["COP"] = df["Proizvedena energija (kWh)"] / df["Potrošena struja (kWh)"]
df["kWh/dan"] = df["Potrošena struja (kWh)"] / df["Dana u mesecu"]
df["Startova/dan"] = df["Startovi kompresora"] / df["Dana u mesecu"]

st.subheader("📊 Rezultati")
st.dataframe(df.round(2), use_container_width=True)

# ---- ANALIZA U ODNOSU NA SPOLJNU TEMPERATURU ----
st.subheader("🌡 Analiza u odnosu na spoljnu temperaturu")

avg_cop = df["COP"].mean()
avg_lwt = df["LWT (°C)"].mean()
avg_out = df["Spoljna T (°C)"].mean()

# Jednostavan benchmark
ideal_lwt = 30 + (15 - avg_out) * 0.4

if avg_lwt <= ideal_lwt + 1:
    stanje_krive = "🟢 Kriva grejanja je dobro pogođena."
elif avg_lwt <= ideal_lwt + 3:
    stanje_krive = "🟡 Kriva je blago previsoka – ima prostora za optimizaciju."
else:
    stanje_krive = "🔴 Kriva je previsoka – sistem radi nepotrebno teško."

st.info(f"Procena krive: **{stanje_krive}**")
st.write(f"Idealni LWT za prosečnu spoljnu T ≈ **{ideal_lwt:.1f} °C**")

# ---- GRAFICI ----
st.subheader("📈 Grafici u odnosu na spoljnu temperaturu")

col1, col2 = st.columns(2)

with col1:
    fig1, ax1 = plt.subplots()
    ax1.scatter(df["Spoljna T (°C)"], df["COP"])
    ax1.set_xlabel("Spoljna T (°C)")
    ax1.set_ylabel("COP")
    ax1.set_title("COP vs spoljna temperatura")
    st.pyplot(fig1)

with col2:
    fig2, ax2 = plt.subplots()
    ax2.scatter(df["Spoljna T (°C)"], df["kWh/dan"])
    ax2.set_xlabel("Spoljna T (°C)")
    ax2.set_ylabel("kWh/dan")
    ax2.set_title("Potrošnja vs spoljna temperatura")
    st.pyplot(fig2)

# ---- PREPORUKE ----
st.subheader("🔧 Pametne preporuke")

if avg_lwt > ideal_lwt + 2:
    st.warning("• Probaj snižavanje cele krive grejanja za −1 °C.")
if avg_cop < 3.5:
    st.warning("• COP je nizak za ovu spoljnu temperaturu – proveri protok / cikluse.")
if avg_cop > 4:
    st.success("• Odličan rad sistema za radijatorsko grejanje.")

st.success("✅ V3.0 aktivna – sada imaš pravu osnovu za optimizaciju.")
