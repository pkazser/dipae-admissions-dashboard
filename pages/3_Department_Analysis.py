import streamlit as st
import plotly.express as px
from modules.database_manager import load_admissions_with_departments


st.set_page_config(
    page_title="Ανάλυση Τμήματος | ΔΙΠΑΕ",
    page_icon="🏛️",
    layout="wide"
)


st.title("🏛️ Ανάλυση Τμήματος ΔΙ.ΠΑ.Ε.")

st.markdown("""
Σε αυτή τη σελίδα εξετάζουμε αναλυτικά κάθε Τμήμα του ΔΙ.ΠΑ.Ε. για το επιλεγμένο έτος.

**Μεθοδολογικοί κανόνες της εφαρμογής:**

- Η ανάλυση γίνεται πάντα για **όλες τις κατηγορίες εισαγωγής**.
- Οι **Συνολικές Θέσεις Τμήματος** υπολογίζονται από τις **Αρχικές Θέσεις** όλων των κατηγοριών.
- Η **Συνολική Κάλυψη Τμήματος** υπολογίζεται ως: Επιτυχόντες / Συνολικές Θέσεις.
- Η **Βάση Τμήματος** είναι η **Βάση ΓΕΛ Ημερήσια**.
- Ο **Πρώτος Τμήματος** είναι ο **Πρώτος ΓΕΛ Ημερήσια**.
- Στη ΓΕΛ Ημερήσια χρησιμοποιούνται οι θέσεις μετά τις τυχόν μεταφορές από άλλες κατηγορίες.
- Δεν εμφανίζονται τελικές θέσεις ή φαινόμενη μεταβολή θέσεων ως ξεχωριστοί δείκτες.
""")

st.divider()


def safe_int(value, default=0):
    """
    Ασφαλής μετατροπή σε int.
    """

    try:
        if value is None:
            return default

        return int(value)
    except Exception:
        return default


def safe_float(value, default=None):
    """
    Ασφαλής μετατροπή σε float.
    """

    try:
        if value is None:
            return default

        return float(value)
    except Exception:
        return default


def get_gel_day_row(df_department):
    """
    Επιστρέφει τη γραμμή ΓΕΛ Ημερήσια για το επιλεγμένο Τμήμα.
    """

    df_gel = df_department[
        df_department["exam_category"] == "ΓΕΛ Ημερήσια"
    ].copy()

    if df_gel.empty:
        return None

    return df_gel.iloc[0]


def build_category_analysis_table(df_department):
    """
    Δημιουργεί πίνακα ανάλυσης ανά κατηγορία.

    Κρίσιμη διόρθωση:
    - Για τη ΓΕΛ Ημερήσια, οι θέσεις ανάλυσης λαμβάνονται από τις θέσεις μετά
      τις τυχόν μεταφορές από άλλες κατηγορίες.
    - Για τις υπόλοιπες κατηγορίες, χρησιμοποιούνται οι αρχικές θέσεις.

    Έτσι τα γραφήματα κάλυψης και κενών θέσεων δεν εμφανίζουν τεχνητά
    ποσοστά πάνω από 100% ή αρνητικές κενές θέσεις στη ΓΕΛ Ημερήσια.
    """

    df_display = df_department.copy()

    df_display["analysis_positions"] = df_display["initial_positions"]

    gel_mask = df_display["exam_category"] == "ΓΕΛ Ημερήσια"

    df_display.loc[gel_mask, "analysis_positions"] = (
        df_display.loc[gel_mask, "final_positions"]
        .fillna(df_display.loc[gel_mask, "initial_positions"])
    )

    df_display["empty_positions"] = (
        df_display["analysis_positions"]
        - df_display["admitted"]
    )

    df_display["category_coverage"] = (
        df_display["admitted"]
        / df_display["analysis_positions"]
        * 100
    )

    category_table = df_display[
        [
            "exam_category",
            "admission_type",
            "scientific_fields",
            "analysis_positions",
            "admitted",
            "empty_positions",
            "category_coverage",
            "first_score",
            "base_score",
        ]
    ].copy()

    category_table = category_table.rename(
        columns={
            "exam_category": "Κατηγορία",
            "admission_type": "Είδος Θέσης",
            "scientific_fields": "Επιστημονικά Πεδία",
            "analysis_positions": "Θέσεις",
            "admitted": "Επιτυχόντες",
            "empty_positions": "Κενές Θέσεις",
            "category_coverage": "Κάλυψη Κατηγορίας %",
            "first_score": "Βαθμός Πρώτου",
            "base_score": "Βάση Τελευταίου",
        }
    )

    for col in [
        "Θέσεις",
        "Επιτυχόντες",
        "Κενές Θέσεις",
    ]:
        category_table[col] = category_table[col].fillna(0).astype(int)

    for col in [
        "Κάλυψη Κατηγορίας %",
        "Βαθμός Πρώτου",
        "Βάση Τελευταίου",
    ]:
        category_table[col] = category_table[col].round(2)

    return category_table


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


def highlight_gel_day_row(row):
    """
    Επισημαίνει ολόκληρη τη γραμμή της ΓΕΛ Ημερήσια.
    """

    category = str(row.get("Κατηγορία", ""))

    if category == "ΓΕΛ Ημερήσια":
        return [
            "background-color: #fff3cd; color: #664d03; font-weight: bold;"
            for _ in row
        ]

    return ["" for _ in row]


def style_category_table(df):
    """
    Styling αναλυτικού πίνακα ανά κατηγορία.
    """

    try:
        return (
            df.style
            .apply(highlight_gel_day_row, axis=1)
            .map(highlight_empty_positions, subset=["Κενές Θέσεις"])
        )
    except AttributeError:
        return (
            df.style
            .apply(highlight_gel_day_row, axis=1)
            .applymap(highlight_empty_positions, subset=["Κενές Θέσεις"])
        )


def style_score_table(df):
    """
    Styling πίνακα βάσεων.
    """

    return df.style.apply(highlight_gel_day_row, axis=1)


try:
    df = load_admissions_with_departments()

    if df.empty:
        st.warning("Δεν υπάρχουν ακόμη δεδομένα εισακτέων στη βάση.")
        st.stop()

    # ---------------------------------------------------------
    # Φίλτρα
    # ---------------------------------------------------------

    years = sorted(df["year"].dropna().unique().tolist())

    col_year, col_department = st.columns(2)

    with col_year:
        selected_year = st.selectbox(
            "Έτος",
            years,
            index=len(years) - 1
        )

    df_year = df[df["year"] == selected_year].copy()

    departments = (
        df_year[
            [
                "department_code",
                "department_name_clean",
                "department_name_raw",
                "school",
                "city",
            ]
        ]
        .drop_duplicates()
        .sort_values("department_name_clean")
    )

    department_options = departments["department_name_clean"].dropna().tolist()

    with col_department:
        selected_department = st.selectbox(
            "Τμήμα",
            department_options
        )

    df_department = df_year[
        df_year["department_name_clean"] == selected_department
    ].copy()

    if df_department.empty:
        st.warning("Δεν υπάρχουν δεδομένα για το επιλεγμένο Τμήμα.")
        st.stop()

    # ---------------------------------------------------------
    # Βασικά στοιχεία Τμήματος
    # ---------------------------------------------------------

    department_info = df_department.iloc[0]

    department_code = department_info.get("department_code", "")
    ministry_department_code = department_info.get("ministry_department_code", "")
    school = department_info.get("school", "")
    city = department_info.get("city", "")
    website = department_info.get("website", "")

    st.subheader(selected_department)

    info_col1, info_col2, info_col3, info_col4 = st.columns(4)

    with info_col1:
        st.metric("Κωδικός ΔΙ.ΠΑ.Ε.", department_code)

    with info_col2:
        st.metric("Κωδικός Υπουργείου", ministry_department_code)

    with info_col3:
        st.metric("Σχολή", school)

    with info_col4:
        st.metric("Πόλη", city)

    if website and str(website).lower() not in ["nan", "none"]:
        st.markdown(f"🌐 Ιστοσελίδα Τμήματος: {website}")

    st.divider()

    # ---------------------------------------------------------
    # Βασικοί δείκτες Τμήματος
    # ---------------------------------------------------------

    total_positions = safe_int(df_department["initial_positions"].sum())
    total_admitted = safe_int(df_department["admitted"].sum())

    empty_positions = total_positions - total_admitted

    total_coverage = (
        total_admitted / total_positions * 100
        if total_positions > 0
        else 0
    )

    gel_day_row = get_gel_day_row(df_department)

    if gel_day_row is not None:
        gel_day_positions = safe_int(
            gel_day_row.get("final_positions"),
            default=safe_int(gel_day_row.get("initial_positions"))
        )

        gel_day_admitted = safe_int(
            gel_day_row.get("admitted")
        )

        gel_day_empty_positions = (
            gel_day_positions
            - gel_day_admitted
        )

        gel_day_coverage = (
            gel_day_admitted / gel_day_positions * 100
            if gel_day_positions > 0
            else None
        )

        gel_day_first_score = safe_float(
            gel_day_row.get("first_score")
        )

        gel_day_base_score = safe_float(
            gel_day_row.get("base_score")
        )
    else:
        gel_day_positions = 0
        gel_day_admitted = 0
        gel_day_empty_positions = 0
        gel_day_coverage = None
        gel_day_first_score = None
        gel_day_base_score = None

    st.subheader("Βασικοί δείκτες Τμήματος")

    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        st.metric(
            "Συνολικές Θέσεις",
            total_positions
        )

    with kpi_col2:
        st.metric(
            "Επιτυχόντες",
            total_admitted
        )

    with kpi_col3:
        st.metric(
            "Κενές Θέσεις",
            empty_positions
        )

    with kpi_col4:
        st.metric(
            "Συνολική Κάλυψη",
            f"{total_coverage:.1f}%"
        )

    kpi_col5, kpi_col6, kpi_col7, kpi_col8 = st.columns(4)

    with kpi_col5:
        st.metric(
            "ΓΕΛ Ημερήσια Θέσεις",
            gel_day_positions
        )

    with kpi_col6:
        st.metric(
            "ΓΕΛ Ημερήσια Επιτυχόντες",
            gel_day_admitted
        )

    with kpi_col7:
        if gel_day_coverage is not None:
            st.metric(
                "Κάλυψη ΓΕΛ Ημερήσια",
                f"{gel_day_coverage:.1f}%"
            )
        else:
            st.metric(
                "Κάλυψη ΓΕΛ Ημερήσια",
                "—"
            )

    with kpi_col8:
        if gel_day_base_score is not None:
            st.metric(
                "Βάση ΓΕΛ Ημερήσια",
                f"{gel_day_base_score:.0f}"
            )
        else:
            st.metric(
                "Βάση ΓΕΛ Ημερήσια",
                "—"
            )

    kpi_col9, kpi_col10 = st.columns(2)

    with kpi_col9:
        if gel_day_first_score is not None:
            st.metric(
                "Πρώτος ΓΕΛ Ημερήσια",
                f"{gel_day_first_score:.0f}"
            )
        else:
            st.metric(
                "Πρώτος ΓΕΛ Ημερήσια",
                "—"
            )

    with kpi_col10:
        st.metric(
            "Κενές ΓΕΛ Ημερήσια",
            gel_day_empty_positions
        )

    st.caption(
        "Η συνολική κάλυψη υπολογίζεται για όλες τις κατηγορίες εισαγωγής. "
        "Η Βάση και ο Πρώτος Τμήματος προέρχονται από τη ΓΕΛ Ημερήσια. "
        "Οι ΓΕΛ Ημερήσιες Θέσεις λαμβάνουν υπόψη τυχόν μεταφορές θέσεων προς τη ΓΕΛ Ημερήσια."
    )

    st.divider()

    # ---------------------------------------------------------
    # Πίνακας ανά κατηγορία
    # ---------------------------------------------------------

    st.subheader("Αναλυτικός πίνακας ανά κατηγορία εισαγωγής")

    category_table = build_category_analysis_table(df_department)

    st.dataframe(
        style_category_table(category_table),
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Η ΓΕΛ Ημερήσια επισημαίνεται με κίτρινο. "
        "Στη στήλη Θέσεις, για τη ΓΕΛ Ημερήσια λαμβάνονται υπόψη οι θέσεις μετά τις τυχόν μεταφορές."
    )

    st.divider()

    # ---------------------------------------------------------
    # Γραφήματα ανά κατηγορία
    # ---------------------------------------------------------

    st.subheader("Γραφήματα ανά κατηγορία")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        fig_positions = px.bar(
            category_table,
            x="Κατηγορία",
            y=["Θέσεις", "Επιτυχόντες"],
            barmode="group",
            title="Θέσεις και επιτυχόντες ανά κατηγορία"
        )

        fig_positions.update_layout(
            xaxis_title="Κατηγορία",
            yaxis_title="Πλήθος",
            legend_title=""
        )

        st.plotly_chart(
            fig_positions,
            use_container_width=True
        )

    with chart_col2:
        coverage_chart_df = category_table.copy()
        coverage_chart_df["Επισήμανση"] = coverage_chart_df["Κατηγορία"].apply(
            lambda x: "ΓΕΛ Ημερήσια" if x == "ΓΕΛ Ημερήσια" else "Λοιπές κατηγορίες"
        )

        fig_coverage = px.bar(
            coverage_chart_df,
            x="Κατηγορία",
            y="Κάλυψη Κατηγορίας %",
            text="Κάλυψη Κατηγορίας %",
            color="Επισήμανση",
            color_discrete_map={
                "ΓΕΛ Ημερήσια": "#f59f00",
                "Λοιπές κατηγορίες": "#1f77b4",
            },
            title="Κάλυψη ανά κατηγορία"
        )

        fig_coverage.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside"
        )

        fig_coverage.update_layout(
            xaxis_title="Κατηγορία",
            yaxis_title="Κάλυψη %",
            yaxis_range=[0, 120],
            legend_title=""
        )

        st.plotly_chart(
            fig_coverage,
            use_container_width=True
        )

    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        empty_chart_df = category_table.copy()
        empty_chart_df["Επισήμανση"] = empty_chart_df["Κατηγορία"].apply(
            lambda x: "ΓΕΛ Ημερήσια" if x == "ΓΕΛ Ημερήσια" else "Λοιπές κατηγορίες"
        )

        fig_empty = px.bar(
            empty_chart_df,
            x="Κατηγορία",
            y="Κενές Θέσεις",
            text="Κενές Θέσεις",
            color="Επισήμανση",
            color_discrete_map={
                "ΓΕΛ Ημερήσια": "#f59f00",
                "Λοιπές κατηγορίες": "#1f77b4",
            },
            title="Κενές θέσεις ανά κατηγορία"
        )

        fig_empty.update_traces(
            textposition="outside"
        )

        fig_empty.update_layout(
            xaxis_title="Κατηγορία",
            yaxis_title="Κενές Θέσεις",
            legend_title=""
        )

        st.plotly_chart(
            fig_empty,
            use_container_width=True
        )

    with chart_col4:
        score_chart_df = category_table.copy()
        score_chart_df["Επισήμανση"] = score_chart_df["Κατηγορία"].apply(
            lambda x: "ΓΕΛ Ημερήσια" if x == "ΓΕΛ Ημερήσια" else "Λοιπές κατηγορίες"
        )

        fig_base_score = px.bar(
            score_chart_df,
            x="Κατηγορία",
            y="Βάση Τελευταίου",
            text="Βάση Τελευταίου",
            color="Επισήμανση",
            color_discrete_map={
                "ΓΕΛ Ημερήσια": "#f59f00",
                "Λοιπές κατηγορίες": "#1f77b4",
            },
            title="Βάση τελευταίου ανά κατηγορία"
        )

        fig_base_score.update_traces(
            texttemplate="%{text:.0f}",
            textposition="outside"
        )

        fig_base_score.update_layout(
            xaxis_title="Κατηγορία",
            yaxis_title="Βάση Τελευταίου",
            legend_title=""
        )

        st.plotly_chart(
            fig_base_score,
            use_container_width=True
        )

    st.divider()

    # ---------------------------------------------------------
    # Πίνακας βάσεων
    # ---------------------------------------------------------

    st.subheader("Βάσεις εισαγωγής ανά κατηγορία")

    score_table = category_table[
        [
            "Κατηγορία",
            "Είδος Θέσης",
            "Βαθμός Πρώτου",
            "Βάση Τελευταίου",
        ]
    ].copy()

    st.dataframe(
        style_score_table(score_table),
        use_container_width=True,
        hide_index=True
    )

except Exception as e:
    st.error("Υπήρξε πρόβλημα κατά την ανάλυση Τμήματος.")
    st.exception(e)