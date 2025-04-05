import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Weekly Phenotype Trends", layout="wide")
st.title("📊 Weekly Prevalence of Staphylococcus aureus Phenotypes")

@st.cache_data
def load_data():
    df = pd.read_excel("data/staph aureus phenotypes R.xlsx")
    df = df[~df["Month"].isin(["Total", "Prevalence %"])]
    df["Date"] = pd.to_datetime(df["Month"] + " 2024", format="%B %Y", errors='coerce')
    df = df.dropna(subset=["Date"])
    df["Week"] = df["Date"].dt.to_period("W").apply(lambda r: r.start_time)
    df = df[df["Week"] <= pd.to_datetime("2024-06-10")]
    
    # Ajout de 'Other'
    df_weekly = df.groupby("Week").agg({
        "MRSA": "sum",
        "VRSA": "sum",
        "Wild": "sum",
        "others": "sum",
        "Total": "sum"
    }).reset_index()
    
    return df_weekly

df_weekly = load_data()

# 🎯 Ajouter un filtre de date (semaine)
min_date = df_weekly["Week"].min()
max_date = df_weekly["Week"].max()

start_week, end_week = st.slider(
    "Sélectionner une plage de semaines",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="YYYY-MM-DD"
)

# Filtrer par semaine
filtered_df = df_weekly[(df_weekly["Week"] >= start_week) & (df_weekly["Week"] <= end_week)]

# 🎯 Choix des phénotypes à afficher
phenotypes = ["MRSA", "VRSA", "Wild", "Other"]
selected = st.multiselect("Phénotypes à afficher", phenotypes, default=phenotypes)

# 📈 Affichage Plotly
fig = go.Figure()
for pheno in selected:
    fig.add_trace(go.Scatter(
        x=filtered_df["Week"],
        y=filtered_df[pheno],
        mode="lines+markers",
        name=pheno
    ))

fig.update_layout(
    title="Évolution hebdomadaire des phénotypes (jusqu'au 10 juin 2024)",
    xaxis_title="Semaine",
    yaxis_title="Nombre de cas",
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)
