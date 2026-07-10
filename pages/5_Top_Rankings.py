import streamlit as st
import plotly.express as px
from modules.database_manager import load_admissions_with_departments


st.set_page_config(
    page_title="Top Rankings | ΔΙΠΑΕ",
    page_icon="🏆",
    layout="wide"
)


st.title("🏆 Top Rankings Εισακτέων ΔΙ.ΠΑ.Ε.")

st.markdown("""
Σε αυτή τη σελίδα εμφανίζονται κατατάξεις Τμημάτων με βάση
βάσεις εισαγωγής, επιτυχόντες και ποσοστά κάλυψης.
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

    st.subheader(f"Κατατάξεις {selected_year} — {selected_category}")

    ranking_df = filtered_df[
        [
            "department_name_clean",
            "school",
            "city",
            "exam_category",
            "final_positions",
            "admitted",
            "coverage",
            "first_score",
            "base_score",
        ]
    ].copy()

    ranking_df = ranking_df.rename(
        columns={
            "department_name_clean": "Τμήμα",
            "school": "Σχολή",
            "city": "Πόλη",
            "exam_category": "Κατηγορία",
            "final_positions": "Τελικές Θέσεις",
            "admitted": "Επιτυχόντες",
            "coverage": "Κάλυψη %",
            "first_score": "Μόρια Πρώτου",
            "base_score": "Βάση Τελευταίου",
        }
    )

    ranking_df["Κάλυψη %"] = ranking_df["Κάλυψη %"].round(2)

    top_n = st.slider(
        "Πλήθος αποτελεσμάτων",
        min_value=3,
        max_value=15,
        value=5
    )

    st.divider()

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "Υψηλότερες βάσεις",
            "Χαμηλότερες βάσεις",
            "Περισσότεροι επιτυχόντες",
            "Λιγότεροι επιτυχόντες",
            "Υψηλότερη κάλυψη",
            "Χαμηλότερη κάλυψη",
        ]
    )

    with tab1:
        st.subheader("Υψηλότερες βάσεις")

        top_base = ranking_df.sort_values(
            "Βάση Τελευταίου",
            ascending=False
        ).head(top_n)

        st.dataframe(
            top_base,
            use_container_width=True,
            hide_index=True
        )

        fig = px.bar(
            top_base,
            x="Τμήμα",
            y="Βάση Τελευταίου",
            text="Βάση Τελευταίου",
            hover_data=["Σχολή", "Πόλη", "Κατηγορία"],
            title="Υψηλότερες βάσεις"
        )

        fig.update_traces(textposition="outside")

        fig.update_layout(
            xaxis_title="Τμήμα",
            yaxis_title="Βάση Τελευταίου",
            yaxis_range=[
                0,
                max(top_base["Βάση Τελευταίου"].max() * 1.15, 10)
            ],
            uniformtext_minsize=8,
            uniformtext_mode="hide"
        )

        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Χαμηλότερες βάσεις")

        low_base = ranking_df.sort_values(
            "Βάση Τελευταίου",
            ascending=True
        ).head(top_n)

        st.dataframe(
            low_base,
            use_container_width=True,
            hide_index=True
        )

        fig = px.bar(
            low_base,
            x="Τμήμα",
            y="Βάση Τελευταίου",
            text="Βάση Τελευταίου",
            hover_data=["Σχολή", "Πόλη", "Κατηγορία"],
            title="Χαμηλότερες βάσεις"
        )

        fig.update_traces(textposition="outside")

        fig.update_layout(
            xaxis_title="Τμήμα",
            yaxis_title="Βάση Τελευταίου",
            yaxis_range=[
                0,
                max(low_base["Βάση Τελευταίου"].max() * 1.15, 10)
            ],
            uniformtext_minsize=8,
            uniformtext_mode="hide"
        )

        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("Περισσότεροι επιτυχόντες")

        top_admitted = ranking_df.sort_values(
            "Επιτυχόντες",
            ascending=False
        ).head(top_n)

        st.dataframe(
            top_admitted,
            use_container_width=True,
            hide_index=True
        )

        fig = px.bar(
            top_admitted,
            x="Τμήμα",
            y="Επιτυχόντες",
            text="Επιτυχόντες",
            hover_data=["Σχολή", "Πόλη", "Κατηγορία"],
            title="Περισσότεροι επιτυχόντες"
        )

        fig.update_traces(textposition="outside")

        fig.update_layout(
            xaxis_title="Τμήμα",
            yaxis_title="Επιτυχόντες",
            yaxis_range=[
                0,
                max(top_admitted["Επιτυχόντες"].max() * 1.15, 10)
            ],
            uniformtext_minsize=8,
            uniformtext_mode="hide"
        )

        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.subheader("Λιγότεροι επιτυχόντες")

        low_admitted = ranking_df.sort_values(
            "Επιτυχόντες",
            ascending=True
        ).head(top_n)

        st.dataframe(
            low_admitted,
            use_container_width=True,
            hide_index=True
        )

        fig = px.bar(
            low_admitted,
            x="Τμήμα",
            y="Επιτυχόντες",
            text="Επιτυχόντες",
            hover_data=["Σχολή", "Πόλη", "Κατηγορία"],
            title="Λιγότεροι επιτυχόντες"
        )

        fig.update_traces(textposition="outside")

        fig.update_layout(
            xaxis_title="Τμήμα",
            yaxis_title="Επιτυχόντες",
            yaxis_range=[
                0,
                max(low_admitted["Επιτυχόντες"].max() * 1.15, 10)
            ],
            uniformtext_minsize=8,
            uniformtext_mode="hide"
        )

        st.plotly_chart(fig, use_container_width=True)

    with tab5:
        st.subheader("Υψηλότερη κάλυψη")

        top_coverage = ranking_df.sort_values(
            "Κάλυψη %",
            ascending=False
        ).head(top_n)

        st.dataframe(
            top_coverage,
            use_container_width=True,
            hide_index=True
        )

        fig = px.bar(
            top_coverage,
            x="Τμήμα",
            y="Κάλυψη %",
            text="Κάλυψη %",
            hover_data=["Σχολή", "Πόλη", "Κατηγορία"],
            title="Υψηλότερη κάλυψη"
        )

        fig.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside"
        )

        fig.update_layout(
            xaxis_title="Τμήμα",
            yaxis_title="Κάλυψη %",
            yaxis_range=[
                0,
                max(top_coverage["Κάλυψη %"].max() * 1.15, 10)
            ],
            uniformtext_minsize=8,
            uniformtext_mode="hide"
        )

        st.plotly_chart(fig, use_container_width=True)

    with tab6:
        st.subheader("Χαμηλότερη κάλυψη")

        low_coverage = ranking_df.sort_values(
            "Κάλυψη %",
            ascending=True
        ).head(top_n)

        st.dataframe(
            low_coverage,
            use_container_width=True,
            hide_index=True
        )

        fig = px.bar(
            low_coverage,
            x="Τμήμα",
            y="Κάλυψη %",
            text="Κάλυψη %",
            hover_data=["Σχολή", "Πόλη", "Κατηγορία"],
            title="Χαμηλότερη κάλυψη"
        )

        fig.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside"
        )

        fig.update_layout(
            xaxis_title="Τμήμα",
            yaxis_title="Κάλυψη %",
            yaxis_range=[
                0,
                max(low_coverage["Κάλυψη %"].max() * 1.15, 10)
            ],
            uniformtext_minsize=8,
            uniformtext_mode="hide"
        )

        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error("Υπήρξε πρόβλημα κατά τη δημιουργία των Top Rankings.")
    st.exception(e)