import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Staph Dashboard", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_excel("data/staph aureus phenotypes R.xlsx")
    df = df[~df["Month"].isin(["Total", "Prevalence %"])]
    df["Date"] = pd.to_datetime(df["Month"] + " 2024", format="%B %Y", errors='coerce')
    df = df.dropna(subset=["Date"])
    df["Week"] = df["Date"].dt.to_period("W").apply(lambda r: r.start_time)
    df["Week"] = pd.to_datetime(df["Week"])
    df = df[df["Week"] <= pd.to_datetime("2024-06-10")]

    df_weekly = df.groupby("Week").agg({
        "MRSA": "sum",
        "VRSA": "sum",
        "Wild": "sum",
        "others": "sum",
        "Total": "sum"
    }).reset_index()

    return df_weekly

df_weekly = load_data()

mean_mrsa = df_weekly["MRSA"].mean()
std_mrsa = df_weekly["MRSA"].std()
threshold = mean_mrsa + 2 * std_mrsa

tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Key Metrics", "Temporal Trends", "Phenotype Analysis"])

with tab1:
    st.header("📋 Overview")
    st.markdown("Bienvenue sur le tableau de bord **Staphylococcus aureus**.")
    st.write("Utilisez les onglets pour explorer les données : métriques, tendances, alertes phénotypiques.")

with tab2:
    st.header("📊 Key Metrics")
    st.metric("Cas totaux", int(df_weekly["Total"].sum()))
    st.metric("Cas MRSA", int(df_weekly["MRSA"].sum()))
    st.metric("Cas VRSA", int(df_weekly["VRSA"].sum()))

    if df_weekly["VRSA"].sum() >= 1:
        st.error("🔴 Alerte globale : VRSA détecté dans l'ensemble des données !")
    if df_weekly["MRSA"].max() > threshold:
        st.warning("⚠️ Alerte globale : pic MRSA détecté au-delà du seuil !")

with tab3:
    st.header("📈 Temporal Trends")
    st.line_chart(df_weekly.set_index("Week")[["MRSA", "VRSA", "Wild", "others"]])

with tab4:
    st.header("🧬 Phenotype Analysis")

    min_date = df_weekly["Week"].min().to_pydatetime()
    max_date = df_weekly["Week"].max().to_pydatetime()
    start_week, end_week = st.slider(
        "Sélectionner une plage de semaines",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM-DD"
    )

    filtered_df = df_weekly[(df_weekly["Week"] >= start_week) & (df_weekly["Week"] <= end_week)]

    if filtered_df["VRSA"].sum() >= 1:
        st.error("⚠️ Alerte : au moins 1 cas de VRSA détecté dans la période sélectionnée.")
    latest_mrsa = filtered_df["MRSA"].iloc[-1] if not filtered_df.empty else 0
    if latest_mrsa > threshold:
        st.warning(f"🚨 Alerte : MRSA dépasse le seuil ({latest_mrsa:.0f} > {threshold:.0f})")

    phenotypes = ["MRSA", "VRSA", "Wild", "others"]
    selected = st.multiselect("Phénotypes à afficher", phenotypes, default=phenotypes)

    # Graphique en nombre de cas
    fig = go.Figure()
    for pheno in selected:
        fig.add_trace(go.Scatter(
            x=filtered_df["Week"],
            y=filtered_df[pheno],
            mode="lines+markers",
            name=pheno
        ))
    fig.update_layout(
        title="Évolution hebdomadaire des phénotypes sélectionnés",
        xaxis_title="Semaine",
        yaxis_title="Nombre de cas",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Graphique en pourcentage
    st.subheader("📊 Prévalence des phénotypes en pourcentage (%)")
    for pheno in selected:
        filtered_df[f"{pheno}_pct"] = (filtered_df[pheno] / filtered_df["Total"]) * 100

    fig_pct = go.Figure()
    for pheno in selected:
        fig_pct.add_trace(go.Scatter(
            x=filtered_df["Week"],
            y=filtered_df[f"{pheno}_pct"],
            mode="lines+markers",
            name=f"{pheno} (%)"
        ))
    fig_pct.update_layout(
        title="Prévalence en pourcentage des phénotypes",
        xaxis_title="Semaine",
        yaxis_title="Pourcentage (%)",
        hovermode="x unified"
    )
    st.plotly_chart(fig_pct, use_container_width=True)
