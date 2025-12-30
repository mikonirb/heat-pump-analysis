import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Toplotna pumpa – EPS analiza", layout="wide")
st.title("💡 EPS analiza troška – V4.0")
st.caption("Obračun po zonama • realan mesečni trošak")

# ================== PODACI ==================
data = {
    "Mesec": ["Novembar", "Decembar"],
    "Potrošena struja (kWh)": [500, 1041],
}

df = pd.DataFrame(data)

st.subheader("📥 Mesečna potrošnja")
df = st.data_editor(df, num_rows="dynamic")

# ================== EPS PARAMETRI ==================
st.subheader("⚙️ EPS parametri")

col1, col2, col3 = st.columns(3)

with col1:
    green_limit = st.number_input("Zelena zona limit (kWh)", 0, 5000, 350)
    green_price = st.number_input("Cena zelene (din/kWh)", 0.0, 50.0, 6.0)

with col2:
    blue_limit = st.number_input("Plava zona limit (kWh)", 0, 5000, 1600)
    blue_price = st.number_input("Cena plave (din/kWh)", 0.0, 50.0, 9.0)

with col3:
    red_price = st.number_input("Cena crvene (din/kWh)", 0.0, 100.0, 18.0)

# ================== OBRAČUN ==================
def eps_cost(kwh):
    green = min(kwh, green_limit)
    blue = min(max(kwh - green_limit, 0), blue_limit - green_limit)
    red = max(kwh - blue_limit, 0)

    cost = (
        green * green_price +
        blue * blue_price +
        red * red_price
    )

    return green, blue, red, cost

results = df["Potrošena struja (kWh)"].apply(eps_cost)
df["Zelena (kWh)"] = results.apply(lambda x: x[0])
df["Plava (kWh)"] = results.apply(lambda x: x[1])
df["Crvena (kWh)"] = results.apply(lambda x: x[2])
df["Račun (din)"] = results.apply(lambda x: x[3])

st.subheader("📊 EPS obračun")
st.dataframe(df.round(0), use_container_width=True)

# ================== STATUS ==================
st.subheader("🚦 Status zone")

for _, row in df.iterrows():
    if row["Crvena (kWh)"] > 0:
        st.error(f"{row['Mesec']}: 🔴 U crvenoj zoni")
    elif row["Plava (kWh)"] > 0:
        st.warning(f"{row['Mesec']}: 🔵 U plavoj zoni")
    else:
        st.success(f"{row['Mesec']}: 🟢 Zelena zona")

# ================== GRAFIK ==================
st.subheader("📈 Raspodela po zonama")

fig, ax = plt.subplots()
ax.bar(df["Mesec"], df["Zelena (kWh)"], label="Zelena")
ax.bar(df["Mesec"], df["Plava (kWh)"], bottom=df["Zelena (kWh)"], label="Plava")
ax.bar(
    df["Mesec"],
    df["Crvena (kWh)"],
    bottom=df["Zelena (kWh)"] + df["Plava (kWh)"],
    label="Crvena"
)
ax.set_ylabel("kWh")
ax.legend()
st.pyplot(fig)

st.success("✅ V4.0 aktivna – vidiš realan EPS trošak po mesecima.")
