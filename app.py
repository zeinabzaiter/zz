# Ajout d'un bouton d'export PDF avec explication incluse (en texte)
from textwrap import dedent

pdf_export_code = """
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import base64
import io

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

    st.markdown("---")
    st.subheader("📌 Analyse des alertes")
    st.write(f"**MRSA** : Moyenne = `{mean_mrsa:.2f}`, Écart-type = `{std_mrsa:.2f}`")
    st.write(f"**Seuil d’alerte MRSA** (moyenne + 2×écart-type) = `{threshold:.2f}`")
    st.write(f"**Maximum observé de MRSA** = `{df_weekly['MRSA'].max()}`")
    st.write(f"**Total VRSA** détecté = `{df_weekly['VRSA'].sum()}`")

    explanation_text = f\"\"\"
    MRSA : Moyenne = {mean_mrsa:.2f}
    MRSA : Écart-type = {std_mrsa:.2f}
    Seuil d’alerte MRSA = {threshold:.2f}
    Max observé MRSA = {df_weekly['MRSA'].max()}
    Total VRSA détecté = {df_weekly['VRSA'].sum()}
    \"\"\"

    if df_weekly["VRSA"].sum() < 1 and df_weekly["MRSA"].max() <= threshold:
        conclusion = "✅ Aucune alerte n’a été déclenchée : les cas de MRSA sont restés sous le seuil, et aucun VRSA n’a été détecté."
        st.success(conclusion)
        explanation_text += "\\n\\n" + conclusion

    # Export PDF
    st.markdown("---")
    st.subheader("📄 Exporter l'analyse en PDF")

    class PDF(FPDF):
        def header(self):
            self.set_font("Arial", "B", 12)
            self.cell(0, 10, "Analyse des alertes - Staph Dashboard", ln=True, align="C")

        def chapter_title(self, title):
            self.set_font("Arial", "B", 12)
            self.cell(0, 10, title, ln=True, align="L")

        def chapter_body(self, body):
            self.set_font("Arial", "", 12)
            self.multi_cell(0, 10, body)

    if st.button("📤 Générer le PDF"):
        pdf = PDF()
        pdf.add_page()
        pdf.chapter_title("Résumé des statistiques")
        pdf.chapter_body(explanation_text)

        pdf_output = io.BytesIO()
        pdf.output(pdf_output)
        b64 = base64.b64encode(pdf_output.getvalue()).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="rapport_staph_alertes.pdf">📥 Télécharger le PDF</a>'
        st.markdown(href, unsafe_allow_html=True)

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
"""

# Save to file
pdf_button_path = "/mnt/data/app_with_pdf_export.py"
with open(pdf_button_path, "w", encoding="utf-8") as f:
    f.write(dedent(pdf_export_code))

pdf_button_path
