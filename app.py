import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Konfiguracija stranice
st.set_page_config(page_title="Toplotna pumpa – ALL IN ONE", layout="wide")
st.title("🔥 Toplotna pumpa – kompletna analiza (V4.1)")

# ================== JEDINSTVEN UNOS PODATAKA ==================
# Inicijalizacija podataka u session_state ako ne postoje
if 'df_data' not in st.session_state:
    st.session_state.df_data = pd.DataFrame({
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

st.subheader("📥 Mesečni podaci")
# Koristimo data_editor za direktnu izmenu
df = st.data_editor(st.session_state.df_data, num_rows="dynamic", key="main_editor")

# Ažuriramo session_state sa novim podacima iz editora
st.session_state.df_data = df

# ================== IZRAČUNAVANJA ==================
# Kalkulacije kolona
df["COP"] = df["Proizvedena energija (kWh)"] / df["Potrošena struja (kWh)"]
df["kWh/dan"] = df["Potrošena struja (kWh)"] / df["Dana u mesecu"]
df["Startova/dan"] = df["Startovi kompresora"] / df["Dana u mesecu"]

# Globalne varijable za ostale tabove
prosek_kwh_dan = df["kWh/dan"].mean() if not df.empty else 0

# ================== TABOVI ==================
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Pregled sistema", "🌡 Spoljna T & kriva", "💡 EPS zone", "📅 Sezona", "🚀 OPTIMIZACIJA"]
)

# --- TAB 1 ---
with tab1:
    st.subheader("📊 Osnovni pokazatelji")
    st.dataframe(df.round(2), use_container_width=True)
    
    colA, colB = st.columns(2)
    with colA:
        fig1, ax1 = plt.subplots()
        ax1.bar(df["Mesec"], df["kWh/dan"], color="skyblue")
        ax1.set_title("Dnevna potrošnja (kWh/dan)")
        st.pyplot(fig1)
        plt.close(fig1)
    with colB:
        fig2, ax2 = plt.subplots()
        ax2.plot(df["Mesec"], df["COP"], marker="o", color="green")
        ax2.set_title("Efikasnost (COP)")
        ax2.grid(True, linestyle="--", alpha=0.6)
        st.pyplot(fig2)
        plt.close(fig2)

# --- TAB 2 ---
with tab2:
    st.subheader("🌡 Analiza krive grejanja")
    if len(df) > 0:
        fig3, ax3 = plt.subplots()
        ax3.scatter(df["Spoljna T (°C)"], df["LWT (°C)"], color="red", label="Realni podaci (LWT)")
        # Referentna linija
        tx = np.linspace(df["Spoljna T (°C)"].min()-2, df["Spoljna T (°C)"].max()+2, 10)
        ty = 38 - 0.4 * tx
        ax3.plot(tx, ty, "--", color="gray", label="Teoretska kriva")
        ax3.set_xlabel("Spoljna Temperatura (°C)")
        ax3.set_ylabel("LWT (°C)")
        ax3.legend()
        st.pyplot(fig3)
        plt.close(fig3)

# --- TAB 3 ---
with tab3:
    st.subheader("💡 EPS obračun")
    c1, c2, c3 = st.columns(3)
    g_price = c1.number_input("Zelena (din)", value=6.0, key="g_p")
    b_price = c2.number_input("Plava (din)", value=9.5, key="b_p")
    r_price = c3.number_input("Crvena (din)", value=19.0, key="r_p")
    
    st.bar_chart(df, x="Mesec", y="Potrošena struja (kWh)")

# --- TAB 4 ---
with tab4:
    st.subheader("📅 Sezonska projekcija")
    sezona_dana = st.number_input("Trajanje grejne sezone (dana)", value=180, key="s_d")
    projekcija = prosek_kwh_dan * sezona_dana
    st.metric("Predviđena potrošnja za celu sezonu", f"{int(projekcija)} kWh")

# --- TAB 5 (OPTIMIZACIJA) ---
with tab5:
    st.subheader("1️⃣ Idealna kriva vs Tvoji podaci")
    
    x_osa = np.linspace(-10, 20, 100)
    y_idealna = 35 - 0.5 * x_osa 

    fig4, ax4 = plt.subplots(figsize=(10, 5))
    ax4.scatter(df["Spoljna T (°C)"], df["LWT (°C)"], color="red", s=100, label="Tvoj trenutni rad", zorder=5)
    ax4.plot(x_osa, y_idealna, label="Preporučena kriva (Optimum)", color="green", linestyle="--")
    ax4.set_xlabel("Spoljna Temperatura (°C)")
    ax4.set_ylabel("LWT (°C)")
    ax4.legend()
    st.pyplot(fig4)
    plt.close(fig4)

    st.divider()

    col_sim1, col_sim2 = st.columns([1, 2])
    with col_sim1:
        st.subheader("2️⃣ LWT Simulator")
        smanjenje = st.slider("Smanji LWT za (°C)", 0, 5, 1, key="slider_lwt")
        usteda_posto = smanjenje * 0.03
        usteda_kwh = projekcija * usteda_posto
        st.metric("Potencijalna godišnja ušteda", f"{int(usteda_kwh)} kWh")

    with col_sim2:
        st.subheader("3️⃣ Comfort & Efikasnost")
        avg_starts = df["Startova/dan"].mean()
        comfort_score = int(max(0, 100 - (avg_starts * 3)))
        st.write(f"**Comfort Index:** {comfort_score}/100")
        st.progress(comfort_score / 100)
        
        if comfort_score < 60:
            st.warning("⚠️ Previše startova! Razmislite o podešavanjima.")
        else:
            st.success("✅ Rad kompresora je stabilan.")

    st.subheader("4️⃣ EPS Pametni alarm")
    mesecna_proj = prosek_kwh_dan * 30
    if mesecna_proj > 1600:
        st.error(f"ALARM: Projekcija {int(mesecna_proj)} kWh - CRVENA zona!")
    elif mesecna_proj > 350:
        st.warning(f"PAŽNJA: Projekcija {int(mesecna_proj)} kWh - PLAVA zona.")
    else:
        st.success(f"ZELENA zona: Projekcija {int(mesecna_proj)} kWh.")

st.success("✅ Aplikacija je osvežena.")
