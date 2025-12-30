import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Toplotna pumpa – analiza V2.0", layout="wide")
st.title("🔥 Analiza rada toplotne pumpe – V2.0")
st.caption("Daikin EBLQ016 • radijatori • 24/7 grejanje")

# Default podaci
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

st.subheader("📊 Rezultati")
st.dataframe(df.round(2), use_container_width=True)

# ---- SEZONSKA PROJEKCIJA ----
st.subheader("📅 Projekcija cele grejne sezone")

sezona_dana = 150
prosek_dnevno = df["kWh/dan"].mean()
projekcija = prosek_dnevno * sezona_dana
do_sada = df["Potrošena struja (kWh)"].sum()

col1, col2, col3 = st.columns(3)
col1.metric("🔌 Potrošnja do sada (kWh)", round(do_sada, 0))
col2.metric("📈 Prosek kWh/dan", round(prosek_dnevno, 1))
col3.metric("📊 Projekcija sezone (kWh)", round(projekcija, 0))

# ---- HEALTH SCORE ----
st.subheader("❤️ Health score pumpe")

avg_cop = df["COP"].mean()
avg_start = df["Startova/dan"].mean()
avg_lwt = df["LWT (°C)"].mean()

score = 100
if avg_cop < 3.5:
    score -= 20
if avg_start > 10:
    score -= 25
if avg_lwt > 40:
    score -= 15

score = max(score, 0)

if score >= 85:
    stanje = "🟢 ZDRAVA"
elif score >= 70:
    stanje = "🟡 DOBRA"
elif score >= 50:
    stanje = "🟠 OPTEREĆENA"
else:
    stanje = "🔴 RIZIČNA"

st.metric("Health score", f"{score}/100", stanje)

# ---- ALARMI ----
st.subheader("🚨 Status ciklusa")

if avg_start <= 8:
    st.success("✅ Broj startova je u idealnom opsegu.")
elif avg_start <= 12:
    st.warning("⚠️ Startovi su povišeni – razmotri finije podešavanje krive.")
else:
    st.error("❌ Previše startova – bafer ili veći protok bi pomogli.")

# ---- PREPORUKE ----
st.subheader("🔧 Preporuke sistema")

if avg_lwt > 38:
    st.info("• Pokušaj blago snižavanje LWT krive (−1 °C po tački).")

if avg_start > 10:
    st.info("• Razmotri bafer 50–100 L za smanjenje ciklusa.")

if avg_cop > 4:
    st.success("• Sistem radi vrlo efikasno za radijatorsko grejanje.")

# ---- GRAFICI ----
st.subheader("📈 Grafici")

colA, colB = st.columns(2)

with colA:
    fig1, ax1 = plt.subplots()
    ax1.bar(df["Mesec"], df["kWh/dan"])
    ax1.set_title("kWh/dan")
    st.pyplot(fig1)

with colB:
    fig2, ax2 = plt.subplots()
    ax2.plot(df["Mesec"], df["COP"], marker="o")
    ax2.set_title("COP po mesecima")
    st.pyplot(fig2)

st.success("✅ V2.0 aktivna – ovo je već ozbiljan monitoring alat.")

