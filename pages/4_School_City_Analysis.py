import pandas as pd
import streamlit as st
import plotly.express as px

from modules.database_manager import load_admissions_with_departments
from components.sidebar_branding import show_sidebar_branding


# ---------------------------------------------------------
# Ρυθμίσεις σελίδας
# ---------------------------------------------------------

st.set_page_config(
    page_title="Σχολές και Πόλεις | ΔΙΠΑΕ",
    page_icon="🏫",
    layout="wide"
)

show_sidebar_branding()


st.title("🏫 Ανάλυση ανά Σχολή και Πόλη")

st.markdown("""
Η σελίδα παρουσιάζει συγκεντρωτική εικόνα των εισακτέων ανά **Σχολή** και ανά **Πόλη**
του ΔΙ.ΠΑ.Ε.

**Μεθοδολογικοί κανόνες:**

- Η ανάλυση γίνεται πάντα για **όλες τις κατηγορίες εισαγωγής**.
- Οι **Συνολικές Θέσεις** υπολογίζονται από τις **Αρχικές Θέσεις**.
- Η **Συνολική Κάλυψη** υπολογίζεται ως: Επιτυχόντες όλων των κατηγοριών / Συνολικές Θέσεις.
- Η **Κάλυψη ΓΕΛ Ημερήσια** υπολογίζεται μόνο για τη βασική κατηγορία ΓΕΛ Ημερήσια.
- Η **Βάση Προγράμματος** είναι η **Βάση ΓΕΛ Ημερήσια**.
- Δεν εμφανίζονται τελικές θέσεις ή φαινόμενη μεταβολή θέσεων.
- Δεν υπολογίζονται μέσοι όροι βάσεων ανά Σχολή ή Πόλη.
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


def get_gel_day_data(df_year):
    """
    Επιστρέφει στοιχεία ΓΕΛ Ημερήσια ανά πρόγραμμα.

    Για τη ΓΕΛ Ημερήσια χρησιμοποιούμε τις final_positions,
    γιατί εκεί φαίνονται οι θέσεις κατόπιν μεταφοράς.
    """

    df_gel = df_year[
        df_year["exam_category"] == "ΓΕΛ Ημερήσια"
    ].copy()

    if df_gel.empty:
        return pd.DataFrame(
            columns=[
                "department_code",
                "gel_day_positions",
                "gel_day_admitted",
                "gel_day_empty",
                "gel_day_coverage",
                "gel_day_base_score",
            ]
        )

    df_gel["gel_day_positions"] = (
        df_gel["final_positions"]
        .fillna(df_gel["initial_positions"])
    )

    df_gel["gel_day_admitted"] = (
        df_gel["admitted"]
        .fillna(0)
    )

    df_gel["gel_day_empty"] = (
        df_gel["gel_day_positions"]
        - df_gel["gel_day_admitted"]
    )

    df_gel["gel_day_coverage"] = (
        df_gel["gel_day_admitted"]
        / df_gel["gel_day_positions"]
        * 100
    )

    gel_data = (
        df_gel[
            [
                "department_code",
                "gel_day_positions",
                "gel_day_admitted",
                "gel_day_empty",
                "gel_day_coverage",
                "base_score",
            ]
        ]
        .drop_duplicates(subset=["department_code"])
        .rename(
            columns={
                "base_score": "gel_day_base_score",
            }
        )
    )

    return gel_data


def build_department_summary(df_year):
    """
    Δημιουργεί σύνοψη ανά προπτυχιακό πρόγραμμα.

    Συνολική εικόνα:
    - όλες οι κατηγορίες εισαγωγής
    - συνολικές θέσεις = αρχικές θέσεις

    ΓΕΛ Ημερήσια:
    - θέσεις ΓΕΛ Ημερήσια
    - επιτυχόντες ΓΕΛ Ημερήσια
    - κάλυψη ΓΕΛ Ημερήσια
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

    summary["total_coverage"] = (
        summary["total_admitted"]
        / summary["total_positions"]
        * 100
    )

    gel_data = get_gel_day_data(df_year)

    summary = summary.merge(
        gel_data,
        on="department_code",
        how="left"
    )

    for col in [
        "gel_day_positions",
        "gel_day_admitted",
        "gel_day_empty",
        "gel_day_coverage",
        "gel_day_base_score",
    ]:
        if col not in summary.columns:
            summary[col] = 0

    for col in [
        "gel_day_positions",
        "gel_day_admitted",
        "gel_day_empty",
        "gel_day_coverage",
    ]:
        summary[col] = summary[col].fillna(0)

    return summary


def build_group_summary(department_summary, group_col):
    """
    Δημιουργεί συγκεντρωτικό πίνακα ανά Σχολή ή Πόλη.

    Δεν υπολογίζει μέσο όρο βάσεων.
    """

    group_summary = (
        department_summary
        .groupby(
            group_col,
            as_index=False
        )
        .agg(
            programs=("department_code", "nunique"),
            total_positions=("total_positions", "sum"),
            total_admitted=("total_admitted", "sum"),
            empty_positions=("empty_positions", "sum"),
            gel_day_positions=("gel_day_positions", "sum"),
            gel_day_admitted=("gel_day_admitted", "sum"),
            gel_day_empty=("gel_day_empty", "sum"),
        )
    )

    group_summary["total_coverage"] = (
        group_summary["total_admitted"]
        / group_summary["total_positions"]
        * 100
    )

    group_summary["gel_day_coverage"] = (
        group_summary["gel_day_admitted"]
        / group_summary["gel_day_positions"]
        * 100
    )

    group_summary["total_coverage"] = (
        group_summary["total_coverage"]
        .fillna(0)
    )

    group_summary["gel_day_coverage"] = (
        group_summary["gel_day_coverage"]
        .fillna(0)
    )

    return group_summary


def format_group_table(df, group_label):
    """
    Μορφοποίηση συγκεντρωτικού πίνακα ανά Σχολή ή Πόλη.
    """

    display = df[
        [
            group_label,
            "programs",
            "total_positions",
            "total_admitted",
            "empty_positions",
            "total_coverage",
            "gel_day_positions",
            "gel_day_admitted",
            "gel_day_empty",
            "gel_day_coverage",
        ]
    ].copy()

    display = display.rename(
        columns={
            group_label: "Ομάδα",
            "programs": "Προγράμματα",
            "total_positions": "Συνολικές Θέσεις",
            "total_admitted": "Επιτυχόντες",
            "empty_positions": "Κενές Θέσεις",
            "total_coverage": "Συνολική Κάλυψη %",
            "gel_day_positions": "ΓΕΛ Ημερήσια Θέσεις",
            "gel_day_admitted": "ΓΕΛ Ημερήσια Επιτυχόντες",
            "gel_day_empty": "Κενές ΓΕΛ Ημερήσια",
            "gel_day_coverage": "Κάλυψη ΓΕΛ Ημ. %",
        }
    )

    for col in [
        "Προγράμματα",
        "Συνολικές Θέσεις",
        "Επιτυχόντες",
        "Κενές Θέσεις",
        "ΓΕΛ Ημερήσια Θέσεις",
        "ΓΕΛ Ημερήσια Επιτυχόντες",
        "Κενές ΓΕΛ Ημερήσια",
    ]:
        display[col] = (
            display[col]
            .fillna(0)
            .round(0)
            .astype(int)
        )

    for col in [
        "Συνολική Κάλυψη %",
        "Κάλυψη ΓΕΛ Ημ. %",
    ]:
        display[col] = (
            display[col]
            .fillna(0)
            .round(2)
        )

    return display


def format_department_table(df):
    """
    Αναλυτικός πίνακας προγραμμάτων.

    Περιλαμβάνει:
    - συνολική κάλυψη όλων των κατηγοριών
    - κάλυψη ΓΕΛ Ημερήσια
    - βάση ΓΕΛ Ημερήσια
    """

    display = df[
        [
            "department_name_clean",
            "school",
            "city",
            "total_positions",
            "total_admitted",
            "empty_positions",
            "total_coverage",
            "gel_day_positions",
            "gel_day_admitted",
            "gel_day_empty",
            "gel_day_coverage",
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
            "total_coverage": "Συνολική Κάλυψη %",
            "gel_day_positions": "ΓΕΛ Ημερήσια Θέσεις",
            "gel_day_admitted": "ΓΕΛ Ημερήσια Επιτυχόντες",
            "gel_day_empty": "Κενές ΓΕΛ Ημερήσια",
            "gel_day_coverage": "Κάλυψη ΓΕΛ Ημ. %",
            "gel_day_base_score": "Βάση ΓΕΛ Ημ.",
        }
    )

    for col in [
        "Συνολικές Θέσεις",
        "Επιτυχόντες",
        "Κενές Θέσεις",
        "ΓΕΛ Ημερήσια Θέσεις",
        "ΓΕΛ Ημερήσια Επιτυχόντες",
        "Κενές ΓΕΛ Ημερήσια",
        "Βάση ΓΕΛ Ημ.",
    ]:
        display[col] = (
            display[col]
            .fillna(0)
            .round(0)
            .astype(int)
        )

    for col in [
        "Συνολική Κάλυψη %",
        "Κάλυψη ΓΕΛ Ημ. %",
    ]:
        display[col] = (
            display[col]
            .fillna(0)
            .round(2)
        )

    return display


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


def style_table(df):
    """
    Κοινό styling για πίνακες.

    Όλες οι στήλες κάλυψης εμφανίζονται με 2 δεκαδικά και σύμβολο %.
    """

    style_obj = df.style

    format_dict = {}

    for col in df.columns:
        if "Κάλυψη" in col and "%" in col:
            format_dict[col] = "{:.2f}%"

    if format_dict:
        style_obj = style_obj.format(format_dict)

    empty_columns = [
        col for col in df.columns
        if "Κενές" in col
    ]

    for col in empty_columns:
        try:
            style_obj = style_obj.map(
                highlight_empty_positions,
                subset=[col]
            )
        except AttributeError:
            style_obj = style_obj.applymap(
                highlight_empty_positions,
                subset=[col]
            )

    coverage_columns = [
        col for col in df.columns
        if "Κάλυψη" in col and "%" in col
    ]

    for col in coverage_columns:
        try:
            style_obj = style_obj.map(
                highlight_coverage,
                subset=[col]
            )
        except AttributeError:
            style_obj = style_obj.applymap(
                highlight_coverage,
                subset=[col]
            )

    return style_obj


# ---------------------------------------------------------
# Γραφήματα
# ---------------------------------------------------------

def create_positions_chart(group_display):
    """
    Θέσεις και επιτυχόντες ανά ομάδα.
    """

    chart_df = group_display[
        [
            "Ομάδα",
            "Συνολικές Θέσεις",
            "Επιτυχόντες",
        ]
    ].copy()

    chart_long = chart_df.melt(
        id_vars="Ομάδα",
        value_vars=[
            "Συνολικές Θέσεις",
            "Επιτυχόντες",
        ],
        var_name="Δείκτης",
        value_name="Πλήθος"
    )

    fig = px.bar(
        chart_long,
        x="Ομάδα",
        y="Πλήθος",
        color="Δείκτης",
        barmode="group",
        text="Πλήθος",
        title="Συνολικές θέσεις και επιτυχόντες ανά ομάδα"
    )

    fig.update_traces(
        texttemplate="%{text:.0f}",
        textposition="outside",
        cliponaxis=False
    )

    max_value = (
        chart_long["Πλήθος"].max()
        if not chart_long.empty
        else 0
    )

    fig.update_layout(
        height=560,
        xaxis_title="",
        yaxis_title="Πλήθος",
        yaxis_range=[0, max(10, max_value * 1.25)],
        legend_title="",
        margin=dict(l=20, r=80, t=80, b=120)
    )

    fig.update_xaxes(
        tickangle=-30
    )

    return fig


def create_coverage_chart(group_display):
    """
    Συνολική κάλυψη και κάλυψη ΓΕΛ Ημερήσια ανά ομάδα.
    """

    chart_df = group_display[
        [
            "Ομάδα",
            "Συνολική Κάλυψη %",
            "Κάλυψη ΓΕΛ Ημ. %",
        ]
    ].copy()

    chart_long = chart_df.melt(
        id_vars="Ομάδα",
        value_vars=[
            "Συνολική Κάλυψη %",
            "Κάλυψη ΓΕΛ Ημ. %",
        ],
        var_name="Δείκτης",
        value_name="Κάλυψη %"
    )

    fig = px.bar(
        chart_long,
        x="Ομάδα",
        y="Κάλυψη %",
        color="Δείκτης",
        barmode="group",
        text="Κάλυψη %",
        title="Συνολική κάλυψη και κάλυψη ΓΕΛ Ημερήσια ανά ομάδα"
    )

    fig.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",
        cliponaxis=False
    )

    fig.update_layout(
        height=560,
        xaxis_title="",
        yaxis_title="Κάλυψη %",
        yaxis_range=[0, 115],
        legend_title="",
        margin=dict(l=20, r=80, t=80, b=120)
    )

    fig.update_yaxes(
        tickformat=".0f"
    )

    fig.update_xaxes(
        tickangle=-30
    )

    return fig


def create_admitted_chart(group_display):
    """
    Επιτυχόντες ανά ομάδα.
    """

    chart_df = group_display.sort_values(
        "Επιτυχόντες",
        ascending=False
    ).copy()

    fig = px.bar(
        chart_df,
        x="Ομάδα",
        y="Επιτυχόντες",
        text="Επιτυχόντες",
        title="Επιτυχόντες ανά ομάδα"
    )

    fig.update_traces(
        texttemplate="%{text:.0f}",
        textposition="outside",
        cliponaxis=False
    )

    max_value = (
        chart_df["Επιτυχόντες"].max()
        if not chart_df.empty
        else 0
    )

    fig.update_layout(
        height=560,
        xaxis_title="",
        yaxis_title="Επιτυχόντες",
        yaxis_range=[0, max(10, max_value * 1.25)],
        margin=dict(l=20, r=80, t=80, b=120)
    )

    fig.update_xaxes(
        tickangle=-30
    )

    return fig


def create_empty_chart(group_display):
    """
    Κενές θέσεις ανά ομάδα.
    """

    chart_df = group_display.sort_values(
        "Κενές Θέσεις",
        ascending=False
    ).copy()

    fig = px.bar(
        chart_df,
        x="Ομάδα",
        y="Κενές Θέσεις",
        text="Κενές Θέσεις",
        title="Κενές θέσεις ανά ομάδα"
    )

    fig.update_traces(
        texttemplate="%{text:.0f}",
        textposition="outside",
        cliponaxis=False
    )

    max_value = (
        chart_df["Κενές Θέσεις"].max()
        if not chart_df.empty
        else 0
    )

    fig.update_layout(
        height=560,
        xaxis_title="",
        yaxis_title="Κενές Θέσεις",
        yaxis_range=[0, max(5, max_value * 1.25)],
        margin=dict(l=20, r=80, t=80, b=120)
    )

    fig.update_xaxes(
        tickangle=-30
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

    total_positions = safe_int(department_summary["total_positions"].sum())
    total_admitted = safe_int(department_summary["total_admitted"].sum())
    total_empty_positions = safe_int(department_summary["empty_positions"].sum())

    total_coverage = (
        total_admitted / total_positions * 100
        if total_positions > 0
        else 0
    )

    total_gel_day_positions = safe_int(
        department_summary["gel_day_positions"]
        .fillna(0)
        .sum()
    )

    total_gel_day_admitted = safe_int(
        department_summary["gel_day_admitted"]
        .fillna(0)
        .sum()
    )

    total_gel_day_coverage = (
        total_gel_day_admitted / total_gel_day_positions * 100
        if total_gel_day_positions > 0
        else 0
    )

    st.subheader(f"Συνολική εικόνα ανά Σχολή και Πόλη {selected_year}")

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
            "Κάλυψη ΓΕΛ Ημερήσια",
            f"{total_gel_day_coverage:.2f}%"
        )

    st.caption(
        "Η Συνολική Κάλυψη αφορά όλες τις κατηγορίες εισαγωγής. "
        "Η Κάλυψη ΓΕΛ Ημερήσια αφορά αποκλειστικά τη βασική κατηγορία ΓΕΛ Ημερήσια."
    )

    st.divider()

    analysis_mode = st.radio(
        "Επιλέξτε επίπεδο ανάλυσης",
        [
            "Σχολές",
            "Πόλεις",
        ],
        horizontal=True
    )

    if analysis_mode == "Σχολές":
        group_col = "school"
        group_title = "Σχολές"
    else:
        group_col = "city"
        group_title = "Πόλεις"

    group_summary = build_group_summary(
        department_summary=department_summary,
        group_col=group_col
    )

    group_display = format_group_table(
        df=group_summary,
        group_label=group_col
    )

    group_display = group_display.sort_values(
        "Συνολική Κάλυψη %",
        ascending=True
    )

    st.subheader(f"Συγκεντρωτικός πίνακας ανά {group_title}")

    st.dataframe(
        style_table(group_display),
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Η «Συνολική Κάλυψη %» υπολογίζεται επί των συνολικών θέσεων όλων "
        "των κατηγοριών εισαγωγής. Η «Κάλυψη ΓΕΛ Ημ. %» υπολογίζεται μόνο "
        "επί των θέσεων της ΓΕΛ Ημερήσιας."
    )

    st.divider()

    st.subheader(f"Βασικά διαγράμματα ανά {group_title}")

    chart_choice = st.selectbox(
        "Επιλέξτε διάγραμμα",
        [
            "Συνολικές θέσεις και επιτυχόντες",
            "Συνολική κάλυψη και κάλυψη ΓΕΛ Ημερήσια",
            "Επιτυχόντες",
            "Κενές θέσεις",
        ]
    )

    if chart_choice == "Συνολικές θέσεις και επιτυχόντες":
        fig = create_positions_chart(group_display)

    elif chart_choice == "Συνολική κάλυψη και κάλυψη ΓΕΛ Ημερήσια":
        fig = create_coverage_chart(group_display)

    elif chart_choice == "Επιτυχόντες":
        fig = create_admitted_chart(group_display)

    else:
        fig = create_empty_chart(group_display)

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.caption(
        "Τα διαγράμματα παρουσιάζουν συγκεντρωτικά στοιχεία ανά επιλεγμένη ομάδα "
        "και όχι μεμονωμένα ανά πρόγραμμα."
    )

    st.divider()

    st.subheader("Αναλυτικός πίνακας προγραμμάτων")

    department_display = format_department_table(
        department_summary.sort_values(
            [
                group_col,
                "department_name_clean",
            ]
        )
    )

    st.dataframe(
        style_table(department_display),
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Στον αναλυτικό πίνακα εμφανίζονται τόσο η Συνολική Κάλυψη όλων των κατηγοριών "
        "όσο και η Κάλυψη ΓΕΛ Ημερήσια ανά πρόγραμμα."
    )

except Exception as e:
    st.error("Υπήρξε πρόβλημα κατά την ανάλυση ανά Σχολή και Πόλη.")
    st.exception(e)