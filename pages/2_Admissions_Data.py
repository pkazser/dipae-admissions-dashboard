import streamlit as st
import plotly.express as px
from modules.database_manager import load_admissions_with_departments
from components.sidebar_branding import show_sidebar_branding


st.set_page_config(
    page_title="Δεδομένα Εισακτέων | ΔΙΠΑΕ",
    page_icon="📋",
    layout="wide"
)

show_sidebar_branding()


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


# ---------------------------------------------------------
# Βοηθητικές συναρτήσεις δεδομένων
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Μορφοποίηση πινάκων
# ---------------------------------------------------------

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
            "coverage": "Συνολική Κάλυψη %",
            "gel_day_base_score": "Βάση ΓΕΛ Ημ.",
        }
    )

    display["Συνολική Κάλυψη %"] = (
        display["Συνολική Κάλυψη %"]
        .round(2)
    )

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
            "coverage": "Συνολική Κάλυψη %",
            "gel_day_first_score": "Πρώτος ΓΕΛ Ημ.",
            "gel_day_base_score": "Βάση ΓΕΛ Ημ.",
        }
    )

    display["Συνολική Κάλυψη %"] = (
        display["Συνολική Κάλυψη %"]
        .round(2)
    )

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


# ---------------------------------------------------------
# Styling πινάκων
# ---------------------------------------------------------

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

    Όλες οι στήλες κάλυψης εμφανίζονται πάντα με 2 δεκαδικά και σύμβολο %.
    """

    style_obj = df.style

    format_dict = {}

    for col in df.columns:
        if "Κάλυψη" in col and "%" in col:
            format_dict[col] = "{:.2f}%"

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

    coverage_columns = [
        col for col in df.columns
        if "Κάλυψη" in col and "%" in col
    ]

    if coverage_columns:
        try:
            style_obj = style_obj.map(
                highlight_coverage,
                subset=coverage_columns
            )
        except AttributeError:
            style_obj = style_obj.applymap(
                highlight_coverage,
                subset=coverage_columns
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


# ---------------------------------------------------------
# Γραφήματα
# ---------------------------------------------------------

def apply_large_chart_layout(fig, title, xaxis_title, yaxis_title):
    """
    Κοινή μορφοποίηση για μεγάλα οριζόντια γραφήματα.
    Δίνει περισσότερο χώρο δεξιά ώστε να μη κόβονται οι αριθμητικές τιμές.
    """

    fig.update_layout(
        title=title,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        height=800,
        margin=dict(l=20, r=220, t=80, b=40),
        uniformtext_minsize=7,
        uniformtext_mode="show"
    )

    fig.update_yaxes(
        automargin=True
    )

    fig.update_xaxes(
        automargin=True
    )

    return fig


def create_positions_chart(summary_display):
    """
    Οριζόντιο γράφημα συνολικών θέσεων και επιτυχόντων ανά πρόγραμμα.

    Χρησιμοποιούμε long μορφή δεδομένων για καλύτερο έλεγχο των labels.
    """

    chart_df = summary_display[
        [
            "Προπτυχιακό Πρόγραμμα",
            "Συνολικές Θέσεις",
            "Επιτυχόντες",
        ]
    ].copy()

    chart_df = chart_df.sort_values(
        "Συνολικές Θέσεις",
        ascending=True
    )

    chart_long = chart_df.melt(
        id_vars="Προπτυχιακό Πρόγραμμα",
        value_vars=[
            "Συνολικές Θέσεις",
            "Επιτυχόντες",
        ],
        var_name="Δείκτης",
        value_name="Πλήθος"
    )

    max_value = (
        chart_long["Πλήθος"].max()
        if not chart_long.empty
        else 0
    )

    fig = px.bar(
        chart_long,
        x="Πλήθος",
        y="Προπτυχιακό Πρόγραμμα",
        color="Δείκτης",
        orientation="h",
        barmode="group",
        text="Πλήθος",
        title="Συνολικές θέσεις και επιτυχόντες ανά πρόγραμμα"
    )

    fig.update_traces(
        texttemplate="%{text:.0f}",
        textposition="outside",
        textfont_size=10,
        cliponaxis=False
    )

    fig.update_layout(
        xaxis_range=[
            0,
            max_value * 1.25 if max_value > 0 else 10
        ],
        legend_title=""
    )

    fig = apply_large_chart_layout(
        fig=fig,
        title="Συνολικές θέσεις και επιτυχόντες ανά πρόγραμμα",
        xaxis_title="Πλήθος",
        yaxis_title=""
    )

    return fig


def create_coverage_chart(summary_display):
    """
    Οριζόντιο γράφημα συνολικής κάλυψης ανά πρόγραμμα.
    """

    chart_df = summary_display.sort_values(
        "Συνολική Κάλυψη %",
        ascending=True
    ).copy()

    fig = px.bar(
        chart_df,
        x="Συνολική Κάλυψη %",
        y="Προπτυχιακό Πρόγραμμα",
        orientation="h",
        text="Συνολική Κάλυψη %",
        title="Συνολική κάλυψη ανά πρόγραμμα"
    )

    fig.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",
        textfont_size=10,
        cliponaxis=False
    )

    fig.update_layout(
        xaxis_range=[0, 115]
    )

    fig = apply_large_chart_layout(
        fig=fig,
        title="Συνολική κάλυψη ανά πρόγραμμα",
        xaxis_title="Συνολική Κάλυψη %",
        yaxis_title=""
    )

    return fig


def create_base_chart(summary_display):
    """
    Οριζόντιο γράφημα βάσης ΓΕΛ Ημερήσια ανά πρόγραμμα.
    """

    chart_df = (
        summary_display[
            summary_display["Βάση ΓΕΛ Ημ."] > 0
        ]
        .sort_values(
            "Βάση ΓΕΛ Ημ.",
            ascending=True
        )
        .copy()
    )

    max_value = (
        chart_df["Βάση ΓΕΛ Ημ."].max()
        if not chart_df.empty
        else 0
    )

    fig = px.bar(
        chart_df,
        x="Βάση ΓΕΛ Ημ.",
        y="Προπτυχιακό Πρόγραμμα",
        orientation="h",
        text="Βάση ΓΕΛ Ημ.",
        title="Βάση ΓΕΛ Ημερήσια ανά πρόγραμμα"
    )

    fig.update_traces(
        texttemplate="%{text:.0f}",
        textposition="outside",
        textfont_size=10,
        cliponaxis=False
    )

    fig.update_layout(
        xaxis_range=[
            0,
            max(20000, max_value * 1.18)
        ]
    )

    fig = apply_large_chart_layout(
        fig=fig,
        title="Βάση ΓΕΛ Ημερήσια ανά πρόγραμμα",
        xaxis_title="Βάση ΓΕΛ Ημερήσια",
        yaxis_title=""
    )

    return fig


def create_empty_chart(summary_display):
    """
    Οριζόντιο γράφημα κενών θέσεων ανά πρόγραμμα.
    """

    chart_df = summary_display.sort_values(
        "Κενές Θέσεις",
        ascending=True
    ).copy()

    max_empty = (
        chart_df["Κενές Θέσεις"].max()
        if not chart_df.empty
        else 0
    )

    fig = px.bar(
        chart_df,
        x="Κενές Θέσεις",
        y="Προπτυχιακό Πρόγραμμα",
        orientation="h",
        text="Κενές Θέσεις",
        title="Κενές θέσεις ανά πρόγραμμα"
    )

    fig.update_traces(
        texttemplate="%{text:.0f}",
        textposition="outside",
        textfont_size=10,
        cliponaxis=False
    )

    fig.update_layout(
        xaxis_range=[
            0,
            max(5, max_empty * 1.25)
        ],
        xaxis=dict(dtick=1)
    )

    fig = apply_large_chart_layout(
        fig=fig,
        title="Κενές θέσεις ανά πρόγραμμα",
        xaxis_title="Κενές Θέσεις",
        yaxis_title=""
    )

    return fig
# ---------------------------------------------------------
# Κύρια ροή
# ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Ενότητα διαγραμμάτων με dropdown
    # ---------------------------------------------------------

    st.subheader("Βασικά διαγράμματα")

    summary_display = format_detailed_summary_table(department_summary)

    chart_choice = st.selectbox(
        "Επιλέξτε διάγραμμα",
        [
            "Συνολικές θέσεις και επιτυχόντες",
            "Συνολική κάλυψη",
            "Βάση ΓΕΛ Ημερήσια",
            "Κενές θέσεις",
        ]
    )

    if chart_choice == "Συνολικές θέσεις και επιτυχόντες":
        fig = create_positions_chart(summary_display)

    elif chart_choice == "Συνολική κάλυψη":
        fig = create_coverage_chart(summary_display)

    elif chart_choice == "Βάση ΓΕΛ Ημερήσια":
        fig = create_base_chart(summary_display)

    else:
        fig = create_empty_chart(summary_display)

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.caption(
        "Τα διαγράμματα εμφανίζονται ένα κάθε φορά για καλύτερη αναγνωσιμότητα. "
        "Η οριζόντια διάταξη βοηθά στην καθαρή εμφάνιση των ονομάτων των προγραμμάτων."
    )

    st.divider()

    # ---------------------------------------------------------
    # Πίνακες δεδομένων
    # ---------------------------------------------------------

    st.subheader("Πίνακες δεδομένων")

    tab_summary, tab_detailed, tab_raw = st.tabs(
        [
            "Συνοπτικός πίνακας",
            "Αναλυτική σύνοψη",
            "Εγγραφές ανά κατηγορία",
        ]
    )

    coverage_note = (
        "Η «Συνολική Κάλυψη %» υπολογίζεται επί των συνολικών θέσεων όλων "
        "των κατηγοριών εισαγωγής και όχι μόνο επί των θέσεων της ΓΕΛ Ημερήσιας."
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

        st.caption(coverage_note)

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

        st.caption(coverage_note)

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