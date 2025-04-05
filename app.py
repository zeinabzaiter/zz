
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
    df_weekly = df.groupby("Week").agg({
        "MRSA": "sum",
        "VRSA": "sum",
        "Wild": "sum",
        "Total": "sum"
    }).reset_index()
    return df_weekly

df_weekly = load_data()

phenotypes = ["MRSA", "VRSA", "Wild"]
selected = st.multiselect("Select phenotypes to display", phenotypes, default=phenotypes)

fig = go.Figure()
for pheno in selected:
    fig.add_trace(go.Scatter(
        x=df_weekly["Week"],
        y=df_weekly[pheno],
        mode="lines+markers",
        name=pheno
    ))

fig.update_layout(
    title="Weekly Phenotype Distribution (up to June 10, 2024)",
    xaxis_title="Week",
    yaxis_title="Number of Cases",
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)
