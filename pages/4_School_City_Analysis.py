import streamlit as st
import plotly.express as px
from modules.database_manager import load_admissions_with_departments


st.set_page_config(
    page_title="Ανάλυση Σχολών και Πόλεων | ΔΙΠΑΕ",
    page_icon="🏫",
    layout="wide"
)


st.title("🏫 Ανάλυση ανά Σχολή και Πόλη ΔΙ.ΠΑ.Ε.")

st.markdown("""
Σε αυτή τη σελίδα εμφανίζονται συγκεντρωτικά στοιχεία εισακτέων
ανά Σχολή και ανά Πόλη του ΔΙ.ΠΑ.Ε.
""")

st.divider()


try:
    df = load_admissions_with_departments()

    if df.empty:
        st.warning("Δεν υπάρχουν ακόμη δεδομένα εισακτέων στη βάση.")
        st.stop()

    years = sorted(df["year"].dropna().unique().tolist())

    selected_year = st.selectbox(
        "Επιλογή έτους",
        years,
        index=len(years) - 1
    )

    df_year = df[df["year"] == selected_year].copy()

    category_options = [
        "Όλες οι κατηγορίες",
        "Βασικές κατηγορίες χωρίς 10%",
        "Μόνο 10%",
    ] + sorted(df_year["exam_category"].dropna().unique().tolist())

    selected_category = st.selectbox(
        "Επιλογή κατηγορίας",
        category_options
    )

    if selected_category == "Όλες οι κατηγορίες":
        filtered_df = df_year.copy()

    elif selected_category == "Βασικές κατηγορίες χωρίς 10%":
        filtered_df = df_year[
            ~df_year["exam_category"].astype(str).str.contains("10%", na=False)
        ].copy()

    elif selected_category == "Μόνο 10%":
        filtered_df = df_year[
            df_year["exam_category"].astype(str).str.contains("10%", na=False)
        ].copy()

    else:
        filtered_df = df_year[
            df_year["exam_category"] == selected_category
        ].copy()

    if filtered_df.empty:
        st.warning("Δεν υπάρχουν δεδομένα για τα επιλεγμένα φίλτρα.")
        st.stop()

    st.subheader(f"Σύνοψη {selected_year} — {selected_category}")

    total_final_positions = int(filtered_df["final_positions"].sum())
    total_admitted = int(filtered_df["admitted"].sum())

    if total_final_positions > 0:
        total_coverage = total_admitted / total_final_positions * 100
    else:
        total_coverage = 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Σχολές", filtered_df["school"].nunique())

    with col2:
        st.metric("Πόλεις", filtered_df["city"].nunique())

    with col3:
        st.metric("Τμήματα", filtered_df["department_name_clean"].nunique())

    with col4:
        st.metric("Συνολική κάλυψη", f"{total_coverage:.1f}%")

    st.divider()

    # ---------------------------------------------------------
    # Ανάλυση ανά Σχολή
    # ---------------------------------------------------------

    st.subheader("Ανάλυση ανά Σχολή")

    school_summary = (
        filtered_df
        .groupby("school", as_index=False)
        .agg(
            departments=("department_name_clean", "nunique"),
            final_positions=("final_positions", "sum"),
            admitted=("admitted", "sum"),
            average_base=("base_score", "mean"),
        )
    )

    school_summary["coverage"] = (
        school_summary["admitted"] /
        school_summary["final_positions"] * 100
    )

    school_summary_display = school_summary.rename(
        columns={
            "school": "Σχολή",
            "departments": "Τμήματα",
            "final_positions": "Τελικές Θέσεις",
            "admitted": "Επιτυχόντες",
            "coverage": "Κάλυψη %",
            "average_base": "Μέση Βάση",
        }
    )

    school_summary_display["Κάλυψη %"] = school_summary_display["Κάλυψη %"].round(2)
    school_summary_display["Μέση Βάση"] = school_summary_display["Μέση Βάση"].round(0)

    st.dataframe(
        school_summary_display,
        use_container_width=True,
        hide_index=True
    )

    fig_school_admitted = px.bar(
        school_summary_display,
        x="Σχολή",
        y="Επιτυχόντες",
        text="Επιτυχόντες",
        title="Επιτυχόντες ανά Σχολή"
    )

    fig_school_admitted.update_traces(textposition="outside")

    fig_school_admitted.update_layout(
        xaxis_title="Σχολή",
        yaxis_title="Επιτυχόντες",
        uniformtext_minsize=8,
        uniformtext_mode="hide"
    )

    st.plotly_chart(
        fig_school_admitted,
        use_container_width=True
    )

    fig_school_coverage = px.bar(
        school_summary_display,
        x="Σχολή",
        y="Κάλυψη %",
        text="Κάλυψη %",
        title="Ποσοστό κάλυψης ανά Σχολή"
    )

    fig_school_coverage.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )

    fig_school_coverage.update_layout(
        xaxis_title="Σχολή",
        yaxis_title="Κάλυψη %",
        yaxis_range=[
            0,
            max(school_summary_display["Κάλυψη %"].max() * 1.15, 10)
        ],
        uniformtext_minsize=8,
        uniformtext_mode="hide"
    )

    st.plotly_chart(
        fig_school_coverage,
        use_container_width=True
    )

    st.divider()

    # ---------------------------------------------------------
    # Ανάλυση ανά Πόλη
    # ---------------------------------------------------------

    st.subheader("Ανάλυση ανά Πόλη")

    city_summary = (
        filtered_df
        .groupby("city", as_index=False)
        .agg(
            departments=("department_name_clean", "nunique"),
            final_positions=("final_positions", "sum"),
            admitted=("admitted", "sum"),
            average_base=("base_score", "mean"),
        )
    )

    city_summary["coverage"] = (
        city_summary["admitted"] /
        city_summary["final_positions"] * 100
    )

    city_summary_display = city_summary.rename(
        columns={
            "city": "Πόλη",
            "departments": "Τμήματα",
            "final_positions": "Τελικές Θέσεις",
            "admitted": "Επιτυχόντες",
            "coverage": "Κάλυψη %",
            "average_base": "Μέση Βάση",
        }
    )

    city_summary_display["Κάλυψη %"] = city_summary_display["Κάλυψη %"].round(2)
    city_summary_display["Μέση Βάση"] = city_summary_display["Μέση Βάση"].round(0)

    st.dataframe(
        city_summary_display,
        use_container_width=True,
        hide_index=True
    )

    fig_city_admitted = px.bar(
        city_summary_display,
        x="Πόλη",
        y="Επιτυχόντες",
        text="Επιτυχόντες",
        title="Επιτυχόντες ανά Πόλη"
    )

    fig_city_admitted.update_traces(textposition="outside")

    fig_city_admitted.update_layout(
        xaxis_title="Πόλη",
        yaxis_title="Επιτυχόντες",
        uniformtext_minsize=8,
        uniformtext_mode="hide"
    )

    st.plotly_chart(
        fig_city_admitted,
        use_container_width=True
    )

    fig_city_coverage = px.bar(
        city_summary_display,
        x="Πόλη",
        y="Κάλυψη %",
        text="Κάλυψη %",
        title="Ποσοστό κάλυψης ανά Πόλη"
    )

    fig_city_coverage.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )

    fig_city_coverage.update_layout(
        xaxis_title="Πόλη",
        yaxis_title="Κάλυψη %",
        yaxis_range=[
            0,
            max(city_summary_display["Κάλυψη %"].max() * 1.15, 10)
        ],
        uniformtext_minsize=8,
        uniformtext_mode="hide"
    )

    st.plotly_chart(
        fig_city_coverage,
        use_container_width=True
    )

except Exception as e:
    st.error("Υπήρξε πρόβλημα κατά την ανάλυση Σχολών και Πόλεων.")
    st.exception(e)