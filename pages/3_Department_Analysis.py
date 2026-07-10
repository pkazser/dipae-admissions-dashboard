import streamlit as st
import plotly.express as px
from modules.database_manager import load_admissions_with_departments


st.set_page_config(
    page_title="Ανάλυση Τμήματος | ΔΙΠΑΕ",
    page_icon="🏛️",
    layout="wide"
)


st.title("🏛️ Ανάλυση ανά Τμήμα ΔΙ.ΠΑ.Ε.")

st.markdown("""
Σε αυτή τη σελίδα εμφανίζεται αναλυτική εικόνα ενός Τμήματος
ανά έτος, σχολή, πόλη και κατηγορία εισαγωγής.
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

    departments = sorted(
        df_year["department_name_clean"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_department = st.selectbox(
        "Επιλογή Τμήματος",
        departments
    )

    dept_df = df_year[
        df_year["department_name_clean"] == selected_department
    ].copy()

    if dept_df.empty:
        st.warning("Δεν βρέθηκαν δεδομένα για το επιλεγμένο Τμήμα.")
        st.stop()

    first_row = dept_df.iloc[0]

    st.subheader(selected_department)

    col_info1, col_info2, col_info3, col_info4 = st.columns(4)

    with col_info1:
        st.metric("Σχολή", first_row["school"])

    with col_info2:
        st.metric("Πόλη", first_row["city"])

    with col_info3:
        st.metric("Κωδικός ΔΙΠΑΕ", first_row["department_code"])

    with col_info4:
        st.metric("Κωδικός Υπουργείου", first_row["ministry_department_code"])

    if first_row["website"] is not None and str(first_row["website"]) != "None":
        if str(first_row["website"]).strip() != "":
            st.markdown(f"🔗 [Ιστοσελίδα Τμήματος]({first_row['website']})")

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    total_final_positions = int(dept_df["final_positions"].sum())
    total_admitted = int(dept_df["admitted"].sum())

    if total_final_positions > 0:
        total_coverage = total_admitted / total_final_positions * 100
    else:
        total_coverage = 0

    with col1:
        st.metric("Κατηγορίες", dept_df["exam_category"].nunique())

    with col2:
        st.metric("Τελικές θέσεις", total_final_positions)

    with col3:
        st.metric("Επιτυχόντες", total_admitted)

    with col4:
        st.metric("Συνολική κάλυψη", f"{total_coverage:.1f}%")

    st.caption(
        "Η συνολική κάλυψη υπολογίζεται ως σύνολο επιτυχόντων / "
        "σύνολο τελικών θέσεων για όλες τις κατηγορίες του επιλεγμένου Τμήματος."
    )

    st.divider()

    st.subheader("Πίνακας ανά κατηγορία εισαγωγής")

    display_df = dept_df[
        [
            "exam_category",
            "admission_type",
            "scientific_fields",
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
            "admission_type": "Είδος Θέσης",
            "scientific_fields": "Επιστημονικά Πεδία",
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

    st.divider()

    st.subheader("Γραφήματα Τμήματος")

    fig_admitted = px.bar(
        display_df,
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

    fig_coverage = px.bar(
        display_df,
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
            max(display_df["Κάλυψη %"].max() * 1.15, 10)
        ],
        uniformtext_minsize=8,
        uniformtext_mode="hide"
    )

    st.plotly_chart(
        fig_coverage,
        use_container_width=True
    )

    fig_base = px.bar(
        display_df,
        x="Κατηγορία",
        y="Βάση Τελευταίου",
        text="Βάση Τελευταίου",
        title="Βάση τελευταίου ανά κατηγορία"
    )

    fig_base.update_traces(
        textposition="outside"
    )

    fig_base.update_layout(
        xaxis_title="Κατηγορία",
        yaxis_title="Βάση Τελευταίου",
        yaxis_range=[
            0,
            max(display_df["Βάση Τελευταίου"].max() * 1.15, 10)
        ],
        uniformtext_minsize=8,
        uniformtext_mode="hide"
    )

    st.plotly_chart(
        fig_base,
        use_container_width=True
    )

except Exception as e:
    st.error("Υπήρξε πρόβλημα κατά την ανάλυση του Τμήματος.")
    st.exception(e)