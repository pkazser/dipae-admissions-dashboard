import pandas as pd
import streamlit as st
import plotly.express as px

from modules.database_manager import load_admissions_with_departments
from components.sidebar_branding import show_sidebar_branding


# ---------------------------------------------------------
# Ρυθμίσεις σελίδας
# ---------------------------------------------------------

st.set_page_config(
    page_title="Ανάλυση Προγράμματος | ΔΙΠΑΕ",
    page_icon="🏛️",
    layout="wide"
)

show_sidebar_branding()


st.title("🏛️ Ανάλυση Προπτυχιακού Προγράμματος")

st.markdown("""
Η σελίδα παρουσιάζει αναλυτικά τα στοιχεία εισακτέων για κάθε ενεργό
προπτυχιακό πρόγραμμα σπουδών του ΔΙ.ΠΑ.Ε.

**Μεθοδολογικοί κανόνες:**

- Η συνολική εικόνα του προγράμματος υπολογίζεται από **όλες τις κατηγορίες εισαγωγής**.
- Οι **Συνολικές Θέσεις** υπολογίζονται από τις **Αρχικές Θέσεις**.
- Η **Συνολική Κάλυψη** υπολογίζεται ως: Επιτυχόντες όλων των κατηγοριών / Συνολικές Θέσεις.
- Για τη **ΓΕΛ Ημερήσια** χρησιμοποιούνται οι θέσεις της συγκεκριμένης κατηγορίας.
- Η **Βάση Προγράμματος** είναι η **Βάση ΓΕΛ Ημερήσια**.
- Ο **Πρώτος Προγράμματος** είναι ο **Πρώτος ΓΕΛ Ημερήσια**.
- Οι κενές θέσεις των κατηγοριών **10% ΓΕΛ** εμφανίζονται πληροφοριακά ανά κατηγορία και δεν πρέπει να αθροίζονται ξανά με τις συνολικές κενές θέσεις.
""")

st.divider()


# ---------------------------------------------------------
# Βοηθητικές συναρτήσεις
# ---------------------------------------------------------

def safe_int(value):
    try:
        if pd.isna(value):
            return 0
        return int(round(float(value)))
    except Exception:
        return 0


def safe_float(value):
    try:
        if pd.isna(value):
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def safe_score(value):
    try:
        if pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def format_score(value):
    try:
        if value is None or pd.isna(value):
            return "-"
        return f"{float(value):.0f}"
    except Exception:
        return "-"


def is_gel_day_category(category):
    """
    Ελέγχει αν η κατηγορία είναι ΓΕΛ Ημερήσια.
    """

    category = str(category).strip()

    return category == "ΓΕΛ Ημερήσια"


def is_ten_percent_gel_category(category):
    """
    Ελέγχει αν η κατηγορία είναι 10% ΓΕΛ.

    Παραδείγματα:
    - 10% ΓΕΛ 2024
    - 10% ΓΕΛ 2025
    - 10% ΓΕΛ 2023
    """

    category = str(category).upper()

    return "10%" in category and "ΓΕΛ" in category


def get_category_note(category):
    """
    Επιστρέφει ερμηνευτική παρατήρηση για ειδικές κατηγορίες.
    """

    if is_ten_percent_gel_category(category):
        return (
            "Οι κενές θέσεις της κατηγορίας 10% ΓΕΛ μεταφέρονται / "
            "απορροφώνται στη ΓΕΛ Ημερήσια και δεν αθροίζονται ξανά."
        )

    if is_gel_day_category(category):
        return (
            "Βασική κατηγορία αναφοράς για θέσεις, βάση και πρώτο."
        )

    return ""


def get_gel_day_row(df_department):
    """
    Επιστρέφει τη γραμμή ΓΕΛ Ημερήσια για το επιλεγμένο πρόγραμμα.
    """

    df_gel = df_department[
        df_department["exam_category"] == "ΓΕΛ Ημερήσια"
    ].copy()

    if df_gel.empty:
        return None

    return df_gel.iloc[0]


def build_category_analysis_table(df_department):
    """
    Δημιουργεί πίνακα ανάλυσης ανά κατηγορία εισαγωγής.

    Για τη ΓΕΛ Ημερήσια χρησιμοποιούνται οι final_positions,
    επειδή σε αυτή την κατηγορία αποτυπώνονται οι θέσεις κατόπιν μεταφοράς.

    Για τις υπόλοιπες κατηγορίες χρησιμοποιούνται οι initial_positions.

    Οι κενές θέσεις των κατηγοριών 10% ΓΕΛ εμφανίζονται πληροφοριακά.
    Δεν πρέπει να αθροίζονται ξανά με τις συνολικές κενές θέσεις του προγράμματος.
    """

    df_display = df_department.copy()

    df_display["analysis_positions"] = (
        df_display["initial_positions"]
        .fillna(0)
    )

    gel_mask = df_display["exam_category"].apply(is_gel_day_category)

    df_display.loc[gel_mask, "analysis_positions"] = (
        df_display.loc[gel_mask, "final_positions"]
        .fillna(df_display.loc[gel_mask, "initial_positions"])
    )

    df_display["analysis_positions"] = (
        df_display["analysis_positions"]
        .fillna(0)
    )

    df_display["admitted"] = (
        df_display["admitted"]
        .fillna(0)
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

    df_display["category_coverage"] = (
        df_display["category_coverage"]
        .fillna(0)
    )

    df_display["category_note"] = df_display["exam_category"].apply(
        get_category_note
    )

    display = df_display[
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
            "category_note",
        ]
    ].copy()

    display = display.rename(
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
            "category_note": "Παρατήρηση",
        }
    )

    for col in [
        "Θέσεις",
        "Επιτυχόντες",
        "Κενές Θέσεις",
    ]:
        display[col] = (
            display[col]
            .fillna(0)
            .round(0)
            .astype(int)
        )

    display["Κάλυψη Κατηγορίας %"] = (
        display["Κάλυψη Κατηγορίας %"]
        .fillna(0)
        .round(2)
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


def build_category_chart_data(df_department):
    """
    Δεδομένα για γραφήματα κατηγοριών.
    """

    table = build_category_analysis_table(df_department)

    return table


# ---------------------------------------------------------
# Styling πινάκων
# ---------------------------------------------------------

def highlight_empty_positions(val):
    try:
        value = float(val)
    except Exception:
        return ""

    if value > 0:
        return "background-color: #f8d7da; color: #721c24; font-weight: bold;"
    else:
        return "background-color: #d4edda; color: #155724; font-weight: bold;"


def highlight_coverage(val):
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


def highlight_special_category_rows(row):
    """
    Χρωματίζει ειδικές γραμμές του πίνακα.

    ΓΕΛ Ημερήσια:
    - κίτρινο, επειδή είναι η βασική κατηγορία αναφοράς.

    10% ΓΕΛ:
    - γαλάζιο, επειδή οι κενές θέσεις εμφανίζονται πληροφοριακά
      και δεν πρέπει να αθροίζονται ξανά με τις συνολικές κενές.
    """

    category = str(row.get("Κατηγορία", ""))

    if is_gel_day_category(category):
        return [
            "background-color: #fff3cd; color: #664d03; font-weight: bold;"
            for _ in row
        ]

    if is_ten_percent_gel_category(category):
        return [
            "background-color: #dbeafe; color: #1e3a8a; font-weight: bold;"
            for _ in row
        ]

    return ["" for _ in row]


def style_category_table(df):
    """
    Styling πίνακα ανά κατηγορία.
    """

    style_obj = df.style.apply(
        highlight_special_category_rows,
        axis=1
    )

    if "Κάλυψη Κατηγορίας %" in df.columns:
        style_obj = style_obj.format(
            {
                "Κάλυψη Κατηγορίας %": "{:.2f}%"
            }
        )

        try:
            style_obj = style_obj.map(
                highlight_coverage,
                subset=["Κάλυψη Κατηγορίας %"]
            )
        except AttributeError:
            style_obj = style_obj.applymap(
                highlight_coverage,
                subset=["Κάλυψη Κατηγορίας %"]
            )

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


# ---------------------------------------------------------
# Γραφήματα
# ---------------------------------------------------------

def create_positions_by_category_chart(category_table):
    """
    Θέσεις και επιτυχόντες ανά κατηγορία.
    """

    chart_df = category_table[
        [
            "Κατηγορία",
            "Θέσεις",
            "Επιτυχόντες",
        ]
    ].copy()

    chart_long = chart_df.melt(
        id_vars="Κατηγορία",
        value_vars=[
            "Θέσεις",
            "Επιτυχόντες",
        ],
        var_name="Δείκτης",
        value_name="Πλήθος"
    )

    fig = px.bar(
        chart_long,
        x="Κατηγορία",
        y="Πλήθος",
        color="Δείκτης",
        barmode="group",
        text="Πλήθος",
        title="Θέσεις και επιτυχόντες ανά κατηγορία εισαγωγής"
    )

    fig.update_traces(
        texttemplate="%{text:.0f}",
        textposition="outside",
        cliponaxis=False
    )

    fig.update_layout(
        height=520,
        xaxis_title="Κατηγορία",
        yaxis_title="Πλήθος",
        legend_title="",
        margin=dict(l=20, r=60, t=80, b=120)
    )

    fig.update_xaxes(
        tickangle=-35
    )

    return fig


def create_empty_positions_chart(category_table):
    """
    Κενές θέσεις ανά κατηγορία.
    """

    chart_df = category_table.sort_values(
        "Κενές Θέσεις",
        ascending=False
    ).copy()

    fig = px.bar(
        chart_df,
        x="Κατηγορία",
        y="Κενές Θέσεις",
        text="Κενές Θέσεις",
        title="Κενές θέσεις ανά κατηγορία εισαγωγής"
    )

    fig.update_traces(
        texttemplate="%{text:.0f}",
        textposition="outside",
        cliponaxis=False
    )

    max_empty = (
        chart_df["Κενές Θέσεις"].max()
        if not chart_df.empty
        else 0
    )

    fig.update_layout(
        height=520,
        xaxis_title="Κατηγορία",
        yaxis_title="Κενές Θέσεις",
        yaxis_range=[0, max(5, max_empty * 1.25)],
        margin=dict(l=20, r=60, t=80, b=120)
    )

    fig.update_xaxes(
        tickangle=-35
    )

    return fig


def create_coverage_chart(category_table):
    """
    Κάλυψη ανά κατηγορία.
    """

    chart_df = category_table.sort_values(
        "Κάλυψη Κατηγορίας %",
        ascending=False
    ).copy()

    fig = px.bar(
        chart_df,
        x="Κατηγορία",
        y="Κάλυψη Κατηγορίας %",
        text="Κάλυψη Κατηγορίας %",
        title="Κάλυψη ανά κατηγορία εισαγωγής"
    )

    fig.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",
        cliponaxis=False
    )

    fig.update_layout(
        height=520,
        xaxis_title="Κατηγορία",
        yaxis_title="Κάλυψη %",
        yaxis_range=[0, 110],
        margin=dict(l=20, r=60, t=80, b=120)
    )

    fig.update_yaxes(
        tickformat=".0f"
    )

    fig.update_xaxes(
        tickangle=-35
    )

    return fig


def create_scores_chart(category_table):
    """
    Βαθμός πρώτου και βάση τελευταίου ανά κατηγορία.
    """

    chart_df = category_table[
        [
            "Κατηγορία",
            "Βαθμός Πρώτου",
            "Βάση Τελευταίου",
        ]
    ].copy()

    chart_long = chart_df.melt(
        id_vars="Κατηγορία",
        value_vars=[
            "Βαθμός Πρώτου",
            "Βάση Τελευταίου",
        ],
        var_name="Δείκτης",
        value_name="Μόρια"
    )

    fig = px.bar(
        chart_long,
        x="Κατηγορία",
        y="Μόρια",
        color="Δείκτης",
        barmode="group",
        text="Μόρια",
        title="Βαθμολογικά στοιχεία ανά κατηγορία εισαγωγής"
    )

    fig.update_traces(
        texttemplate="%{text:.0f}",
        textposition="outside",
        cliponaxis=False
    )

    fig.update_layout(
        height=520,
        xaxis_title="Κατηγορία",
        yaxis_title="Μόρια",
        yaxis_range=[0, 22000],
        legend_title="",
        margin=dict(l=20, r=60, t=80, b=120)
    )

    fig.update_xaxes(
        tickangle=-35
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

    departments = (
        df_year[
            [
                "department_code",
                "department_name_clean",
                "school",
                "city",
            ]
        ]
        .drop_duplicates()
        .sort_values("department_name_clean")
    )

    department_options = {
        f"{row['department_name_clean']} ({row['city']})": row["department_code"]
        for _, row in departments.iterrows()
    }

    selected_department_label = st.selectbox(
        "Επιλέξτε προπτυχιακό πρόγραμμα",
        list(department_options.keys())
    )

    selected_department_code = department_options[selected_department_label]

    df_department = df_year[
        df_year["department_code"] == selected_department_code
    ].copy()

    if df_department.empty:
        st.warning("Δεν υπάρχουν δεδομένα για το επιλεγμένο πρόγραμμα.")
        st.stop()

    department_name = (
        df_department["department_name_clean"]
        .dropna()
        .iloc[0]
    )

    school = (
        df_department["school"]
        .dropna()
        .iloc[0]
    )

    city = (
        df_department["city"]
        .dropna()
        .iloc[0]
    )

    st.subheader(department_name)

    st.markdown(
        f"""
**Σχολή:** {school}  
**Πόλη:** {city}  
**Έτος:** {selected_year}
"""
    )

    st.divider()

    # ---------------------------------------------------------
    # Υπολογισμός βασικών δεικτών
    # ---------------------------------------------------------

    total_positions = safe_int(
        df_department["initial_positions"].sum()
    )

    total_admitted = safe_int(
        df_department["admitted"].sum()
    )

    total_empty_positions = (
        total_positions
        - total_admitted
    )

    total_coverage = (
        total_admitted / total_positions * 100
        if total_positions > 0
        else 0
    )

    gel_row = get_gel_day_row(df_department)

    if gel_row is not None:
        gel_day_positions = safe_int(
            gel_row.get("final_positions", gel_row.get("initial_positions", 0))
        )

        if gel_day_positions == 0:
            gel_day_positions = safe_int(
                gel_row.get("initial_positions", 0)
            )

        gel_day_admitted = safe_int(
            gel_row.get("admitted", 0)
        )

        gel_day_empty_positions = (
            gel_day_positions
            - gel_day_admitted
        )

        gel_day_coverage = (
            gel_day_admitted / gel_day_positions * 100
            if gel_day_positions > 0
            else 0
        )

        gel_day_base_score = safe_score(
            gel_row.get("base_score", None)
        )

        gel_day_first_score = safe_score(
            gel_row.get("first_score", None)
        )

    else:
        gel_day_positions = 0
        gel_day_admitted = 0
        gel_day_empty_positions = 0
        gel_day_coverage = 0
        gel_day_base_score = None
        gel_day_first_score = None

    # ---------------------------------------------------------
    # Βασικοί δείκτες προγράμματος
    # ---------------------------------------------------------

    st.subheader("Βασικοί δείκτες προγράμματος")

    # 1η σειρά: Συνολική εικόνα προγράμματος
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.metric(
            "Συνολικές Θέσεις",
            total_positions
        )

    with kpi2:
        st.metric(
            "Επιτυχόντες",
            total_admitted
        )

    with kpi3:
        st.metric(
            "Κενές Θέσεις",
            total_empty_positions
        )

    with kpi4:
        st.metric(
            "Συνολική Κάλυψη",
            f"{total_coverage:.2f}%"
        )

    # 2η σειρά: Εικόνα ΓΕΛ Ημερήσια
    gel_kpi1, gel_kpi2, gel_kpi3, gel_kpi4 = st.columns(4)

    with gel_kpi1:
        st.metric(
            "ΓΕΛ Ημερ. Θέσεις",
            gel_day_positions
        )

    with gel_kpi2:
        st.metric(
            "ΓΕΛ Ημερ. Επιτυχόντες",
            gel_day_admitted
        )

    with gel_kpi3:
        st.metric(
            "Κενές ΓΕΛ Ημερ.",
            gel_day_empty_positions
        )

    with gel_kpi4:
        st.metric(
            "Κάλυψη ΓΕΛ Ημερ.",
            f"{gel_day_coverage:.2f}%"
        )

    # 3η σειρά: Βαθμολογικά στοιχεία ΓΕΛ Ημερήσια
    score_kpi1, score_kpi2, score_kpi3, score_kpi4 = st.columns(4)

    with score_kpi1:
        st.metric(
            "Βάση ΓΕΛ Ημερ.",
            format_score(gel_day_base_score)
        )

    with score_kpi2:
        st.metric(
            "Πρώτος ΓΕΛ Ημερ.",
            format_score(gel_day_first_score)
        )

    with score_kpi3:
        st.empty()

    with score_kpi4:
        st.empty()

    st.caption(
        "Η πρώτη σειρά αφορά το σύνολο των κατηγοριών εισαγωγής. "
        "Η δεύτερη και η τρίτη σειρά αφορούν αποκλειστικά τη ΓΕΛ Ημερήσια."
    )

    st.divider()

    # ---------------------------------------------------------
    # Πίνακας κατηγοριών
    # ---------------------------------------------------------

    st.subheader(
        "Ανάλυση ανά κατηγορία εισαγωγής — πληροφοριακή ανάλυση, όχι άθροισμα συνολικών κενών"
    )

    category_table = build_category_analysis_table(df_department)

    st.dataframe(
        style_category_table(category_table),
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Στον πίνακα η ΓΕΛ Ημερήσια επισημαίνεται με κίτρινο, επειδή αποτελεί τη βασική "
        "κατηγορία αναφοράς για τη βάση και τον πρώτο κάθε προγράμματος. "
        "Οι γραμμές 10% ΓΕΛ επισημαίνονται με γαλάζιο. Οι κενές θέσεις των κατηγοριών "
        "10% ΓΕΛ εμφανίζονται μόνο πληροφοριακά και δεν πρέπει να αθροίζονται ξανά "
        "με τις συνολικές κενές θέσεις, καθώς οι αδιάθετες θέσεις μεταφέρονται / "
        "απορροφώνται στη ΓΕΛ Ημερήσια."
    )

    st.info(
        "Για τη συνολική εικόνα του προγράμματος χρησιμοποιούνται οι βασικοί δείκτες "
        "στο επάνω μέρος της σελίδας: Συνολικές Θέσεις, Επιτυχόντες, Κενές Θέσεις "
        "και Συνολική Κάλυψη."
    )

    st.divider()

    # ---------------------------------------------------------
    # Γραφήματα
    # ---------------------------------------------------------

    st.subheader("Βασικά διαγράμματα προγράμματος")

    chart_choice = st.selectbox(
        "Επιλέξτε διάγραμμα",
        [
            "Θέσεις και επιτυχόντες ανά κατηγορία",
            "Κάλυψη ανά κατηγορία",
            "Κενές θέσεις ανά κατηγορία",
            "Βαθμολογικά στοιχεία ανά κατηγορία",
        ]
    )

    if chart_choice == "Θέσεις και επιτυχόντες ανά κατηγορία":
        fig = create_positions_by_category_chart(category_table)

    elif chart_choice == "Κάλυψη ανά κατηγορία":
        fig = create_coverage_chart(category_table)

    elif chart_choice == "Κενές θέσεις ανά κατηγορία":
        fig = create_empty_positions_chart(category_table)

    else:
        fig = create_scores_chart(category_table)

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.caption(
        "Τα διαγράμματα αφορούν τις επιμέρους κατηγορίες εισαγωγής του επιλεγμένου "
        "προγράμματος. Οι κενές θέσεις των κατηγοριών 10% ΓΕΛ εμφανίζονται πληροφοριακά "
        "και δεν πρέπει να αθροίζονται ξανά με τις συνολικές κενές θέσεις."
    )

except Exception as e:
    st.error("Υπήρξε πρόβλημα κατά την ανάλυση του προγράμματος.")
    st.exception(e)