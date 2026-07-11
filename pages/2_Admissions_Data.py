import streamlit as st
import plotly.express as px
from modules.database_manager import load_admissions_with_departments


st.set_page_config(
    page_title="Δεδομένα Εισακτέων | ΔΙΠΑΕ",
    page_icon="📋",
    layout="wide"
)


st.title("📋 Δεδομένα Εισακτέων ΔΙ.ΠΑ.Ε.")

st.markdown("""
Σε αυτή τη σελίδα προβάλλονται τα δεδομένα εισακτέων του ΔΙ.ΠΑ.Ε. ανά έτος,
Τμήμα και κατηγορία εισαγωγής.

**Μεθοδολογικοί κανόνες της εφαρμογής:**

- Η ανάλυση γίνεται πάντα για **όλες τις κατηγορίες**.
- Οι **Συνολικές Θέσεις** υπολογίζονται από τις **Αρχικές Θέσεις**.
- Η **Συνολική Κάλυψη** υπολογίζεται ως: Επιτυχόντες / Συνολικές Θέσεις.
- Η **Βάση Τμήματος** είναι η **Βάση ΓΕΛ Ημερήσια**.
- Ο **Πρώτος Τμήματος** είναι ο **Πρώτος ΓΕΛ Ημερήσια**.
- Δεν εμφανίζεται άθροισμα τελικών θέσεων ή φαινόμενη μεταβολή θέσεων.
""")

st.divider()


def get_gel_day_scores(df_year):
    """
    Επιστρέφει Βάση Τελευταίου και Βαθμό Πρώτου από τη ΓΕΛ Ημερήσια ανά Τμήμα.
    Αυτές οι τιμές χρησιμοποιούνται ως βασικοί δείκτες βάσης/ζήτησης.
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
    Δημιουργεί σύνοψη ανά Τμήμα.

    Η ανάλυση γίνεται πάντα για όλες τις κατηγορίες.
    Οι συνολικές θέσεις είναι το άθροισμα των αρχικών θέσεων.
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


def format_department_summary(df):
    """
    Μορφοποιεί τη σύνοψη ανά Τμήμα για εμφάνιση.
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


def format_raw_table(df):
    """
    Μορφοποιεί τον αναλυτικό πίνακα εγγραφών ανά κατηγορία.

    Εδώ εμφανίζουμε τις αρχικές θέσεις, τους επιτυχόντες και τις βάσεις ανά κατηγορία,
    χωρίς να εμφανίζουμε τελικές θέσεις ή φαινόμενες μεταβολές.
    """

    display = df[
        [
            "year",
            "exam_category",
            "department_name_clean",
            "school",
            "city",
            "admission_type",
            "scientific_fields",
            "initial_positions",
            "admitted",
            "first_score",
            "base_score",
            "source_file",
        ]
    ].copy()

    display = display.rename(
        columns={
            "year": "Έτος",
            "exam_category": "Κατηγορία",
            "department_name_clean": "Τμήμα",
            "school": "Σχολή",
            "city": "Πόλη",
            "admission_type": "Είδος Θέσης",
            "scientific_fields": "Επιστημονικά Πεδία",
            "initial_positions": "Αρχικές Θέσεις",
            "admitted": "Επιτυχόντες",
            "first_score": "Βαθμός Πρώτου",
            "base_score": "Βάση Τελευταίου",
            "source_file": "Αρχείο Πηγής",
        }
    )

    for col in [
        "Βαθμός Πρώτου",
        "Βάση Τελευταίου",
    ]:
        display[col] = display[col].round(2)

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


def highlight_gel_day_row(row):
    """
    Επισημαίνει τη ΓΕΛ Ημερήσια στον αναλυτικό πίνακα.
    """

    category = str(row.get("Κατηγορία", ""))

    if category == "ΓΕΛ Ημερήσια":
        return [
            "background-color: #fff3cd; color: #664d03; font-weight: bold;"
            for _ in row
        ]

    return ["" for _ in row]


def style_summary_table(df):
    """
    Styling σύνοψης ανά Τμήμα.
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

    return style_obj


def style_raw_table(df):
    """
    Styling αναλυτικού πίνακα κατηγοριών.
    """

    return df.style.apply(
        highlight_gel_day_row,
        axis=1
    )


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
    # Σύνοψη ανά Τμήμα
    # ---------------------------------------------------------

    department_summary = build_department_summary(df_year)

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

    st.subheader(f"Συνολική εικόνα εισακτέων {selected_year}")

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
        "Η Βάση Τμήματος είναι η Βάση ΓΕΛ Ημερήσια."
    )

    st.divider()

    # ---------------------------------------------------------
    # Γραφήματα συνολικής εικόνας
    # ---------------------------------------------------------

    st.subheader("Γραφήματα ανά Τμήμα")

    summary_display = format_department_summary(department_summary)

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        fig_positions = px.bar(
            summary_display.sort_values("Συνολικές Θέσεις", ascending=False),
            x="Τμήμα",
            y=["Συνολικές Θέσεις", "Επιτυχόντες"],
            barmode="group",
            title="Συνολικές θέσεις και επιτυχόντες ανά Τμήμα"
        )

        fig_positions.update_layout(
            xaxis_title="Τμήμα",
            yaxis_title="Πλήθος",
            legend_title=""
        )

        st.plotly_chart(
            fig_positions,
            use_container_width=True
        )

    with chart_col2:
        fig_coverage = px.bar(
            summary_display.sort_values("Κάλυψη %", ascending=False),
            x="Τμήμα",
            y="Κάλυψη %",
            text="Κάλυψη %",
            title="Συνολική κάλυψη ανά Τμήμα"
        )

        fig_coverage.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside"
        )

        fig_coverage.update_layout(
            xaxis_title="Τμήμα",
            yaxis_title="Κάλυψη %",
            yaxis_range=[0, 110]
        )

        st.plotly_chart(
            fig_coverage,
            use_container_width=True
        )

    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        fig_base = px.bar(
            summary_display.dropna(subset=["Βάση ΓΕΛ Ημ."]).sort_values(
                "Βάση ΓΕΛ Ημ.",
                ascending=False
            ),
            x="Τμήμα",
            y="Βάση ΓΕΛ Ημ.",
            text="Βάση ΓΕΛ Ημ.",
            title="Βάση ΓΕΛ Ημερήσια ανά Τμήμα"
        )

        fig_base.update_traces(
            texttemplate="%{text:.0f}",
            textposition="outside"
        )

        fig_base.update_layout(
            xaxis_title="Τμήμα",
            yaxis_title="Βάση ΓΕΛ Ημερήσια"
        )

        st.plotly_chart(
            fig_base,
            use_container_width=True
        )

    with chart_col4:
        fig_empty = px.bar(
            summary_display.sort_values("Κενές Θέσεις", ascending=False),
            x="Τμήμα",
            y="Κενές Θέσεις",
            text="Κενές Θέσεις",
            title="Κενές θέσεις ανά Τμήμα"
        )

        fig_empty.update_traces(
            textposition="outside"
        )

        fig_empty.update_layout(
            xaxis_title="Τμήμα",
            yaxis_title="Κενές Θέσεις"
        )

        st.plotly_chart(
            fig_empty,
            use_container_width=True
        )

    st.divider()

    # ---------------------------------------------------------
    # Πίνακες
    # ---------------------------------------------------------

    st.subheader("Πίνακες δεδομένων")

    tab_summary, tab_raw = st.tabs(
        [
            "Σύνοψη ανά Τμήμα",
            "Αναλυτικές εγγραφές ανά κατηγορία",
        ]
    )

    with tab_summary:
        summary_display = summary_display.sort_values(
            "Βάση ΓΕΛ Ημ.",
            ascending=False,
            na_position="last"
        )

        st.dataframe(
            style_summary_table(summary_display),
            use_container_width=True,
            hide_index=True
        )

    with tab_raw:
        raw_display = format_raw_table(
            df_year.sort_values(
                [
                    "department_name_clean",
                    "exam_category",
                ]
            )
        )

        st.dataframe(
            style_raw_table(raw_display),
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "Στον αναλυτικό πίνακα η ΓΕΛ Ημερήσια επισημαίνεται με κίτρινο, "
            "επειδή αποτελεί τη βασική κατηγορία αναφοράς για τη βάση κάθε Τμήματος."
        )

except Exception as e:
    st.error("Υπήρξε πρόβλημα κατά την προβολή των δεδομένων εισακτέων.")
    st.exception(e)