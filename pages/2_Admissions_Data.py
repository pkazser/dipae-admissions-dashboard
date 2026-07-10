import streamlit as st
import plotly.express as px
from modules.database_manager import load_admissions


st.set_page_config(
    page_title="Δεδομένα Εισακτέων | ΔΙΠΑΕ",
    page_icon="📊",
    layout="wide"
)


st.title("📊 Δεδομένα Εισακτέων ΔΙ.ΠΑ.Ε.")

st.markdown("""
Σε αυτή τη σελίδα εμφανίζονται τα δεδομένα εισακτέων που έχουν εισαχθεί
στη βάση δεδομένων της εφαρμογής.
""")

st.divider()


try:
    df = load_admissions()

    if df.empty:
        st.warning("Δεν υπάρχουν ακόμη δεδομένα εισακτέων στη βάση.")
        st.stop()

    years = sorted(df["year"].dropna().unique().tolist())
    categories = sorted(df["exam_category"].dropna().unique().tolist())

    col_filter1, col_filter2 = st.columns(2)

    with col_filter1:
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
    ] + categories

    with col_filter2:
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
        st.warning("Δεν υπάρχουν δεδομένα για την επιλεγμένη κατηγορία.")
        st.stop()

    st.subheader(f"Σύνοψη {selected_year} — {selected_category}")

    total_initial_positions = int(filtered_df["initial_positions"].sum())
    total_final_positions = int(filtered_df["final_positions"].sum())
    total_admitted = int(filtered_df["admitted"].sum())

    if total_final_positions > 0:
        total_coverage = total_admitted / total_final_positions * 100
    else:
        total_coverage = 0

    average_base = filtered_df["base_score"].mean()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Αρχικές θέσεις", total_initial_positions)

    with col2:
        st.metric("Τελικές θέσεις", total_final_positions)

    with col3:
        st.metric("Επιτυχόντες", total_admitted)

    with col4:
        st.metric("Συνολική κάλυψη", f"{total_coverage:.1f}%")

    col5, col6, col7 = st.columns(3)

    with col5:
        st.metric("Εγγραφές", len(filtered_df))

    with col6:
        st.metric("Μέση βάση", f"{average_base:.0f}")

    with col7:
        st.metric("Κατηγορίες", filtered_df["exam_category"].nunique())

    st.caption(
        "Σημείωση: Η συνολική κάλυψη υπολογίζεται ως "
        "σύνολο επιτυχόντων / σύνολο τελικών θέσεων. "
        "Η μέση βάση είναι ενδεικτικός μέσος όρος των βάσεων των εγγραφών."
    )

    st.divider()

    st.subheader("Ανάλυση ανά κατηγορία")

    summary_by_category = (
        filtered_df
        .groupby("exam_category", as_index=False)
        .agg(
            initial_positions=("initial_positions", "sum"),
            final_positions=("final_positions", "sum"),
            admitted=("admitted", "sum"),
            departments=("department_name_raw", "count"),
            average_base=("base_score", "mean"),
        )
    )

    summary_by_category["coverage"] = (
        summary_by_category["admitted"]
        / summary_by_category["final_positions"]
        * 100
    )

    summary_by_category = summary_by_category.rename(
        columns={
            "exam_category": "Κατηγορία",
            "initial_positions": "Αρχικές Θέσεις",
            "final_positions": "Τελικές Θέσεις",
            "admitted": "Επιτυχόντες",
            "departments": "Εγγραφές",
            "average_base": "Μέση Βάση",
            "coverage": "Κάλυψη %",
        }
    )

    summary_by_category["Κάλυψη %"] = summary_by_category["Κάλυψη %"].round(2)
    summary_by_category["Μέση Βάση"] = summary_by_category["Μέση Βάση"].round(0)

    st.dataframe(
        summary_by_category,
        use_container_width=True,
        hide_index=True
    )
    
    st.divider()
    st.subheader("Γραφήματα ανά κατηγορία")

    fig_admitted = px.bar(
        summary_by_category,
        x="Κατηγορία",
        y="Επιτυχόντες",
        text="Επιτυχόντες",
        title="Επιτυχόντες ανά κατηγορία"
    )

    fig_admitted.update_traces(
        textposition="outside"
    )

    fig_admitted.update_layout(
        xaxis_title="Κατηγορία",
        yaxis_title="Επιτυχόντες",
        uniformtext_minsize=8,
        uniformtext_mode="hide"
    )

    st.plotly_chart(
        fig_admitted,
        use_container_width=True
    )

    fig_positions = px.bar(
        summary_by_category,
        x="Κατηγορία",
        y="Τελικές Θέσεις",
        text="Τελικές Θέσεις",
        title="Τελικές θέσεις ανά κατηγορία"
    )

    fig_positions.update_traces(
        textposition="outside"
    )

    fig_positions.update_layout(
        xaxis_title="Κατηγορία",
        yaxis_title="Τελικές Θέσεις",
        uniformtext_minsize=8,
        uniformtext_mode="hide"
    )

    st.plotly_chart(
        fig_positions,
        use_container_width=True
    )

    fig_coverage = px.bar(
        summary_by_category,
        x="Κατηγορία",
        y="Κάλυψη %",
        text="Κάλυψη %",
        title="Ποσοστό κάλυψης ανά κατηγορία"
    )

    fig_coverage.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )

    fig_coverage.update_layout(
        xaxis_title="Κατηγορία",
        yaxis_title="Κάλυψη %",
        yaxis_range=[
            0,
            max(summary_by_category["Κάλυψη %"].max() * 1.15, 10)
        ],
        uniformtext_minsize=8,
        uniformtext_mode="hide"
    )

    st.plotly_chart(
        fig_coverage,
        use_container_width=True
    )
    st.subheader("Πίνακας δεδομένων")

    display_df = filtered_df[
        [
            "exam_category",
            "ministry_department_code",
            "department_name_raw",
            "scientific_fields",
            "admission_type",
            "initial_positions",
            "final_positions",
            "admitted",
            "coverage",
            "first_score",
            "base_score",
        ]
    ].copy()

    display_df = display_df.rename(
        columns={
            "exam_category": "Κατηγορία",
            "ministry_department_code": "Κωδικός Υπουργείου",
            "department_name_raw": "Τμήμα",
            "scientific_fields": "Επιστημονικά Πεδία",
            "admission_type": "Είδος Θέσης",
            "initial_positions": "Αρχικές Θέσεις",
            "final_positions": "Τελικές Θέσεις",
            "admitted": "Επιτυχόντες",
            "coverage": "Κάλυψη %",
            "first_score": "Μόρια Πρώτου",
            "base_score": "Βάση Τελευταίου",
        }
    )

    display_df["Κάλυψη %"] = display_df["Κάλυψη %"].round(2)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

except Exception as e:
    st.error("Υπήρξε πρόβλημα κατά την ανάγνωση των δεδομένων.")
    st.exception(e)