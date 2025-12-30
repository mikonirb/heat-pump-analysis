import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

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

# ----------------------------------------------------------------
# TAB 1 – PREGLED SISTEMA
# ----------------------------------------------------------------
with tab1:
    st.subheader("📊 Osnovni pokazatelji")
    st.dataframe(df.round(2), use_container_width=True)

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

    stanje = (
        "🟢 ZDRAVA" if score >= 85 else
        "🟡 DOBRA" if score >= 70 else
        "🟠 OPTEREĆENA" if score >= 50 else
        "🔴 RIZIČNA"
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Prosečan COP", round(avg_cop, 2))
    col2.metric("Startova / dan", round(avg_start, 1))
    col3.metric("Health score", f"{score}/100", stanje)

    colA, colB = st.columns(2)
    with colA:
        fig, ax = plt.subplots()
        ax.bar(df["Mesec"], df["kWh/dan"])
        ax.set_title("kWh/dan")
        st.pyplot(fig)

    with colB:
        fig, ax = plt.subplots()
        ax.plot(df["Mesec"], df["COP"], marker="o")
        ax.set_title("COP po mesecima")
        st.pyplot(fig)

# ----------------------------------------------------------------
# TAB 2 – SPOLJNA TEMPERATURA & KRIVA
# ----------------------------------------------------------------
with tab2:
    st.subheader("🌡 Analiza u odnosu na spoljnu temperaturu")

    avg_out = df["Spoljna T (°C)"].mean()
    ideal_lwt = 30 + (15 - avg_out) * 0.4

    if avg_lwt <= ideal_lwt + 1:
        st.success("🟢 Kriva grejanja je dobro pogođena.")
    elif avg_lwt <= ideal_lwt + 3:
        st.warning("🟡 Kriva je blago previsoka – ima prostora za optimizaciju.")
    else:
        st.error("🔴 Kriva je previsoka – sistem radi nepotrebno teško.")

    st.write(f"Idealni LWT za prosečnu spoljnu T ≈ **{ideal_lwt:.1f} °C**")

    col1, col2 = st.columns(2)
    with col1:
        fig, ax = plt.subplots()
        ax.scatter(df["Spoljna T (°C)"], df["COP"])
        ax.set_xlabel("Spoljna T (°C)")
        ax.set_ylabel("COP")
        ax.set_title("COP vs spoljna T")
        st.pyplot(fig)

    with col2:
        fig, ax = plt.subplots()
        ax.scatter(df["Spoljna T (°C)"], df["kWh/dan"])
        ax.set_xlabel("Spoljna T (°C)")
        ax.set_ylabel("kWh/dan")
        ax.set_title("Potrošnja vs spoljna T")
        st.pyplot(fig)

# ----------------------------------------------------------------
# TAB 3 – EPS ZONE
# ----------------------------------------------------------------
with tab3:
    st.subheader("💡 EPS obračun po zonama")

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

    fig, ax = plt.subplots()
    ax.bar(df_eps["Mesec"], df_eps["Zelena (kWh)"], label="Zelena")
    ax.bar(df_eps["Mesec"], df_eps["Plava (kWh)"],
           bottom=df_eps["Zelena (kWh)"], label="Plava")
    ax.bar(df_eps["Mesec"], df_eps["Crvena (kWh)"],
           bottom=df_eps["Zelena (kWh)"] + df_eps["Plava (kWh)"], label="Crvena")
    ax.set_ylabel("kWh")
    ax.legend()
    st.pyplot(fig)

# ----------------------------------------------------------------
# TAB 4 – SEZONA & PROJEKCIJA
# ----------------------------------------------------------------
with tab4:
    st.subheader("📅 Sezonski pregled")

    sezona_dana = st.number_input("Trajanje sezone (dana)", 90, 200, 150)
    do_sada = df["Potrošena struja (kWh)"].sum()
    prosek = df["kWh/dan"].mean()
    projekcija = prosek * sezona_dana

    col1, col2, col3 = st.columns(3)
    col1.metric("Potrošnja do sada (kWh)", round(do_sada, 0))
    col2.metric("Prosek kWh/dan", round(prosek, 1))
    col3.metric("Projekcija sezone (kWh)", round(projekcija, 0))

st.success("✅ V4.1 ALL-IN-ONE aktivna – sve objedinjeno u jednoj aplikaciji.")


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

    if mesecna_proj > 1600:
        st.error("⚠️ Ulazak u CRVENU zonu!")
    elif mesecna_proj > 1200:
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
