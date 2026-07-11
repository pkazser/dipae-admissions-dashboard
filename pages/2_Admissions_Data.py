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
Σε αυτή τη σελίδα προβάλλονται τα δεδομένα εισακτέων των ενεργών προπτυχιακών
προγραμμάτων σπουδών του ΔΙ.ΠΑ.Ε. ανά έτος.

**Μεθοδολογικοί κανόνες της εφαρμογής:**

- Η ανάλυση γίνεται πάντα για **όλες τις κατηγορίες εισαγωγής**.
- Οι **Συνολικές Θέσεις** υπολογίζονται από τις **Αρχικές Θέσεις**.
- Η **Συνολική Κάλυψη** υπολογίζεται ως: Επιτυχόντες / Συνολικές Θέσεις.
- Η **Βάση Προγράμματος** είναι η **Βάση ΓΕΛ Ημερήσια**.
- Ο **Πρώτος Προγράμματος** είναι ο **Πρώτος ΓΕΛ Ημερήσια**.
- Δεν εμφανίζονται τελικές θέσεις ή φαινόμενη μεταβολή θέσεων.
""")

st.divider()


def get_gel_day_scores(df_year):
    """
    Επιστρέφει τη βάση και τον βαθμό πρώτου της ΓΕΛ Ημερήσια ανά πρόγραμμα.
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
    Δημιουργεί σύνοψη ανά ενεργό προπτυχιακό πρόγραμμα.

    Η ανάλυση γίνεται για όλες τις κατηγορίες.
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


def format_summary_table(df):
    """
    Συνοπτικός πίνακας ανά πρόγραμμα.

    Δεν εμφανίζουμε Πρώτο ΓΕΛ Ημ. και Κενές Θέσεις εδώ,
    ώστε ο πίνακας να είναι καθαρός και να φαίνεται εύκολα η βάση.
    """

    display = df[
        [
            "department_name_clean",
            "school",
            "city",
            "total_positions",
            "total_admitted",
            "coverage",
            "gel_day_base_score",
        ]
    ].copy()

    display = display.rename(
        columns={
            "department_name_clean": "Προπτυχιακό Πρόγραμμα",
            "school": "Σχολή",
            "city": "Πόλη",
            "total_positions": "Συνολικές Θέσεις",
            "total_admitted": "Επιτυχόντες",
            "coverage": "Κάλυψη %",
            "gel_day_base_score": "Βάση ΓΕΛ Ημ.",
        }
    )

    display["Κάλυψη %"] = display["Κάλυψη %"].round(2)

    display["Βάση ΓΕΛ Ημ."] = (
        display["Βάση ΓΕΛ Ημ."]
        .fillna(0)
        .round(0)
        .astype(int)
    )

    return display


def format_detailed_summary_table(df):
    """
    Αναλυτικότερη σύνοψη ανά πρόγραμμα.
    Περιλαμβάνει και κενές θέσεις / πρώτο ΓΕΛ Ημ. για περισσότερη πληροφορία.
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
            "department_name_clean": "Προπτυχιακό Πρόγραμμα",
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

    display["Κάλυψη %"] = display["Κάλυψη %"].round(2)

    for col in [
        "Πρώτος ΓΕΛ Ημ.",
        "Βάση ΓΕΛ Ημ.",
    ]:
        display[col] = (
            display[col]
            .fillna(0)
            .round(0)
            .astype(int)
        )

    return display


def format_raw_table(df):
    """
    Μορφοποιεί τον αναλυτικό πίνακα εγγραφών ανά κατηγορία.

    Εδώ εμφανίζονται οι αρχικές θέσεις, οι επιτυχόντες και οι βάσεις ανά κατηγορία,
    χωρίς τελικές θέσεις ή φαινόμενες μεταβολές.
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
            "department_name_clean": "Προπτυχιακό Πρόγραμμα",
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
        display[col] = (
            display[col]
            .fillna(0)
            .round(0)
            .astype(int)
        )

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
    Styling σύνοψης προγραμμάτων.

    Τα ποσοστά κάλυψης εμφανίζονται πάντα με 2 δεκαδικά και σύμβολο %.
    """

    style_obj = df.style

    format_dict = {}

    if "Κάλυψη %" in df.columns:
        format_dict["Κάλυψη %"] = "{:.2f}%"

    if format_dict:
        style_obj = style_obj.format(format_dict)

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

    department_summary = build_department_summary(df_year)

    total_programs = int(department_summary["department_code"].nunique())
    total_schools = int(department_summary["school"].nunique())
    total_cities = int(department_summary["city"].nunique())

    total_positions = int(department_summary["total_positions"].sum())
    total_admitted = int(department_summary["total_admitted"].sum())
    total_empty_positions = int(department_summary["empty_positions"].sum())

    total_coverage = (
        total_admitted / total_positions * 100
        if total_positions > 0
        else 0
    )

    gel_day_available = int(
        department_summary["gel_day_base_score"].notna().sum()
    )

    st.subheader(f"Συνολική εικόνα εισακτέων {selected_year}")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.metric(
            "Ενεργά Προπτυχιακά Προγράμματα",
            total_programs
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
            f"{total_coverage:.2f}%"
        )

    with kpi8:
        st.metric(
            "Προγράμματα με Βάση ΓΕΛ Ημ.",
            gel_day_available
        )

    st.caption(
        "Η ανάλυση περιλαμβάνει όλες τις κατηγορίες εισαγωγής. "
        "Οι Συνολικές Θέσεις είναι οι αρχικές θέσεις. "
        "Η Βάση Προγράμματος είναι η Βάση ΓΕΛ Ημερήσια."
    )

    st.divider()

    st.subheader("Γραφήματα ανά πρόγραμμα")

    summary_display = format_detailed_summary_table(department_summary)

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        fig_positions = px.bar(
            summary_display.sort_values("Συνολικές Θέσεις", ascending=False),
            x="Προπτυχιακό Πρόγραμμα",
            y=["Συνολικές Θέσεις", "Επιτυχόντες"],
            barmode="group",
            title="Συνολικές θέσεις και επιτυχόντες ανά πρόγραμμα"
        )

        fig_positions.update_layout(
            xaxis_title="Προπτυχιακό Πρόγραμμα",
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
            x="Προπτυχιακό Πρόγραμμα",
            y="Κάλυψη %",
            text="Κάλυψη %",
            title="Συνολική κάλυψη ανά πρόγραμμα"
        )

        fig_coverage.update_traces(
            texttemplate="%{text:.2f}%",
            textposition="outside"
        )

        fig_coverage.update_layout(
            xaxis_title="Προπτυχιακό Πρόγραμμα",
            yaxis_title="Κάλυψη %",
            yaxis_range=[0, 100]
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
            x="Προπτυχιακό Πρόγραμμα",
            y="Βάση ΓΕΛ Ημ.",
            text="Βάση ΓΕΛ Ημ.",
            title="Βάση ΓΕΛ Ημερήσια ανά πρόγραμμα"
        )

        fig_base.update_traces(
            texttemplate="%{text:.0f}",
            textposition="outside"
        )

        fig_base.update_layout(
            xaxis_title="Προπτυχιακό Πρόγραμμα",
            yaxis_title="Βάση ΓΕΛ Ημερήσια",
            yaxis_range=[0, 20000]
        )

        st.plotly_chart(
            fig_base,
            use_container_width=True
        )

    with chart_col4:
        fig_empty = px.bar(
            summary_display.sort_values("Κενές Θέσεις", ascending=False),
            x="Προπτυχιακό Πρόγραμμα",
            y="Κενές Θέσεις",
            text="Κενές Θέσεις",
            title="Κενές θέσεις ανά πρόγραμμα"
        )

        fig_empty.update_traces(
            textposition="outside"
        )

        fig_empty.update_layout(
            xaxis_title="Προπτυχιακό Πρόγραμμα",
            yaxis_title="Κενές Θέσεις",
            yaxis=dict(dtick=1)
        )

        st.plotly_chart(
            fig_empty,
            use_container_width=True
        )

    st.divider()

    st.subheader("Πίνακες δεδομένων")

    tab_summary, tab_detailed, tab_raw = st.tabs(
        [
            "Συνοπτικός πίνακας",
            "Αναλυτική σύνοψη",
            "Εγγραφές ανά κατηγορία",
        ]
    )

    with tab_summary:
        clean_summary_display = format_summary_table(
            department_summary.sort_values(
                "gel_day_base_score",
                ascending=False,
                na_position="last"
            )
        )

        st.dataframe(
            style_summary_table(clean_summary_display),
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "Ο συνοπτικός πίνακας κρατά τις βασικές πληροφορίες ώστε οι βάσεις να εντοπίζονται εύκολα."
        )

    with tab_detailed:
        detailed_display = format_detailed_summary_table(
            department_summary.sort_values(
                "gel_day_base_score",
                ascending=False,
                na_position="last"
            )
        )

        st.dataframe(
            style_summary_table(detailed_display),
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
            "επειδή αποτελεί τη βασική κατηγορία αναφοράς για τη βάση κάθε προγράμματος."
        )

except Exception as e:
    st.error("Υπήρξε πρόβλημα κατά την προβολή των δεδομένων εισακτέων.")
    st.exception(e)