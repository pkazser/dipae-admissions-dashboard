import streamlit as st
import plotly.express as px
from modules.database_manager import load_admissions_with_departments


st.set_page_config(
    page_title="Dashboard Διοίκησης | ΔΙΠΑΕ",
    page_icon="📊",
    layout="wide"
)


st.title("📊 Dashboard Διοίκησης Εισακτέων ΔΙ.ΠΑ.Ε.")

st.markdown("""
Συνοπτική διοικητική εικόνα των εισακτέων του ΔΙ.ΠΑ.Ε. ανά έτος, Σχολή, Πόλη και Τμήμα.

**Μεθοδολογικοί κανόνες της εφαρμογής:**

- Η ανάλυση γίνεται πάντα για **όλες τις κατηγορίες εισαγωγής**.
- Οι **Συνολικές Θέσεις** υπολογίζονται από τις **Αρχικές Θέσεις**.
- Η **Συνολική Κάλυψη** υπολογίζεται ως: Επιτυχόντες / Συνολικές Θέσεις.
- Δεν εμφανίζονται τελικές θέσεις ή φαινόμενη μεταβολή θέσεων.
- Δεν χρησιμοποιούνται μέσοι όροι βάσεων ή μέσοι όροι πρώτου υποψηφίου.
- Η **Βάση ΓΕΛ Ημερήσια** εμφανίζεται μόνο σε επίπεδο Τμήματος.
""")

st.divider()


def get_gel_day_scores(df_year):
    """
    Επιστρέφει βάση τελευταίου και βαθμό πρώτου από τη ΓΕΛ Ημερήσια ανά Τμήμα.
    Χρησιμοποιείται μόνο σε πίνακες Τμημάτων και σε επισημάνσεις Τμημάτων.
    """

    df_gel = df_year[
        df_year["exam_category"] == "ΓΕΛ Ημερήσια"
    ].copy()

    if df_gel.empty:
        return None

    scores = (
        df_gel[
            [
                "department_code",
                "first_score",
                "base_score",
            ]
        ]
        .drop_duplicates(subset=["department_code"])
        .rename(
            columns={
                "first_score": "gel_day_first_score",
                "base_score": "gel_day_base_score",
            }
        )
    )

    return scores


def build_department_summary(df_year):
    """
    Δημιουργεί σύνοψη ανά Τμήμα για όλες τις κατηγορίες.

    Οι συνολικές θέσεις είναι οι αρχικές θέσεις.
    Οι βάσεις προέρχονται από τη ΓΕΛ Ημερήσια.
    """

    summary = (
        df_year
        .groupby(
            [
                "department_code",
                "department_name_clean",
                "school",
                "city",
            ],
            as_index=False
        )
        .agg(
            total_positions=("initial_positions", "sum"),
            total_admitted=("admitted", "sum"),
        )
    )

    summary["empty_positions"] = (
        summary["total_positions"]
        - summary["total_admitted"]
    )

    summary["coverage"] = (
        summary["total_admitted"]
        / summary["total_positions"]
        * 100
    )

    gel_scores = get_gel_day_scores(df_year)

    if gel_scores is not None:
        summary = summary.merge(
            gel_scores,
            on="department_code",
            how="left"
        )
    else:
        summary["gel_day_first_score"] = None
        summary["gel_day_base_score"] = None

    return summary


def build_group_summary(department_summary, group_field):
    """
    Δημιουργεί σύνοψη ανά Σχολή ή Πόλη.
    Δεν υπολογίζει μέσους όρους βάσεων.
    """

    summary = (
        department_summary
        .groupby(group_field, as_index=False)
        .agg(
            departments=("department_code", "nunique"),
            total_positions=("total_positions", "sum"),
            total_admitted=("total_admitted", "sum"),
            empty_positions=("empty_positions", "sum"),
        )
    )

    summary["coverage"] = (
        summary["total_admitted"]
        / summary["total_positions"]
        * 100
    )

    return summary


def format_department_table(df):
    """
    Πίνακας Τμημάτων για εμφάνιση.
    """

    display = df[
        [
            "department_name_clean",
            "school",
            "city",
            "total_positions",
            "total_admitted",
            "empty_positions",
            "coverage",
            "gel_day_first_score",
            "gel_day_base_score",
        ]
    ].copy()

    display = display.rename(
        columns={
            "department_name_clean": "Τμήμα",
            "school": "Σχολή",
            "city": "Πόλη",
            "total_positions": "Συνολικές Θέσεις",
            "total_admitted": "Επιτυχόντες",
            "empty_positions": "Κενές Θέσεις",
            "coverage": "Κάλυψη %",
            "gel_day_first_score": "Πρώτος ΓΕΛ Ημ.",
            "gel_day_base_score": "Βάση ΓΕΛ Ημ.",
        }
    )

    for col in [
        "Κάλυψη %",
        "Πρώτος ΓΕΛ Ημ.",
        "Βάση ΓΕΛ Ημ.",
    ]:
        display[col] = display[col].round(2)

    return display


def format_group_table(df, group_field, group_label):
    """
    Πίνακας Σχολής ή Πόλης για εμφάνιση.
    """

    display = df[
        [
            group_field,
            "departments",
            "total_positions",
            "total_admitted",
            "empty_positions",
            "coverage",
        ]
    ].copy()

    display = display.rename(
        columns={
            group_field: group_label,
            "departments": "Τμήματα",
            "total_positions": "Συνολικές Θέσεις",
            "total_admitted": "Επιτυχόντες",
            "empty_positions": "Κενές Θέσεις",
            "coverage": "Κάλυψη %",
        }
    )

    display["Κάλυψη %"] = display["Κάλυψη %"].round(2)

    return display


def highlight_empty_positions(val):
    """
    Χρωματισμός κενών θέσεων.
    """

    try:
        value = float(val)
    except Exception:
        return ""

    if value > 0:
        return "background-color: #f8d7da; color: #721c24; font-weight: bold;"
    else:
        return "background-color: #d4edda; color: #155724; font-weight: bold;"


def highlight_coverage(val):
    """
    Χρωματισμός κάλυψης.
    """

    try:
        value = float(val)
    except Exception:
        return ""

    if value >= 100:
        return "background-color: #d4edda; color: #155724; font-weight: bold;"
    elif value >= 90:
        return "background-color: #fff3cd; color: #664d03; font-weight: bold;"
    else:
        return "background-color: #f8d7da; color: #721c24; font-weight: bold;"


def style_table(df):
    """
    Styling πινάκων.
    """

    style_obj = df.style

    if "Κενές Θέσεις" in df.columns:
        try:
            style_obj = style_obj.map(
                highlight_empty_positions,
                subset=["Κενές Θέσεις"]
            )
        except AttributeError:
            style_obj = style_obj.applymap(
                highlight_empty_positions,
                subset=["Κενές Θέσεις"]
            )

    if "Κάλυψη %" in df.columns:
        try:
            style_obj = style_obj.map(
                highlight_coverage,
                subset=["Κάλυψη %"]
            )
        except AttributeError:
            style_obj = style_obj.applymap(
                highlight_coverage,
                subset=["Κάλυψη %"]
            )

    return style_obj


try:
    df = load_admissions_with_departments()

    if df.empty:
        st.warning("Δεν υπάρχουν ακόμη δεδομένα εισακτέων στη βάση.")
        st.stop()

    # ---------------------------------------------------------
    # Φίλτρο έτους
    # ---------------------------------------------------------

    years = sorted(df["year"].dropna().unique().tolist())

    selected_year = st.selectbox(
        "Έτος",
        years,
        index=len(years) - 1
    )

    df_year = df[df["year"] == selected_year].copy()

    if df_year.empty:
        st.warning("Δεν υπάρχουν δεδομένα για το επιλεγμένο έτος.")
        st.stop()

    # ---------------------------------------------------------
    # Σύνοψη Τμημάτων / Σχολών / Πόλεων
    # ---------------------------------------------------------

    department_summary = build_department_summary(df_year)

    school_summary = build_group_summary(
        department_summary,
        "school"
    )

    city_summary = build_group_summary(
        department_summary,
        "city"
    )

    # ---------------------------------------------------------
    # Κεντρικά KPIs
    # ---------------------------------------------------------

    total_departments = department_summary["department_code"].nunique()
    total_schools = department_summary["school"].nunique()
    total_cities = department_summary["city"].nunique()

    total_positions = int(department_summary["total_positions"].sum())
    total_admitted = int(department_summary["total_admitted"].sum())
    total_empty_positions = int(department_summary["empty_positions"].sum())

    total_coverage = (
        total_admitted / total_positions * 100
        if total_positions > 0
        else 0
    )

    gel_day_available = department_summary["gel_day_base_score"].notna().sum()

    st.subheader(f"Συνολική διοικητική εικόνα {selected_year}")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.metric(
            "Τμήματα",
            total_departments
        )

    with kpi2:
        st.metric(
            "Σχολές",
            total_schools
        )

    with kpi3:
        st.metric(
            "Πόλεις",
            total_cities
        )

    with kpi4:
        st.metric(
            "Συνολικές Θέσεις",
            total_positions
        )

    kpi5, kpi6, kpi7, kpi8 = st.columns(4)

    with kpi5:
        st.metric(
            "Επιτυχόντες",
            total_admitted
        )

    with kpi6:
        st.metric(
            "Κενές Θέσεις",
            total_empty_positions
        )

    with kpi7:
        st.metric(
            "Συνολική Κάλυψη",
            f"{total_coverage:.1f}%"
        )

    with kpi8:
        st.metric(
            "Τμήματα με Βάση ΓΕΛ Ημ.",
            gel_day_available
        )

    st.caption(
        "Η ανάλυση περιλαμβάνει όλες τις κατηγορίες εισαγωγής. "
        "Οι Συνολικές Θέσεις είναι οι αρχικές θέσεις. "
        "Η Βάση ΓΕΛ Ημερήσια εμφανίζεται μόνο σε επίπεδο Τμήματος."
    )

    st.divider()

    # ---------------------------------------------------------
    # Συνοπτικά γραφήματα διοίκησης
    # ---------------------------------------------------------

    st.subheader("Συνοπτικά γραφήματα")

    school_display = format_group_table(
        school_summary.sort_values("total_admitted", ascending=False),
        "school",
        "Σχολή"
    )

    city_display = format_group_table(
        city_summary.sort_values("total_admitted", ascending=False),
        "city",
        "Πόλη"
    )

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        fig_school_positions = px.bar(
            school_display.sort_values("Συνολικές Θέσεις", ascending=False),
            x="Σχολή",
            y=["Συνολικές Θέσεις", "Επιτυχόντες"],
            barmode="group",
            title="Συνολικές θέσεις και επιτυχόντες ανά Σχολή"
        )

        fig_school_positions.update_layout(
            xaxis_title="Σχολή",
            yaxis_title="Πλήθος",
            legend_title=""
        )

        st.plotly_chart(
            fig_school_positions,
            use_container_width=True
        )

    with chart_col2:
        fig_school_coverage = px.bar(
            school_display.sort_values("Κάλυψη %", ascending=False),
            x="Σχολή",
            y="Κάλυψη %",
            text="Κάλυψη %",
            title="Κάλυψη ανά Σχολή"
        )

        fig_school_coverage.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside"
        )

        fig_school_coverage.update_layout(
            xaxis_title="Σχολή",
            yaxis_title="Κάλυψη %",
            yaxis_range=[0, 110]
        )

        st.plotly_chart(
            fig_school_coverage,
            use_container_width=True
        )

    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        fig_city_positions = px.bar(
            city_display.sort_values("Συνολικές Θέσεις", ascending=False),
            x="Πόλη",
            y=["Συνολικές Θέσεις", "Επιτυχόντες"],
            barmode="group",
            title="Συνολικές θέσεις και επιτυχόντες ανά Πόλη"
        )

        fig_city_positions.update_layout(
            xaxis_title="Πόλη",
            yaxis_title="Πλήθος",
            legend_title=""
        )

        st.plotly_chart(
            fig_city_positions,
            use_container_width=True
        )

    with chart_col4:
        fig_city_coverage = px.bar(
            city_display.sort_values("Κάλυψη %", ascending=False),
            x="Πόλη",
            y="Κάλυψη %",
            text="Κάλυψη %",
            title="Κάλυψη ανά Πόλη"
        )

        fig_city_coverage.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside"
        )

        fig_city_coverage.update_layout(
            xaxis_title="Πόλη",
            yaxis_title="Κάλυψη %",
            yaxis_range=[0, 110]
        )

        st.plotly_chart(
            fig_city_coverage,
            use_container_width=True
        )

    st.divider()

    # ---------------------------------------------------------
    # Γρήγορες επισημάνσεις
    # ---------------------------------------------------------

    st.subheader("Γρήγορες επισημάνσεις Τμημάτων")

    alert_col1, alert_col2 = st.columns(2)

    with alert_col1:
        st.markdown("### Υψηλότερες βάσεις ΓΕΛ Ημερήσια")

        top_base = (
            department_summary
            .dropna(subset=["gel_day_base_score"])
            .sort_values("gel_day_base_score", ascending=False)
            .head(5)
        )

        top_base_display = format_department_table(top_base)[
            [
                "Τμήμα",
                "Σχολή",
                "Πόλη",
                "Βάση ΓΕΛ Ημ.",
                "Πρώτος ΓΕΛ Ημ.",
            ]
        ]

        st.dataframe(
            top_base_display,
            use_container_width=True,
            hide_index=True
        )

    with alert_col2:
        st.markdown("### Περισσότερες κενές θέσεις")

        top_empty = (
            department_summary
            .sort_values("empty_positions", ascending=False)
            .head(5)
        )

        top_empty_display = format_department_table(top_empty)[
            [
                "Τμήμα",
                "Σχολή",
                "Πόλη",
                "Συνολικές Θέσεις",
                "Επιτυχόντες",
                "Κενές Θέσεις",
                "Κάλυψη %",
            ]
        ]

        st.dataframe(
            style_table(top_empty_display),
            use_container_width=True,
            hide_index=True
        )

    alert_col3, alert_col4 = st.columns(2)

    with alert_col3:
        st.markdown("### Χαμηλότερη κάλυψη")

        low_coverage = (
            department_summary
            .sort_values("coverage", ascending=True)
            .head(5)
        )

        low_coverage_display = format_department_table(low_coverage)[
            [
                "Τμήμα",
                "Σχολή",
                "Πόλη",
                "Συνολικές Θέσεις",
                "Επιτυχόντες",
                "Κενές Θέσεις",
                "Κάλυψη %",
            ]
        ]

        st.dataframe(
            style_table(low_coverage_display),
            use_container_width=True,
            hide_index=True
        )

    with alert_col4:
        st.markdown("### Περισσότεροι επιτυχόντες")

        top_admitted = (
            department_summary
            .sort_values("total_admitted", ascending=False)
            .head(5)
        )

        top_admitted_display = format_department_table(top_admitted)[
            [
                "Τμήμα",
                "Σχολή",
                "Πόλη",
                "Συνολικές Θέσεις",
                "Επιτυχόντες",
                "Κάλυψη %",
            ]
        ]

        st.dataframe(
            style_table(top_admitted_display),
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    # ---------------------------------------------------------
    # Αναλυτικοί πίνακες
    # ---------------------------------------------------------

    st.subheader("Αναλυτικοί πίνακες")

    tab_dept, tab_school, tab_city = st.tabs(
        [
            "Ανά Τμήμα",
            "Ανά Σχολή",
            "Ανά Πόλη",
        ]
    )

    with tab_dept:
        department_display = format_department_table(
            department_summary.sort_values(
                "coverage",
                ascending=False
            )
        )

        st.dataframe(
            style_table(department_display),
            use_container_width=True,
            hide_index=True
        )

    with tab_school:
        school_display = format_group_table(
            school_summary.sort_values(
                "coverage",
                ascending=False
            ),
            "school",
            "Σχολή"
        )

        st.dataframe(
            style_table(school_display),
            use_container_width=True,
            hide_index=True
        )

    with tab_city:
        city_display = format_group_table(
            city_summary.sort_values(
                "coverage",
                ascending=False
            ),
            "city",
            "Πόλη"
        )

        st.dataframe(
            style_table(city_display),
            use_container_width=True,
            hide_index=True
        )

except Exception as e:
    st.error("Υπήρξε πρόβλημα κατά την παραγωγή του Dashboard Διοίκησης.")
    st.exception(e)