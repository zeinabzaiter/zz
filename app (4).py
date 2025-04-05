import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Staphylococcus Phenotypes Dashboard", layout="wide")
st.title("🦠 Staphylococcus Phenotype Surveillance Dashboard")

# Upload Excel file
uploaded_file = st.file_uploader("Upload the Excel file with phenotype counts (no daptomycin)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df['Month'] = df['Month'].astype(str)

    st.subheader("📊 Monthly Distribution of Phenotypes")
    
    # Select phenotypes to show
    phenotypes = ['Wild', 'MRSA', 'VRSA', 'Other']
    selected = st.multiselect("Select phenotypes to display:", phenotypes, default=phenotypes)

    # Plot count evolution
    fig_count = px.line(df, x='Month', y=selected, markers=True,
                        labels={"value": "Number of Isolates", "variable": "Phenotype"},
                        title="Phenotype Counts per Month")
    st.plotly_chart(fig_count, use_container_width=True)

    # Prevalence calculation
    prevalence_df = df.copy()
    for col in phenotypes:
        prevalence_df[col] = (prevalence_df[col] / prevalence_df['Total']) * 100

    fig_prev = px.line(prevalence_df, x='Month', y=selected, markers=True,
                       labels={"value": "Prevalence (%)", "variable": "Phenotype"},
                       title="Phenotype Prevalence per Month")
    st.plotly_chart(fig_prev, use_container_width=True)

    # Show data table
    with st.expander("📁 View Data Table"):
        st.dataframe(df)

    # Download CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Data as CSV", data=csv, file_name="phenotypes_by_month.csv", mime="text/csv")

else:
    st.info("👆 Please upload an Excel file to begin.")
