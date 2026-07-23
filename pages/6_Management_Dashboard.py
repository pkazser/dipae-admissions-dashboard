import pandas as pd
import streamlit as st
import plotly.express as px

from modules.database_manager import load_admissions_with_departments
from components.sidebar_branding import show_sidebar_branding


# ---------------------------------------------------------
# Ρυθμίσεις σελίδας
# ---------------------------------------------------------

st.set_page_config(
    page_title="Management Dashboard | ΔΙΠΑΕ",
    page_icon="📊",
    layout="wide"
)

show_sidebar_branding()


st.title("📊 Management Dashboard Εισακτέων ΔΙ.ΠΑ.Ε.")

st.markdown("""
Η σελίδα παρουσιάζει συνοπτική διοικητική εικόνα των εισακτέων του ΔΙ.ΠΑ.Ε.,
με έμφαση στη συνολική εικόνα του Ιδρύματος και στη βασική κατηγορία
**ΓΕΛ Ημερήσια**.

**Μεθοδολογικοί κανόνες:**

- Η συνολική εικόνα υπολογίζεται από **όλες τις κατηγορίες εισαγωγής**.
- Οι **Συνολικές Θέσεις** υπολογίζονται από τις **Αρχικές Θέσεις**.
- Η **Συνολική Κάλυψη** υπολογίζεται ως: Επιτυχόντες όλων των κατηγοριών / Συνολικές Θέσεις.
- Η **Κάλυψη ΓΕΛ Ημερήσια** υπολογίζεται μόνο για τη βασική κατηγορία ΓΕΛ Ημερήσια.
- Για τη ΓΕΛ Ημερήσια χρησιμοποιούνται οι θέσεις της συγκεκριμένης κατηγορίας.
- Η **Βάση Προγράμματος** είναι η **Βάση ΓΕΛ Ημερήσια**.
- Δεν εμφανίζονται τελικές θέσεις ή φαινόμενη μεταβολή θέσεων.
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

    Για τη ΓΕΛ Ημερήσια χρησιμοποιούνται οι final_positions,
    γιατί σε αυτή την κατηγορία αποτυπώνονται οι θέσεις κατόπιν μεταφοράς.
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

    summary["total_coverage"] = (
        summary["total_coverage"]
        .fillna(0)
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

        summary[col] = (
            summary[col]
            .fillna(0)
        )

    return summary


# ---------------------------------------------------------
# Μορφοποίηση πινάκων
# ---------------------------------------------------------

def format_numeric_display(display):
    integer_columns = [
        "Συνολικές Θέσεις",
        "Επιτυχόντες",
        "Κενές Θέσεις",
        "ΓΕΛ Ημερήσια Θέσεις",
        "ΓΕΛ Ημερήσια Επιτυχόντες",
        "Κενές ΓΕΛ Ημερήσια",
        "Βάση ΓΕΛ Ημ.",
        "Πρώτος ΓΕΛ Ημ.",
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


def top_base_table(df):
    table = (
        df[df["gel_day_base_score"] > 0]
        .sort_values("gel_day_base_score", ascending=False)
        .head(5)
    )

    display = table[
        [
            "department_name_clean",
            "school",
            "city",
            "gel_day_base_score",
            "gel_day_first_score",
            "gel_day_positions",
            "gel_day_admitted",
            "gel_day_coverage",
        ]
    ].copy()

    display = display.rename(
        columns={
            "department_name_clean": "Προπτυχιακό Πρόγραμμα",
            "school": "Σχολή",
            "city": "Πόλη",
            "gel_day_base_score": "Βάση ΓΕΛ Ημ.",
            "gel_day_first_score": "Πρώτος ΓΕΛ Ημ.",
            "gel_day_positions": "ΓΕΛ Ημερήσια Θέσεις",
            "gel_day_admitted": "ΓΕΛ Ημερήσια Επιτυχόντες",
            "gel_day_coverage": "Κάλυψη ΓΕΛ Ημ. %",
        }
    )

    return format_numeric_display(display)


def top_gel_admitted_table(df):
    table = (
        df.sort_values("gel_day_admitted", ascending=False)
        .head(5)
    )

    display = table[
        [
            "department_name_clean",
            "school",
            "city",
            "gel_day_admitted",
            "gel_day_positions",
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
            "gel_day_admitted": "ΓΕΛ Ημερήσια Επιτυχόντες",
            "gel_day_positions": "ΓΕΛ Ημερήσια Θέσεις",
            "gel_day_empty": "Κενές ΓΕΛ Ημερήσια",
            "gel_day_coverage": "Κάλυψη ΓΕΛ Ημ. %",
            "gel_day_base_score": "Βάση ΓΕΛ Ημ.",
        }
    )

    return format_numeric_display(display)


def top_gel_empty_table(df):
    table = (
        df.sort_values("gel_day_empty", ascending=False)
        .head(5)
    )

    display = table[
        [
            "department_name_clean",
            "school",
            "city",
            "gel_day_empty",
            "gel_day_positions",
            "gel_day_admitted",
            "gel_day_coverage",
            "gel_day_base_score",
        ]
    ].copy()

    display = display.rename(
        columns={
            "department_name_clean": "Προπτυχιακό Πρόγραμμα",
            "school": "Σχολή",
            "city": "Πόλη",
            "gel_day_empty": "Κενές ΓΕΛ Ημερήσια",
            "gel_day_positions": "ΓΕΛ Ημερήσια Θέσεις",
            "gel_day_admitted": "ΓΕΛ Ημερήσια Επιτυχόντες",
            "gel_day_coverage": "Κάλυψη ΓΕΛ Ημ. %",
            "gel_day_base_score": "Βάση ΓΕΛ Ημ.",
        }
    )

    return format_numeric_display(display)


def top_gel_positions_table(df):
    table = (
        df.sort_values("gel_day_positions", ascending=False)
        .head(5)
    )

    display = table[
        [
            "department_name_clean",
            "school",
            "city",
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
            "gel_day_positions": "ΓΕΛ Ημερήσια Θέσεις",
            "gel_day_admitted": "ΓΕΛ Ημερήσια Επιτυχόντες",
            "gel_day_empty": "Κενές ΓΕΛ Ημερήσια",
            "gel_day_coverage": "Κάλυψη ΓΕΛ Ημ. %",
            "gel_day_base_score": "Βάση ΓΕΛ Ημ.",
        }
    )

    return format_numeric_display(display)


def lowest_gel_coverage_table(df):
    table = (
        df[df["gel_day_positions"] > 0]
        .sort_values("gel_day_coverage", ascending=True)
        .head(5)
    )

    display = table[
        [
            "department_name_clean",
            "school",
            "city",
            "gel_day_coverage",
            "gel_day_positions",
            "gel_day_admitted",
            "gel_day_empty",
            "gel_day_base_score",
        ]
    ].copy()

    display = display.rename(
        columns={
            "department_name_clean": "Προπτυχιακό Πρόγραμμα",
            "school": "Σχολή",
            "city": "Πόλη",
            "gel_day_coverage": "Κάλυψη ΓΕΛ Ημ. %",
            "gel_day_positions": "ΓΕΛ Ημερήσια Θέσεις",
            "gel_day_admitted": "ΓΕΛ Ημερήσια Επιτυχόντες",
            "gel_day_empty": "Κενές ΓΕΛ Ημερήσια",
            "gel_day_base_score": "Βάση ΓΕΛ Ημ.",
        }
    )

    return format_numeric_display(display)


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

def create_institution_positions_chart(total_positions, total_admitted, gel_positions, gel_admitted):
    chart_df = pd.DataFrame(
        {
            "Κατηγορία Δείκτη": [
                "Σύνολο όλων των κατηγοριών",
                "Σύνολο όλων των κατηγοριών",
                "ΓΕΛ Ημερήσια",
                "ΓΕΛ Ημερήσια",
            ],
            "Δείκτης": [
                "Θέσεις",
                "Επιτυχόντες",
                "Θέσεις",
                "Επιτυχόντες",
            ],
            "Πλήθος": [
                total_positions,
                total_admitted,
                gel_positions,
                gel_admitted,
            ],
        }
    )

    fig = px.bar(
        chart_df,
        x="Κατηγορία Δείκτη",
        y="Πλήθος",
        color="Δείκτης",
        barmode="group",
        text="Πλήθος",
        title="Θέσεις και επιτυχόντες Ιδρύματος: σύνολο και ΓΕΛ Ημερήσια"
    )

    fig.update_traces(
        texttemplate="%{text:.0f}",
        textposition="outside",
        cliponaxis=False
    )

    max_value = (
        chart_df["Πλήθος"].max()
        if not chart_df.empty
        else 0
    )

    fig.update_layout(
        height=520,
        xaxis_title="",
        yaxis_title="Πλήθος",
        yaxis_range=[0, max(10, max_value * 1.20)],
        legend_title="",
        margin=dict(l=20, r=80, t=80, b=80)
    )

    return fig


def apply_horizontal_chart_layout(fig, title, xaxis_title):
    fig.update_layout(
        title=title,
        xaxis_title=xaxis_title,
        yaxis_title="",
        height=560,
        margin=dict(l=20, r=180, t=80, b=40),
        uniformtext_minsize=8,
        uniformtext_mode="show"
    )

    fig.update_yaxes(automargin=True)
    fig.update_xaxes(automargin=True)

    return fig


def create_top_base_chart(df):
    chart_df = (
        df[df["gel_day_base_score"] > 0]
        .sort_values("gel_day_base_score", ascending=True)
        .tail(5)
        .copy()
    )

    max_value = chart_df["gel_day_base_score"].max() if not chart_df.empty else 0

    fig = px.bar(
        chart_df,
        x="gel_day_base_score",
        y="department_name_clean",
        orientation="h",
        text="gel_day_base_score",
        title="Top 5 υψηλότερων βάσεων ΓΕΛ Ημερήσια"
    )

    fig.update_traces(
        texttemplate="%{text:.0f}",
        textposition="outside",
        cliponaxis=False
    )

    fig.update_layout(
        xaxis_range=[0, max(20000, max_value * 1.18)]
    )

    return apply_horizontal_chart_layout(
        fig,
        "Top 5 υψηλότερων βάσεων ΓΕΛ Ημερήσια",
        "Βάση ΓΕΛ Ημερήσια"
    )


def create_top_gel_admitted_chart(df):
    chart_df = (
        df.sort_values("gel_day_admitted", ascending=True)
        .tail(5)
        .copy()
    )

    max_value = chart_df["gel_day_admitted"].max() if not chart_df.empty else 0

    fig = px.bar(
        chart_df,
        x="gel_day_admitted",
        y="department_name_clean",
        orientation="h",
        text="gel_day_admitted",
        title="Top 5 περισσότερων επιτυχόντων ΓΕΛ Ημερήσια"
    )

    fig.update_traces(
        texttemplate="%{text:.0f}",
        textposition="outside",
        cliponaxis=False
    )

    fig.update_layout(
        xaxis_range=[0, max(10, max_value * 1.25)]
    )

    return apply_horizontal_chart_layout(
        fig,
        "Top 5 περισσότερων επιτυχόντων ΓΕΛ Ημερήσια",
        "Επιτυχόντες ΓΕΛ Ημερήσια"
    )


def create_top_gel_empty_chart(df):
    chart_df = (
        df.sort_values("gel_day_empty", ascending=True)
        .tail(5)
        .copy()
    )

    max_value = chart_df["gel_day_empty"].max() if not chart_df.empty else 0

    fig = px.bar(
        chart_df,
        x="gel_day_empty",
        y="department_name_clean",
        orientation="h",
        text="gel_day_empty",
        title="Top 5 περισσότερων κενών θέσεων ΓΕΛ Ημερήσια"
    )

    fig.update_traces(
        texttemplate="%{text:.0f}",
        textposition="outside",
        cliponaxis=False
    )

    fig.update_layout(
        xaxis_range=[0, max(5, max_value * 1.25)],
        xaxis=dict(dtick=1)
    )

    return apply_horizontal_chart_layout(
        fig,
        "Top 5 περισσότερων κενών θέσεων ΓΕΛ Ημερήσια",
        "Κενές ΓΕΛ Ημερήσια"
    )


def create_top_gel_positions_chart(df):
    chart_df = (
        df.sort_values("gel_day_positions", ascending=True)
        .tail(5)
        .copy()
    )

    max_value = chart_df["gel_day_positions"].max() if not chart_df.empty else 0

    fig = px.bar(
        chart_df,
        x="gel_day_positions",
        y="department_name_clean",
        orientation="h",
        text="gel_day_positions",
        title="Top 5 περισσότερων θέσεων ΓΕΛ Ημερήσια"
    )

    fig.update_traces(
        texttemplate="%{text:.0f}",
        textposition="outside",
        cliponaxis=False
    )

    fig.update_layout(
        xaxis_range=[0, max(10, max_value * 1.25)]
    )

    return apply_horizontal_chart_layout(
        fig,
        "Top 5 περισσότερων θέσεων ΓΕΛ Ημερήσια",
        "Θέσεις ΓΕΛ Ημερήσια"
    )


def create_lowest_gel_coverage_chart(df):
    chart_df = (
        df[df["gel_day_positions"] > 0]
        .sort_values("gel_day_coverage", ascending=True)
        .head(5)
        .sort_values("gel_day_coverage", ascending=True)
        .copy()
    )

    fig = px.bar(
        chart_df,
        x="gel_day_coverage",
        y="department_name_clean",
        orientation="h",
        text="gel_day_coverage",
        title="Top 5 χαμηλότερης κάλυψης ΓΕΛ Ημερήσια"
    )

    fig.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",
        cliponaxis=False
    )

    fig.update_layout(
        xaxis_range=[0, 115]
    )

    return apply_horizontal_chart_layout(
        fig,
        "Top 5 χαμηλότερης κάλυψης ΓΕΛ Ημερήσια",
        "Κάλυψη ΓΕΛ Ημερήσια %"
    )


def get_top5_content(selection, department_summary):
    """
    Επιστρέφει τίτλο, πίνακα, γράφημα και υποσημείωση για την επιλεγμένη ανάλυση.
    """

    if selection == "Top 5 υψηλότερων βάσεων ΓΕΛ Ημερήσια":
        return (
            "Top 5 υψηλότερων βάσεων ΓΕΛ Ημερήσια",
            top_base_table(department_summary),
            create_top_base_chart(department_summary),
            "Ο πίνακας και το γράφημα βασίζονται στη βάση της ΓΕΛ Ημερήσιας."
        )

    if selection == "Top 5 περισσότερων επιτυχόντων ΓΕΛ Ημερήσια":
        return (
            "Top 5 περισσότερων επιτυχόντων ΓΕΛ Ημερήσια",
            top_gel_admitted_table(department_summary),
            create_top_gel_admitted_chart(department_summary),
            "Ο πίνακας και το γράφημα βασίζονται στους επιτυχόντες της ΓΕΛ Ημερήσιας."
        )

    if selection == "Top 5 περισσότερων κενών θέσεων ΓΕΛ Ημερήσια":
        return (
            "Top 5 περισσότερων κενών θέσεων ΓΕΛ Ημερήσια",
            top_gel_empty_table(department_summary),
            create_top_gel_empty_chart(department_summary),
            "Ο πίνακας και το γράφημα χρησιμοποιούν αποκλειστικά τις θέσεις και τους επιτυχόντες της ΓΕΛ Ημερήσιας."
        )

    if selection == "Top 5 περισσότερων θέσεων ΓΕΛ Ημερήσια":
        return (
            "Top 5 περισσότερων θέσεων ΓΕΛ Ημερήσια",
            top_gel_positions_table(department_summary),
            create_top_gel_positions_chart(department_summary),
            "Ο πίνακας και το γράφημα χρησιμοποιούν αποκλειστικά τις θέσεις της ΓΕΛ Ημερήσιας."
        )

    return (
        "Top 5 χαμηλότερης κάλυψης ΓΕΛ Ημερήσια",
        lowest_gel_coverage_table(department_summary),
        create_lowest_gel_coverage_chart(department_summary),
        "Ο πίνακας και το γράφημα χρησιμοποιούν αποκλειστικά την κάλυψη της ΓΕΛ Ημερήσιας και όχι τη συνολική κάλυψη όλων των κατηγοριών."
    )


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
    total_empty = safe_int(department_summary["empty_positions"].sum())

    total_coverage = (
        total_admitted / total_positions * 100
        if total_positions > 0
        else 0
    )

    gel_day_positions = safe_int(department_summary["gel_day_positions"].sum())
    gel_day_admitted = safe_int(department_summary["gel_day_admitted"].sum())
    gel_day_empty = safe_int(department_summary["gel_day_empty"].sum())

    gel_day_coverage = (
        gel_day_admitted / gel_day_positions * 100
        if gel_day_positions > 0
        else 0
    )

    # ---------------------------------------------------------
    # Συνολική εικόνα Ιδρύματος
    # ---------------------------------------------------------

    st.subheader(f"Συνολική εικόνα Ιδρύματος {selected_year}")

    info1, info2, info3, info4 = st.columns(4)

    with info1:
        st.metric(
            "Ενεργά Προπτυχιακά Προγράμματα",
            total_programs
        )

    with info2:
        st.metric(
            "Σχολές",
            total_schools
        )

    with info3:
        st.metric(
            "Πόλεις",
            total_cities
        )

    with info4:
        st.empty()

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
            total_empty
        )

    with kpi4:
        st.metric(
            "Συνολική Κάλυψη",
            f"{total_coverage:.2f}%"
        )

    gel1, gel2, gel3, gel4 = st.columns(4)

    with gel1:
        st.metric(
            "ΓΕΛ Ημερ. Θέσεις",
            gel_day_positions
        )

    with gel2:
        st.metric(
            "ΓΕΛ Ημερ. Επιτυχόντες",
            gel_day_admitted
        )

    with gel3:
        st.metric(
            "Κενές ΓΕΛ Ημερ.",
            gel_day_empty
        )

    with gel4:
        st.metric(
            "Κάλυψη ΓΕΛ Ημερ.",
            f"{gel_day_coverage:.2f}%"
        )

    st.caption(
        "Η δεύτερη σειρά αφορά όλες τις κατηγορίες εισαγωγής. "
        "Η τρίτη σειρά αφορά αποκλειστικά τη ΓΕΛ Ημερήσια."
    )

    st.divider()

    # ---------------------------------------------------------
    # Γράφημα Ιδρύματος
    # ---------------------------------------------------------

    st.subheader("Θέσεις και επιτυχόντες Ιδρύματος")

    fig = create_institution_positions_chart(
        total_positions=total_positions,
        total_admitted=total_admitted,
        gel_positions=gel_day_positions,
        gel_admitted=gel_day_admitted
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.caption(
        "Το γράφημα συγκρίνει τις θέσεις και τους επιτυχόντες σε επίπεδο Ιδρύματος "
        "για όλες τις κατηγορίες εισαγωγής και για τη ΓΕΛ Ημερήσια."
    )

    st.divider()

    # ---------------------------------------------------------
    # Top 5 με επιλογή
    # ---------------------------------------------------------

    st.subheader("Top-5 δείκτες ΓΕΛ Ημερήσια")

    top5_selection = st.selectbox(
        "Επιλέξτε είδος Top-5",
        [
            "Top 5 υψηλότερων βάσεων ΓΕΛ Ημερήσια",
            "Top 5 περισσότερων επιτυχόντων ΓΕΛ Ημερήσια",
            "Top 5 περισσότερων κενών θέσεων ΓΕΛ Ημερήσια",
            "Top 5 περισσότερων θέσεων ΓΕΛ Ημερήσια",
            "Top 5 χαμηλότερης κάλυψης ΓΕΛ Ημερήσια",
        ]
    )

    title, table, fig, note = get_top5_content(
        selection=top5_selection,
        department_summary=department_summary
    )

    st.markdown(f"### {title}")

    st.dataframe(
        style_table(table),
        use_container_width=True,
        hide_index=True
    )

    st.caption(note)

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.caption(note)

except Exception as e:
    st.error("Υπήρξε πρόβλημα κατά την προβολή του Management Dashboard.")
    st.exception(e)