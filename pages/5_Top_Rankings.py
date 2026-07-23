import pandas as pd
import streamlit as st
import plotly.express as px

from modules.database_manager import load_admissions_with_departments
from components.sidebar_branding import show_sidebar_branding


# ---------------------------------------------------------
# Ρυθμίσεις σελίδας
# ---------------------------------------------------------

st.set_page_config(
    page_title="Top Rankings | ΔΙΠΑΕ",
    page_icon="🏆",
    layout="wide"
)

show_sidebar_branding()


st.title("🏆 Top Rankings Προγραμμάτων ΔΙ.ΠΑ.Ε.")

st.markdown("""
Η σελίδα παρουσιάζει κατατάξεις των ενεργών προπτυχιακών προγραμμάτων σπουδών
του ΔΙ.ΠΑ.Ε. με βάση βασικούς δείκτες εισακτέων.

**Μεθοδολογικοί κανόνες:**

- Η ανάλυση γίνεται πάντα για **όλες τις κατηγορίες εισαγωγής**.
- Οι **Συνολικές Θέσεις** υπολογίζονται από τις **Αρχικές Θέσεις**.
- Η **Συνολική Κάλυψη** υπολογίζεται ως: Επιτυχόντες όλων των κατηγοριών / Συνολικές Θέσεις.
- Η **Κάλυψη ΓΕΛ Ημερήσια** υπολογίζεται μόνο για τη βασική κατηγορία ΓΕΛ Ημερήσια.
- Η **Βάση Προγράμματος** είναι η **Βάση ΓΕΛ Ημερήσια**.
- Ο **Πρώτος Προγράμματος** είναι ο **Πρώτος ΓΕΛ Ημερήσια**.
- Δεν εμφανίζονται τελικές θέσεις ή φαινόμενη μεταβολή θέσεων.
- Δεν υπολογίζονται μέσοι όροι βάσεων.
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
                "gel_day_first_score",
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
    - βάση και πρώτος ΓΕΛ Ημερήσια
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
        "gel_day_first_score",
        "gel_day_base_score",
    ]:
        if col not in summary.columns:
            summary[col] = 0

    for col in [
        "gel_day_positions",
        "gel_day_admitted",
        "gel_day_empty",
        "gel_day_coverage",
        "gel_day_first_score",
        "gel_day_base_score",
    ]:
        summary[col] = summary[col].fillna(0)

    return summary


def format_ranking_table(df, columns):
    """
    Μορφοποιεί πίνακα κατάταξης.
    """

    display = df[columns].copy()

    rename_map = {
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
        "gel_day_first_score": "Πρώτος ΓΕΛ Ημ.",
        "gel_day_base_score": "Βάση ΓΕΛ Ημ.",
    }

    display = display.rename(columns=rename_map)

    integer_columns = [
        "Συνολικές Θέσεις",
        "Επιτυχόντες",
        "Κενές Θέσεις",
        "ΓΕΛ Ημερήσια Θέσεις",
        "ΓΕΛ Ημερήσια Επιτυχόντες",
        "Κενές ΓΕΛ Ημερήσια",
        "Πρώτος ΓΕΛ Ημ.",
        "Βάση ΓΕΛ Ημ.",
    ]

    for col in integer_columns:
        if col in display.columns:
            display[col] = (
                display[col]
                .fillna(0)
                .round(0)
                .astype(int)
            )

    percent_columns = [
        "Συνολική Κάλυψη %",
        "Κάλυψη ΓΕΛ Ημ. %",
    ]

    for col in percent_columns:
        if col in display.columns:
            display[col] = (
                display[col]
                .fillna(0)
                .round(2)
            )

    return display


def format_full_table(df):
    """
    Πλήρης συγκεντρωτικός πίνακας προγραμμάτων.
    """

    columns = [
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
        "gel_day_first_score",
        "gel_day_base_score",
    ]

    return format_ranking_table(df, columns)


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
    Κοινό styling για όλους τους πίνακες.
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

def apply_chart_layout(fig, title, xaxis_title, yaxis_title):
    """
    Κοινή μορφοποίηση οριζόντιων γραφημάτων.
    """

    fig.update_layout(
        title=title,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        height=720,
        margin=dict(l=20, r=180, t=80, b=40),
        uniformtext_minsize=8,
        uniformtext_mode="show"
    )

    fig.update_yaxes(
        automargin=True
    )

    fig.update_xaxes(
        automargin=True
    )

    return fig


def create_base_chart(df):
    """
    Top βάση ΓΕΛ Ημερήσια.
    """

    chart_df = (
        df[df["gel_day_base_score"] > 0]
        .sort_values("gel_day_base_score", ascending=True)
        .copy()
    )

    max_value = (
        chart_df["gel_day_base_score"].max()
        if not chart_df.empty
        else 0
    )

    fig = px.bar(
        chart_df,
        x="gel_day_base_score",
        y="department_name_clean",
        orientation="h",
        text="gel_day_base_score",
        title="Υψηλότερες βάσεις ΓΕΛ Ημερήσια"
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

    fig = apply_chart_layout(
        fig=fig,
        title="Υψηλότερες βάσεις ΓΕΛ Ημερήσια",
        xaxis_title="Βάση ΓΕΛ Ημερήσια",
        yaxis_title=""
    )

    return fig


def create_first_score_chart(df):
    """
    Top πρώτος ΓΕΛ Ημερήσια.
    """

    chart_df = (
        df[df["gel_day_first_score"] > 0]
        .sort_values("gel_day_first_score", ascending=True)
        .copy()
    )

    max_value = (
        chart_df["gel_day_first_score"].max()
        if not chart_df.empty
        else 0
    )

    fig = px.bar(
        chart_df,
        x="gel_day_first_score",
        y="department_name_clean",
        orientation="h",
        text="gel_day_first_score",
        title="Υψηλότερος πρώτος ΓΕΛ Ημερήσια"
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
            max(22000, max_value * 1.12)
        ]
    )

    fig = apply_chart_layout(
        fig=fig,
        title="Υψηλότερος πρώτος ΓΕΛ Ημερήσια",
        xaxis_title="Πρώτος ΓΕΛ Ημερήσια",
        yaxis_title=""
    )

    return fig


def create_admitted_chart(df):
    """
    Top επιτυχόντες.
    """

    chart_df = df.sort_values(
        "total_admitted",
        ascending=True
    ).copy()

    max_value = (
        chart_df["total_admitted"].max()
        if not chart_df.empty
        else 0
    )

    fig = px.bar(
        chart_df,
        x="total_admitted",
        y="department_name_clean",
        orientation="h",
        text="total_admitted",
        title="Περισσότεροι επιτυχόντες ανά πρόγραμμα"
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
            max(10, max_value * 1.25)
        ]
    )

    fig = apply_chart_layout(
        fig=fig,
        title="Περισσότεροι επιτυχόντες ανά πρόγραμμα",
        xaxis_title="Επιτυχόντες",
        yaxis_title=""
    )

    return fig


def create_total_coverage_chart(df):
    """
    Ranking συνολικής κάλυψης.
    """

    chart_df = df.sort_values(
        "total_coverage",
        ascending=True
    ).copy()

    chart_df["label_text"] = chart_df.apply(
        lambda row: (
            f'{row["total_coverage"]:.2f}% | '
            f'<b>ΓΕΛ Ημ.: {row["gel_day_coverage"]:.2f}%</b>'
        ),
        axis=1
    )

    fig = px.bar(
        chart_df,
        x="total_coverage",
        y="department_name_clean",
        orientation="h",
        text="label_text",
        title="Συνολική κάλυψη ανά πρόγραμμα"
    )

    fig.update_traces(
        texttemplate="%{text}",
        textposition="outside",
        textfont_size=10,
        cliponaxis=False
    )

    fig.update_layout(
        xaxis_range=[0, 135]
    )

    fig = apply_chart_layout(
        fig=fig,
        title="Συνολική κάλυψη ανά πρόγραμμα",
        xaxis_title="Συνολική Κάλυψη %",
        yaxis_title=""
    )

    fig.add_annotation(
        text=(
            "Σημείωση: Η πρώτη τιμή δείχνει τη Συνολική Κάλυψη. "
            "<b>Η έντονη τιμή δείχνει την Κάλυψη ΓΕΛ Ημερήσια.</b>"
        ),
        xref="paper",
        yref="paper",
        x=0,
        y=-0.10,
        showarrow=False,
        align="left",
        font=dict(size=12)
    )

    fig.update_layout(
        margin=dict(l=20, r=280, t=80, b=90)
    )

    return fig


def create_gel_day_coverage_chart(df):
    """
    Ranking κάλυψης ΓΕΛ Ημερήσια.
    """

    chart_df = df.sort_values(
        "gel_day_coverage",
        ascending=True
    ).copy()

    fig = px.bar(
        chart_df,
        x="gel_day_coverage",
        y="department_name_clean",
        orientation="h",
        text="gel_day_coverage",
        title="Κάλυψη ΓΕΛ Ημερήσια ανά πρόγραμμα"
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

    fig = apply_chart_layout(
        fig=fig,
        title="Κάλυψη ΓΕΛ Ημερήσια ανά πρόγραμμα",
        xaxis_title="Κάλυψη ΓΕΛ Ημερήσια %",
        yaxis_title=""
    )

    return fig


def create_empty_chart(df):
    """
    Ranking κενών θέσεων.
    """

    chart_df = df.sort_values(
        "empty_positions",
        ascending=True
    ).copy()

    max_value = (
        chart_df["empty_positions"].max()
        if not chart_df.empty
        else 0
    )

    fig = px.bar(
        chart_df,
        x="empty_positions",
        y="department_name_clean",
        orientation="h",
        text="empty_positions",
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
            max(5, max_value * 1.25)
        ],
        xaxis=dict(dtick=1)
    )

    fig = apply_chart_layout(
        fig=fig,
        title="Κενές θέσεις ανά πρόγραμμα",
        xaxis_title="Κενές Θέσεις",
        yaxis_title=""
    )

    return fig


def create_positions_chart(df):
    """
    Ranking συνολικών θέσεων.
    """

    chart_df = df.sort_values(
        "total_positions",
        ascending=True
    ).copy()

    max_value = (
        chart_df["total_positions"].max()
        if not chart_df.empty
        else 0
    )

    fig = px.bar(
        chart_df,
        x="total_positions",
        y="department_name_clean",
        orientation="h",
        text="total_positions",
        title="Συνολικές θέσεις ανά πρόγραμμα"
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
            max(10, max_value * 1.25)
        ]
    )

    fig = apply_chart_layout(
        fig=fig,
        title="Συνολικές θέσεις ανά πρόγραμμα",
        xaxis_title="Συνολικές Θέσεις",
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

    st.subheader(f"Συνολική εικόνα rankings {selected_year}")

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

    # ---------------------------------------------------------
    # Επιλογές Top N
    # ---------------------------------------------------------

    top_n = st.slider(
        "Πλήθος προγραμμάτων στα rankings",
        min_value=3,
        max_value=23,
        value=10,
        step=1
    )

    st.divider()

    # ---------------------------------------------------------
    # Tabs rankings
    # ---------------------------------------------------------

    tab_base, tab_first, tab_admitted, tab_total_cov, tab_gel_cov, tab_empty, tab_positions, tab_full = st.tabs(
        [
            "Βάσεις ΓΕΛ Ημ.",
            "Πρώτοι ΓΕΛ Ημ.",
            "Επιτυχόντες",
            "Συνολική Κάλυψη",
            "Κάλυψη ΓΕΛ Ημ.",
            "Κενές Θέσεις",
            "Θέσεις",
            "Πλήρης Πίνακας",
        ]
    )

    with tab_base:
        st.subheader("Υψηλότερες βάσεις ΓΕΛ Ημερήσια")

        ranking_df = (
            department_summary[
                department_summary["gel_day_base_score"] > 0
            ]
            .sort_values(
                "gel_day_base_score",
                ascending=False
            )
            .head(top_n)
        )

        display = format_ranking_table(
            ranking_df,
            [
                "department_name_clean",
                "school",
                "city",
                "gel_day_base_score",
                "gel_day_first_score",
                "total_coverage",
                "gel_day_coverage",
                "total_admitted",
            ]
        )

        st.dataframe(
            style_table(display),
            use_container_width=True,
            hide_index=True
        )

        fig = create_base_chart(ranking_df)
        st.plotly_chart(fig, use_container_width=True)

    with tab_first:
        st.subheader("Υψηλότερος πρώτος ΓΕΛ Ημερήσια")

        ranking_df = (
            department_summary[
                department_summary["gel_day_first_score"] > 0
            ]
            .sort_values(
                "gel_day_first_score",
                ascending=False
            )
            .head(top_n)
        )

        display = format_ranking_table(
            ranking_df,
            [
                "department_name_clean",
                "school",
                "city",
                "gel_day_first_score",
                "gel_day_base_score",
                "total_coverage",
                "gel_day_coverage",
                "total_admitted",
            ]
        )

        st.dataframe(
            style_table(display),
            use_container_width=True,
            hide_index=True
        )

        fig = create_first_score_chart(ranking_df)
        st.plotly_chart(fig, use_container_width=True)

    with tab_admitted:
        st.subheader("Προγράμματα με περισσότερους επιτυχόντες")

        ranking_df = (
            department_summary
            .sort_values(
                "total_admitted",
                ascending=False
            )
            .head(top_n)
        )

        display = format_ranking_table(
            ranking_df,
            [
                "department_name_clean",
                "school",
                "city",
                "total_admitted",
                "total_positions",
                "empty_positions",
                "total_coverage",
                "gel_day_coverage",
                "gel_day_base_score",
            ]
        )

        st.dataframe(
            style_table(display),
            use_container_width=True,
            hide_index=True
        )

        fig = create_admitted_chart(ranking_df)
        st.plotly_chart(fig, use_container_width=True)

    with tab_total_cov:
        st.subheader("Κατάταξη με βάση τη Συνολική Κάλυψη")

        ranking_df = (
            department_summary
            .sort_values(
                "total_coverage",
                ascending=False
            )
            .head(top_n)
        )

        display = format_ranking_table(
            ranking_df,
            [
                "department_name_clean",
                "school",
                "city",
                "total_coverage",
                "gel_day_coverage",
                "total_positions",
                "total_admitted",
                "empty_positions",
                "gel_day_base_score",
            ]
        )

        st.dataframe(
            style_table(display),
            use_container_width=True,
            hide_index=True
        )

        fig = create_total_coverage_chart(ranking_df)
        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "Η «Συνολική Κάλυψη %» υπολογίζεται επί των συνολικών θέσεων όλων "
            "των κατηγοριών εισαγωγής. Στο γράφημα η έντονη τιμή δείχνει την Κάλυψη ΓΕΛ Ημερήσια."
        )

    with tab_gel_cov:
        st.subheader("Κατάταξη με βάση την Κάλυψη ΓΕΛ Ημερήσια")

        ranking_df = (
            department_summary
            .sort_values(
                "gel_day_coverage",
                ascending=False
            )
            .head(top_n)
        )

        display = format_ranking_table(
            ranking_df,
            [
                "department_name_clean",
                "school",
                "city",
                "gel_day_coverage",
                "total_coverage",
                "gel_day_positions",
                "gel_day_admitted",
                "gel_day_empty",
                "gel_day_base_score",
            ]
        )

        st.dataframe(
            style_table(display),
            use_container_width=True,
            hide_index=True
        )

        fig = create_gel_day_coverage_chart(ranking_df)
        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "Η «Κάλυψη ΓΕΛ Ημ. %» υπολογίζεται μόνο επί των θέσεων της ΓΕΛ Ημερήσιας."
        )

    with tab_empty:
        st.subheader("Προγράμματα με περισσότερες κενές θέσεις")

        ranking_df = (
            department_summary
            .sort_values(
                "empty_positions",
                ascending=False
            )
            .head(top_n)
        )

        display = format_ranking_table(
            ranking_df,
            [
                "department_name_clean",
                "school",
                "city",
                "empty_positions",
                "total_positions",
                "total_admitted",
                "total_coverage",
                "gel_day_empty",
                "gel_day_coverage",
                "gel_day_base_score",
            ]
        )

        st.dataframe(
            style_table(display),
            use_container_width=True,
            hide_index=True
        )

        fig = create_empty_chart(ranking_df)
        st.plotly_chart(fig, use_container_width=True)

    with tab_positions:
        st.subheader("Προγράμματα με περισσότερες συνολικές θέσεις")

        ranking_df = (
            department_summary
            .sort_values(
                "total_positions",
                ascending=False
            )
            .head(top_n)
        )

        display = format_ranking_table(
            ranking_df,
            [
                "department_name_clean",
                "school",
                "city",
                "total_positions",
                "total_admitted",
                "empty_positions",
                "total_coverage",
                "gel_day_coverage",
                "gel_day_base_score",
            ]
        )

        st.dataframe(
            style_table(display),
            use_container_width=True,
            hide_index=True
        )

        fig = create_positions_chart(ranking_df)
        st.plotly_chart(fig, use_container_width=True)

    with tab_full:
        st.subheader("Πλήρης συγκεντρωτικός πίνακας προγραμμάτων")

        full_display = format_full_table(
            department_summary.sort_values(
                "gel_day_base_score",
                ascending=False
            )
        )

        st.dataframe(
            style_table(full_display),
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "Η «Συνολική Κάλυψη %» υπολογίζεται επί των συνολικών θέσεων όλων "
            "των κατηγοριών εισαγωγής. Η «Κάλυψη ΓΕΛ Ημ. %» υπολογίζεται μόνο "
            "επί των θέσεων της ΓΕΛ Ημερήσιας."
        )

except Exception as e:
    st.error("Υπήρξε πρόβλημα κατά την προβολή των Top Rankings.")
    st.exception(e)