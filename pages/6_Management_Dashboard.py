import streamlit as st
import plotly.express as px
from modules.database_manager import load_admissions_with_departments


st.set_page_config(
    page_title="Dashboard Διοίκησης | ΔΙΠΑΕ",
    page_icon="📈",
    layout="wide"
)


st.title("📈 Dashboard Διοίκησης Εισακτέων ΔΙ.ΠΑ.Ε.")

st.markdown("""
Κεντρική σελίδα συνοπτικής παρακολούθησης των αποτελεσμάτων εισαγωγής
του ΔΙ.ΠΑ.Ε. ανά έτος, κατηγορία, σχολή και πόλη.
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
        "Βασικές κατηγορίες χωρίς 10%",
        "Όλες οι κατηγορίες",
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

    # ---------------------------------------------------------
    # KPIs
    # ---------------------------------------------------------

    total_initial_positions = int(filtered_df["initial_positions"].sum())
    total_final_positions = int(filtered_df["final_positions"].sum())
    total_admitted = int(filtered_df["admitted"].sum())

    if total_final_positions > 0:
        total_coverage = total_admitted / total_final_positions * 100
    else:
        total_coverage = 0

    average_base = filtered_df["base_score"].mean()

    st.subheader(f"Κεντρική σύνοψη {selected_year} — {selected_category}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Αρχικές θέσεις", total_initial_positions)

    with col2:
        st.metric("Τελικές θέσεις", total_final_positions)

    with col3:
        st.metric("Επιτυχόντες", total_admitted)

    with col4:
        st.metric("Συνολική κάλυψη", f"{total_coverage:.1f}%")

    col5, col6, col7, col8 = st.columns(4)

    with col5:
        st.metric("Σχολές", filtered_df["school"].nunique())

    with col6:
        st.metric("Πόλεις", filtered_df["city"].nunique())

    with col7:
        st.metric("Τμήματα", filtered_df["department_name_clean"].nunique())

    with col8:
        st.metric("Μέση βάση", f"{average_base:.0f}")

    st.caption(
        "Η συνολική κάλυψη υπολογίζεται ως σύνολο επιτυχόντων / σύνολο τελικών θέσεων. "
        "Η μέση βάση είναι ενδεικτικός μέσος όρος εγγραφών και δεν αποτελεί επίσημη ενιαία βάση Ιδρύματος."
    )

    st.divider()

    # ---------------------------------------------------------
    # Summary by category
    # ---------------------------------------------------------

    st.subheader("Σύνοψη ανά κατηγορία εισαγωγής")

    category_summary = (
        filtered_df
        .groupby("exam_category", as_index=False)
        .agg(
            departments=("department_name_clean", "nunique"),
            final_positions=("final_positions", "sum"),
            admitted=("admitted", "sum"),
            average_base=("base_score", "mean"),
        )
    )

    category_summary["coverage"] = (
        category_summary["admitted"]
        / category_summary["final_positions"]
        * 100
    )

    category_display = category_summary.rename(
        columns={
            "exam_category": "Κατηγορία",
            "departments": "Τμήματα",
            "final_positions": "Τελικές Θέσεις",
            "admitted": "Επιτυχόντες",
            "coverage": "Κάλυψη %",
            "average_base": "Μέση Βάση",
        }
    )

    category_display["Κάλυψη %"] = category_display["Κάλυψη %"].round(2)
    category_display["Μέση Βάση"] = category_display["Μέση Βάση"].round(0)

    st.dataframe(
        category_display,
        use_container_width=True,
        hide_index=True
    )

    fig_category = px.bar(
        category_display,
        x="Κατηγορία",
        y="Επιτυχόντες",
        text="Επιτυχόντες",
        title="Επιτυχόντες ανά κατηγορία"
    )

    fig_category.update_traces(textposition="outside")

    fig_category.update_layout(
        xaxis_title="Κατηγορία",
        yaxis_title="Επιτυχόντες",
        uniformtext_minsize=8,
        uniformtext_mode="hide"
    )

    st.plotly_chart(
        fig_category,
        use_container_width=True
    )

    st.divider()

    # ---------------------------------------------------------
    # School and city summaries
    # ---------------------------------------------------------

    col_school, col_city = st.columns(2)

    with col_school:
        st.subheader("Σύνοψη ανά Σχολή")

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
            school_summary["admitted"]
            / school_summary["final_positions"]
            * 100
        )

        school_display = school_summary.rename(
            columns={
                "school": "Σχολή",
                "departments": "Τμήματα",
                "final_positions": "Θέσεις",
                "admitted": "Επιτυχόντες",
                "coverage": "Κάλυψη %",
                "average_base": "Μέση Βάση",
            }
        )

        school_display["Κάλυψη %"] = school_display["Κάλυψη %"].round(2)
        school_display["Μέση Βάση"] = school_display["Μέση Βάση"].round(0)

        st.dataframe(
            school_display,
            use_container_width=True,
            hide_index=True
        )

    with col_city:
        st.subheader("Σύνοψη ανά Πόλη")

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
            city_summary["admitted"]
            / city_summary["final_positions"]
            * 100
        )

        city_display = city_summary.rename(
            columns={
                "city": "Πόλη",
                "departments": "Τμήματα",
                "final_positions": "Θέσεις",
                "admitted": "Επιτυχόντες",
                "coverage": "Κάλυψη %",
                "average_base": "Μέση Βάση",
            }
        )

        city_display["Κάλυψη %"] = city_display["Κάλυψη %"].round(2)
        city_display["Μέση Βάση"] = city_display["Μέση Βάση"].round(0)

        st.dataframe(
            city_display,
            use_container_width=True,
            hide_index=True
        )

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        fig_school = px.bar(
            school_display,
            x="Σχολή",
            y="Επιτυχόντες",
            text="Επιτυχόντες",
            title="Επιτυχόντες ανά Σχολή"
        )

        fig_school.update_traces(textposition="outside")

        fig_school.update_layout(
            xaxis_title="Σχολή",
            yaxis_title="Επιτυχόντες",
            uniformtext_minsize=8,
            uniformtext_mode="hide"
        )

        st.plotly_chart(
            fig_school,
            use_container_width=True
        )

    with col_chart2:
        fig_city = px.bar(
            city_display,
            x="Πόλη",
            y="Επιτυχόντες",
            text="Επιτυχόντες",
            title="Επιτυχόντες ανά Πόλη"
        )

        fig_city.update_traces(textposition="outside")

        fig_city.update_layout(
            xaxis_title="Πόλη",
            yaxis_title="Επιτυχόντες",
            uniformtext_minsize=8,
            uniformtext_mode="hide"
        )

        st.plotly_chart(
            fig_city,
            use_container_width=True
        )

    st.divider()

    # ---------------------------------------------------------
    # Top / risk sections
    # ---------------------------------------------------------

    st.subheader("Γρήγορες επισημάνσεις")

    department_summary = (
        filtered_df
        .groupby(
            [
                "department_name_clean",
                "school",
                "city",
            ],
            as_index=False
        )
        .agg(
            final_positions=("final_positions", "sum"),
            admitted=("admitted", "sum"),
            average_base=("base_score", "mean"),
        )
    )

    department_summary["coverage"] = (
        department_summary["admitted"]
        / department_summary["final_positions"]
        * 100
    )

    department_display = department_summary.rename(
        columns={
            "department_name_clean": "Τμήμα",
            "school": "Σχολή",
            "city": "Πόλη",
            "final_positions": "Θέσεις",
            "admitted": "Επιτυχόντες",
            "coverage": "Κάλυψη %",
            "average_base": "Μέση Βάση",
        }
    )

    department_display["Κάλυψη %"] = department_display["Κάλυψη %"].round(2)
    department_display["Μέση Βάση"] = department_display["Μέση Βάση"].round(0)

    col_top, col_low = st.columns(2)

    with col_top:
        st.markdown("### Τμήματα με περισσότερους επιτυχόντες")

        top_departments = department_display.sort_values(
            "Επιτυχόντες",
            ascending=False
        ).head(5)

        st.dataframe(
            top_departments,
            use_container_width=True,
            hide_index=True
        )

    with col_low:
        st.markdown("### Τμήματα με χαμηλότερη κάλυψη")

        low_coverage_departments = department_display.sort_values(
            "Κάλυψη %",
            ascending=True
        ).head(5)

        st.dataframe(
            low_coverage_departments,
            use_container_width=True,
            hide_index=True
        )

    col_fig_top, col_fig_low = st.columns(2)

    with col_fig_top:
        fig_top = px.bar(
            top_departments,
            x="Τμήμα",
            y="Επιτυχόντες",
            text="Επιτυχόντες",
            title="Top-5 τμήματα σε επιτυχόντες"
        )

        fig_top.update_traces(textposition="outside")

        fig_top.update_layout(
            xaxis_title="Τμήμα",
            yaxis_title="Επιτυχόντες",
            uniformtext_minsize=8,
            uniformtext_mode="hide"
        )

        st.plotly_chart(
            fig_top,
            use_container_width=True
        )

    with col_fig_low:
        fig_low = px.bar(
            low_coverage_departments,
            x="Τμήμα",
            y="Κάλυψη %",
            text="Κάλυψη %",
            title="Top-5 χαμηλότερης κάλυψης"
        )

        fig_low.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside"
        )

        fig_low.update_layout(
            xaxis_title="Τμήμα",
            yaxis_title="Κάλυψη %",
            yaxis_range=[
                0,
                max(low_coverage_departments["Κάλυψη %"].max() * 1.25, 10)
            ],
            uniformtext_minsize=8,
            uniformtext_mode="hide"
        )

        st.plotly_chart(
            fig_low,
            use_container_width=True
        )

except Exception as e:
    st.error("Υπήρξε πρόβλημα κατά τη δημιουργία του Dashboard Διοίκησης.")
    st.exception(e)