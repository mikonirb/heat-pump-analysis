import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Konfiguracija stranice
st.set_page_config(page_title="Toplotna pumpa – PRO ANALIZA", layout="wide")
st.title("🔥 Toplotna pumpa – kompletna analiza (V5.0)")

# ================== JEDINSTVEN UNOS PODATAKA ==================
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
df = st.data_editor(st.session_state.df_data, num_rows="dynamic", key="main_editor_v5")
st.session_state.df_data = df

# ================== IZRAČUNAVANJA ==================
df["COP"] = df["Proizvedena energija (kWh)"] / df["Potrošena struja (kWh)"]
df["kWh/dan"] = df["Potrošena struja (kWh)"] / df["Dana u mesecu"]
df["Startova/dan"] = df["Startovi kompresora"] / df["Dana u mesecu"]

prosek_kwh_dan = df["kWh/dan"].mean() if not df.empty else 0
ukupna_proizvedena = df["Proizvedena energija (kWh)"].sum()
ukupna_potrosnja_struje = df["Potrošena struja (kWh)"].sum()

# ================== TABOVI ==================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Pregled", "🌡 Kriva", "💡 EPS", "📅 Sezona", "🚀 OPTIMIZACIJA", "❄️ DEFROST", "💰 UŠTEDA VS DRUGI"
])

# --- TABovi 1-4 (Zadržana stara logika) ---
with tab1:
    st.subheader("📊 Osnovni pokazatelji")
    st.dataframe(df.round(2), use_container_width=True)
    colA, colB = st.columns(2)
    with colA:
        fig1, ax1 = plt.subplots(); ax1.bar(df["Mesec"], df["kWh/dan"], color="skyblue")
        ax1.set_title("Dnevna potrošnja (kWh/dan)"); st.pyplot(fig1); plt.close(fig1)
    with colB:
        fig2, ax2 = plt.subplots(); ax2.plot(df["Mesec"], df["COP"], marker="o", color="green")
        ax2.set_title("Efikasnost (COP)"); ax2.grid(True); st.pyplot(fig2); plt.close(fig2)

with tab2:
    st.subheader("🌡 Analiza krive grejanja")
    if len(df) > 0:
        fig3, ax3 = plt.subplots()
        ax3.scatter(df["Spoljna T (°C)"], df["LWT (°C)"], color="red", label="Realni podaci")
        tx = np.linspace(df["Spoljna T (°C)"].min()-2, df["Spoljna T (°C)"].max()+2, 10)
        ty = 38 - 0.4 * tx
        ax3.plot(tx, ty, "--", color="gray", label="Teoretska kriva")
        ax3.legend(); st.pyplot(fig3); plt.close(fig3)

with tab3:
    st.subheader("💡 EPS obračun (Plava zona prosek)")
    b_price = st.number_input("Cena kWh sa prenosom (din)", value=10.5)
    st.bar_chart(df, x="Mesec", y="Potrošena struja (kWh)")
    trenutni_racun = ukupna_potrosnja_struje * b_price

with tab4:
    st.subheader("📅 Sezonska projekcija")
    sezona_dana = st.number_input("Trajanje grejne sezone (dana)", value=180)
    projekcija_kwh = prosek_kwh_dan * sezona_dana
    st.metric("Predviđena potrošnja sezone", f"{int(projekcija_kwh)} kWh")

# --- TAB 5 (Optimizacija) ---
with tab5:
    st.subheader("🚀 Simulator optimizacije")
    x_osa = np.linspace(-10, 20, 50); y_idealna = 35 - 0.5 * x_osa 
    fig4, ax4 = plt.subplots(figsize=(10, 4))
    ax4.scatter(df["Spoljna T (°C)"], df["LWT (°C)"], color="red", s=100, label="Trenutni rad")
    ax4.plot(x_osa, y_idealna, label="Optimum", color="green", linestyle="--")
    st.pyplot(fig4); plt.close(fig4)
    
    smanjenje = st.slider("Smanji LWT za (°C)", 0, 5, 1)
    usteda_posto = smanjenje * 0.03
    st.metric("Potencijalna ušteda", f"{int(projekcija_kwh * usteda_posto)} kWh")

# --- NOVI TAB 6: DEFROST ANALIZA ---
with tab6:
    st.subheader("❄️ Analiza gubitaka usled odmrzavanja (Defrost)")
    st.write("Procena energije potrošene na otapanje spoljne jedinice u vlažnim i hladnim danima.")
    
    col_def1, col_def2 = st.columns(2)
    with col_def1:
        vreme_defrosta = st.slider("Prosečno trajanje defrosta (minuta)", 5, 15, 8)
        broj_defrosta = st.slider("Broj defrosta po satu (pri vlažnom vremenu)", 0.5, 3.0, 1.0)
    
    snaga_pumpe = (ukupna_potrosnja_struje / df["Rad kompresora (h)"].sum()) if df["Rad kompresora (h)"].sum() > 0 else 5.0
    # Gubitak: (vreme/60) * broj_po_satu * snaga_pumpe * broj_sati_rada
    sati_rada = df["Rad kompresora (h)"].sum()
    gubitak_kwh = (vreme_defrosta / 60) * broj_defrosta * snaga_pumpe * sati_rada
    
    with col_def2:
        st.metric("Izgubljena energija na defrost", f"{int(gubitak_kwh)} kWh")
        st.metric("Procentualni gubitak", f"{round((gubitak_kwh/ukupna_potrosnja_struje)*100, 1)} %" if ukupna_potrosnja_struje > 0 else "0%")
    
    st.info("Savet: Ako je gubitak veći od 10%, proverite da li je spoljna jedinica previše blizu zida ili je zapušena prašinom.")

# --- NOVI TAB 7: UŠTEDA VS DRUGI ---
with tab7:
    st.subheader("💰 Uporedna analiza troškova")
    st.write("Koliko bi koštalo grejanje na druge energentne za istu proizvedenu toplotu:")
    
    # Parametri za poređenje
    # Drva: 1 m3 ~ 2000 kWh, efikasnost 70%
    # Gas: 1 m3 ~ 10 kWh, efikasnost 90%
    # Pelet: 1 kg ~ 5 kWh, efikasnost 85%
    
    col_u1, col_u2, col_u3 = st.columns(3)
    cena_drva = col_u1.number_input("Cena drva (din/m3)", value=9000)
    cena_gasa = col_u2.number_input("Cena gasa (din/m3)", value=55)
    cena_peleta = col_u3.number_input("Cena peleta (din/kg)", value=35)
    
    # Kalkulacija
    trosak_drva = (ukupna_proizvedena / (2000 * 0.7)) * cena_drva
    trosak_gas = (ukupna_proizvedena / (10 * 0.9)) * cena_gasa
    trosak_pelet = (ukupna_proizvedena / (5 * 0.85)) * cena_peleta
    
    st.divider()
    
    uporedni_df = pd.DataFrame({
        "Energent": ["Toplotna pumpa", "Drva", "Gas", "Pelet"],
        "Trošak (RSD)": [int(trenutni_racun), int(trosak_drva), int(trosak_gas), int(trosak_pelet)]
    })
    
    c_res1, c_res2 = st.columns([2, 1])
    with c_res1:
        st.bar_chart(uporedni_df, x="Energent", y="Trošak (RSD)")
    with c_res2:
        st.write("### Rezime uštede")
        razlika = trosak_drva - trenutni_racun
        st.success(f"U odnosu na drva štedite: **{int(razlika)} din**")
        st.success(f"U odnosu na gas štedite: **{int(trosak_gas - trenutni_racun)} din**")

st.success("✅ Verzija 5.0 spremna sa Defrost i Ekonomskom analizom.")
