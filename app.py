import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Toplotna pumpa – analiza sezone", layout="wide")

st.title("🔥 Analiza rada toplotne pumpe – Daikin EBLQ016")

st.markdown("Unesi mesečne podatke. Sve ostalo se računa automatski.")

# Default podaci (tvoji)
data = {
    "Mesec": ["Novembar", "Decembar"],
    "Proizvedena energija (kWh)": [3065, 4188],
    "Potrošena struja (kWh)": [500, 1041],
    "Rad kompresora (h)": [514, 606],
    "Startovi kompresora": [1179, 402],
    "LWT (°C)": [32.38, 36.5],
    "Dana u mesecu": [30, 31],
}

df = pd.DataFrame(data)

st.subheader("📥 Mesečni podaci")
df = st.data_editor(df, num_rows="dynamic")

# Izračunavanja
df["COP"] = df["Proizvedena energija (kWh)"] / df["Potrošena struja (kWh)"]
df["kWh/dan"] = df["Potrošena struja (kWh)"] / df["Dana u mesecu"]
df["Startova/dan"] = df["Startovi kompresora"] / df["Dana u mesecu"]

st.subheader("📊 Izračunati rezultati")
st.dataframe(df.round(2), use_container_width=True)

# Sezonski zbir
total_kwh = df["Potrošena struja (kWh)"].sum()
st.metric("🔌 Ukupna potrošnja do sada (kWh)", round(total_kwh, 0))

# Grafici
st.subheader("📈 Grafici")

col1, col2 = st.columns(2)

with col1:
    fig1, ax1 = plt.subplots()
    ax1.bar(df["Mesec"], df["kWh/dan"])
    ax1.set_ylabel("kWh/dan")
    ax1.set_title("Dnevna potrošnja")
    st.pyplot(fig1)

with col2:
    fig2, ax2 = plt.subplots()
    ax2.plot(df["Mesec"], df["COP"], marker="o")
    ax2.set_ylabel("COP")
    ax2.set_title("COP po mesecima")
    st.pyplot(fig2)

col3, col4 = st.columns(2)

with col3:
    fig3, ax3 = plt.subplots()
    ax3.plot(df["Mesec"], df["LWT (°C)"], marker="s")
    ax3.set_ylabel("°C")
    ax3.set_title("LWT po mesecima")
    st.pyplot(fig3)

with col4:
    fig4, ax4 = plt.subplots()
    ax4.bar(df["Mesec"], df["Startova/dan"])
    ax4.set_ylabel("Startova/dan")
    ax4.set_title("Ciklusi kompresora")
    st.pyplot(fig4)

st.success("✅ Spremno – možeš dodavati nove mesece i pratiti celu sezonu.")
