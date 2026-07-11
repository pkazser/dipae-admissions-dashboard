import io
from datetime import datetime

import pandas as pd
import streamlit as st
from docx import Document
from docx.shared import Pt

from modules.database_manager import load_admissions_with_departments


st.set_page_config(
    page_title="Έκθεση Διοίκησης | ΔΙΠΑΕ",
    page_icon="📄",
    layout="wide"
)


st.title("📄 Έκθεση Αναφοράς προς Διοίκηση")

st.markdown("""
Η σελίδα δημιουργεί αυτόματα αρχείο **Word (.docx)** με συνοπτική διοικητική
αναφορά για τους εισακτέους του ΔΙ.ΠΑ.Ε. για το επιλεγμένο έτος.

Η αναφορά περιλαμβάνει:

- συνολική εικόνα Ιδρύματος,
- κατηγορίες κάλυψης προγραμμάτων,
- βασικά συμπεράσματα,
- Top-5 πίνακες,
- ανάλυση ανά Σχολή,
- ανάλυση ανά Πόλη,
- αναλυτικό πίνακα προπτυχιακών προγραμμάτων,
- μεθοδολογικές σημειώσεις.
""")

st.divider()


# ---------------------------------------------------------
# Βοηθητικές συναρτήσεις υπολογισμών
# ---------------------------------------------------------

def get_gel_day_data(df_year):
    """
    Επιστρέφει στοιχεία ΓΕΛ Ημερήσια ανά πρόγραμμα.

    Για τις θέσεις ΓΕΛ Ημερήσια χρησιμοποιούμε τις τελικές θέσεις της συγκεκριμένης
    κατηγορίας, γιατί εκεί αποτυπώνονται οι τυχόν μεταφορές θέσεων προς τη ΓΕΛ Ημερήσια.
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
                "gel_day_coverage",
                "gel_day_first_score",
                "gel_day_base_score",
            ]
        )

    df_gel["gel_day_positions"] = (
        df_gel["final_positions"]
        .fillna(df_gel["initial_positions"])
    )

    df_gel["gel_day_admitted"] = df_gel["admitted"]

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
    Δημιουργεί σύνοψη ανά ενεργό προπτυχιακό πρόγραμμα.
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

    gel_data = get_gel_day_data(df_year)

    summary = summary.merge(
        gel_data,
        on="department_code",
        how="left"
    )

    return summary


def build_group_summary(department_summary, group_field):
    """
    Δημιουργεί σύνοψη ανά Σχολή ή Πόλη.
    """

    summary = (
        department_summary
        .groupby(group_field, as_index=False)
        .agg(
            programs=("department_code", "nunique"),
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


def classify_coverage(row):
    """
    Κατηγοριοποιεί την κάλυψη κάθε προγράμματος.

    Κανόνες:
    1. Πλήρης συνολική κάλυψη: συνολική κάλυψη >= 100%.
    2. Πλήρης κάλυψη ΓΕΛ Ημερήσια με μικρά κενά:
       ΓΕΛ Ημερήσια >= 100%, συνολική κάλυψη από 95% έως κάτω από 100%.
    3. Μη πλήρης κάλυψη ΓΕΛ Ημερήσια:
       ΓΕΛ Ημερήσια κάτω από 100%.
    4. Χωρίς διαθέσιμα στοιχεία ΓΕΛ Ημερήσια.
    """

    total_coverage = row.get("coverage")
    gel_coverage = row.get("gel_day_coverage")

    if pd.isna(gel_coverage):
        return "Χωρίς στοιχεία ΓΕΛ Ημερήσια"

    if total_coverage >= 99.999:
        return "Πλήρης συνολική κάλυψη"

    if gel_coverage >= 99.999 and total_coverage >= 95:
        return "Πλήρης κάλυψη ΓΕΛ Ημερήσια με μικρά κενά*"

    if gel_coverage >= 99.999:
        return "Πλήρης κάλυψη ΓΕΛ Ημερήσια με σημαντικά κενά*"

    return "Μη πλήρης κάλυψη ΓΕΛ Ημερήσια"


def prepare_report_data(df_year):
    """
    Ετοιμάζει όλα τα δεδομένα που θα χρησιμοποιηθούν στην αναφορά.
    """

    department_summary = build_department_summary(df_year)

    department_summary["coverage_category"] = department_summary.apply(
        classify_coverage,
        axis=1
    )

    school_summary = build_group_summary(
        department_summary,
        "school"
    )

    city_summary = build_group_summary(
        department_summary,
        "city"
    )

    total_programs = int(department_summary["department_code"].nunique())
    total_positions = int(department_summary["total_positions"].sum())
    total_admitted = int(department_summary["total_admitted"].sum())
    total_empty = int(department_summary["empty_positions"].sum())

    total_coverage = (
        total_admitted / total_positions * 100
        if total_positions > 0
        else 0
    )

    coverage_counts = (
        department_summary["coverage_category"]
        .value_counts()
        .reset_index()
    )

    coverage_counts.columns = [
        "Κατηγορία Κάλυψης",
        "Πλήθος Προγραμμάτων",
    ]

    return {
        "department_summary": department_summary,
        "school_summary": school_summary,
        "city_summary": city_summary,
        "coverage_counts": coverage_counts,
        "total_programs": total_programs,
        "total_positions": total_positions,
        "total_admitted": total_admitted,
        "total_empty": total_empty,
        "total_coverage": total_coverage,
    }


# ---------------------------------------------------------
# Μορφοποίηση πινάκων για προβολή και Word
# ---------------------------------------------------------

def format_int(value):
    try:
        return f"{int(round(float(value)))}"
    except Exception:
        return "—"


def format_percent(value):
    try:
        return f"{float(value):.1f}%"
    except Exception:
        return "—"


def format_score(value):
    try:
        return f"{int(round(float(value)))}"
    except Exception:
        return "—"


def format_top_base_table(df):
    display = df[
        [
            "department_name_clean",
            "gel_day_base_score",
        ]
    ].copy()

    display = display.rename(
        columns={
            "department_name_clean": "Προπτυχιακό Πρόγραμμα",
            "gel_day_base_score": "Βάση ΓΕΛ Ημ.",
        }
    )

    display["Βάση ΓΕΛ Ημ."] = display["Βάση ΓΕΛ Ημ."].apply(format_score)

    return display


def format_top_admitted_table(df):
    display = df[
        [
            "department_name_clean",
            "total_admitted",
        ]
    ].copy()

    display = display.rename(
        columns={
            "department_name_clean": "Προπτυχιακό Πρόγραμμα",
            "total_admitted": "Επιτυχόντες",
        }
    )

    display["Επιτυχόντες"] = display["Επιτυχόντες"].apply(format_int)

    return display


def format_top_empty_table(df):
    display = df[
        [
            "department_name_clean",
            "empty_positions",
        ]
    ].copy()

    display = display.rename(
        columns={
            "department_name_clean": "Προπτυχιακό Πρόγραμμα",
            "empty_positions": "Κενές Θέσεις",
        }
    )

    display["Κενές Θέσεις"] = display["Κενές Θέσεις"].apply(format_int)

    return display


def format_low_coverage_table(df):
    display = df[
        [
            "department_name_clean",
            "coverage",
        ]
    ].copy()

    display = display.rename(
        columns={
            "department_name_clean": "Προπτυχιακό Πρόγραμμα",
            "coverage": "Συνολική Κάλυψη",
        }
    )

    display["Συνολική Κάλυψη"] = display["Συνολική Κάλυψη"].apply(format_percent)

    return display


def format_group_table(df, group_field, group_label):
    display = df[
        [
            group_field,
            "programs",
            "total_positions",
            "total_admitted",
            "empty_positions",
            "coverage",
        ]
    ].copy()

    display = display.rename(
        columns={
            group_field: group_label,
            "programs": "Προπτυχιακά Προγράμματα",
            "total_positions": "Συνολικές Θέσεις",
            "total_admitted": "Επιτυχόντες",
            "empty_positions": "Κενές Θέσεις",
            "coverage": "Κάλυψη %",
        }
    )

    for col in [
        "Προπτυχιακά Προγράμματα",
        "Συνολικές Θέσεις",
        "Επιτυχόντες",
        "Κενές Θέσεις",
    ]:
        display[col] = display[col].apply(format_int)

    display["Κάλυψη %"] = display["Κάλυψη %"].apply(format_percent)

    return display


def format_department_table(df):
    display = df[
        [
            "department_name_clean",
            "school",
            "city",
            "total_positions",
            "total_admitted",
            "empty_positions",
            "coverage",
            "gel_day_coverage",
            "gel_day_base_score",
            "coverage_category",
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
            "coverage": "Συνολική Κάλυψη",
            "gel_day_coverage": "Κάλυψη ΓΕΛ Ημ.",
            "gel_day_base_score": "Βάση ΓΕΛ Ημ.",
            "coverage_category": "Κατηγορία Κάλυψης",
        }
    )

    for col in [
        "Συνολικές Θέσεις",
        "Επιτυχόντες",
        "Κενές Θέσεις",
    ]:
        display[col] = display[col].apply(format_int)

    for col in [
        "Συνολική Κάλυψη",
        "Κάλυψη ΓΕΛ Ημ.",
    ]:
        display[col] = display[col].apply(format_percent)

    display["Βάση ΓΕΛ Ημ."] = display["Βάση ΓΕΛ Ημ."].apply(format_score)

    return display


def format_coverage_counts_table(df):
    display = df.copy()
    display["Πλήθος Προγραμμάτων"] = display["Πλήθος Προγραμμάτων"].apply(format_int)
    return display


# ---------------------------------------------------------
# Δημιουργία Word
# ---------------------------------------------------------

def add_paragraph(document, text, bold=False):
    paragraph = document.add_paragraph()
    run = paragraph.add_run(text)
    run.bold = bold
    run.font.size = Pt(11)
    return paragraph


def add_dataframe_table(document, df):
    """
    Προσθέτει pandas DataFrame ως πίνακα σε Word.
    """

    if df.empty:
        add_paragraph(document, "Δεν υπάρχουν διαθέσιμα δεδομένα.")
        return

    table = document.add_table(
        rows=1,
        cols=len(df.columns)
    )

    table.style = "Table Grid"

    header_cells = table.rows[0].cells

    for idx, column_name in enumerate(df.columns):
        header_cells[idx].text = str(column_name)

    for _, row in df.iterrows():
        row_cells = table.add_row().cells

        for idx, value in enumerate(row):
            row_cells[idx].text = str(value)

    document.add_paragraph("")


def add_basic_conclusions(document, report_data, year):
    """
    Προσθέτει αυτόματα βασικά συμπεράσματα.
    """

    department_summary = report_data["department_summary"]
    school_summary = report_data["school_summary"]
    city_summary = report_data["city_summary"]

    top_base_row = (
        department_summary
        .dropna(subset=["gel_day_base_score"])
        .sort_values("gel_day_base_score", ascending=False)
        .head(1)
    )

    top_empty_row = (
        department_summary
        .sort_values("empty_positions", ascending=False)
        .head(1)
    )

    low_coverage_row = (
        department_summary
        .sort_values("coverage", ascending=True)
        .head(1)
    )

    best_school_row = (
        school_summary
        .sort_values("coverage", ascending=False)
        .head(1)
    )

    best_city_row = (
        city_summary
        .sort_values("coverage", ascending=False)
        .head(1)
    )

    add_paragraph(
        document,
        f"Για το έτος {year}, το ΔΙ.ΠΑ.Ε. διαθέτει "
        f"{report_data['total_programs']} ενεργά προπτυχιακά προγράμματα σπουδών "
        f"με συνολικά {report_data['total_positions']} θέσεις."
    )

    add_paragraph(
        document,
        f"Οι επιτυχόντες ανέρχονται σε {report_data['total_admitted']}, "
        f"ενώ οι κενές θέσεις ανέρχονται σε {report_data['total_empty']}. "
        f"Η συνολική κάλυψη του Ιδρύματος είναι {report_data['total_coverage']:.1f}%."
    )

    if not top_base_row.empty:
        row = top_base_row.iloc[0]
        add_paragraph(
            document,
            f"Η υψηλότερη Βάση ΓΕΛ Ημερήσια καταγράφεται στο πρόγραμμα "
            f"«{row['department_name_clean']}» με {format_score(row['gel_day_base_score'])} μόρια."
        )

    if not top_empty_row.empty:
        row = top_empty_row.iloc[0]
        add_paragraph(
            document,
            f"Οι περισσότερες κενές θέσεις καταγράφονται στο πρόγραμμα "
            f"«{row['department_name_clean']}» με {format_int(row['empty_positions'])} κενές θέσεις."
        )

    if not low_coverage_row.empty:
        row = low_coverage_row.iloc[0]
        add_paragraph(
            document,
            f"Το χαμηλότερο ποσοστό συνολικής κάλυψης εμφανίζεται στο πρόγραμμα "
            f"«{row['department_name_clean']}» με {format_percent(row['coverage'])}."
        )

    if not best_school_row.empty:
        row = best_school_row.iloc[0]
        add_paragraph(
            document,
            f"Σε επίπεδο Σχολής, την υψηλότερη κάλυψη εμφανίζει η "
            f"«{row['school']}» με {format_percent(row['coverage'])}."
        )

    if not best_city_row.empty:
        row = best_city_row.iloc[0]
        add_paragraph(
            document,
            f"Σε επίπεδο Πόλης, την υψηλότερη κάλυψη εμφανίζει η πόλη "
            f"«{row['city']}» με {format_percent(row['coverage'])}."
        )


def create_management_report_docx(report_data, year):
    """
    Δημιουργεί Word αναφορά προς διοίκηση και επιστρέφει bytes.
    """

    document = Document()

    document.add_heading(
        "Έκθεση Ανάλυσης Εισακτέων ΔΙ.ΠΑ.Ε.",
        level=0
    )

    add_paragraph(
        document,
        f"Έτος αναφοράς: {year}",
        bold=True
    )

    add_paragraph(
        document,
        f"Ημερομηνία δημιουργίας: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )

    add_paragraph(
        document,
        "Η παρούσα έκθεση δημιουργήθηκε αυτόματα από την Πλατφόρμα Ανάλυσης "
        "Εισακτέων ΔΙ.ΠΑ.Ε. και αποτυπώνει τη συνολική εικόνα των ενεργών "
        "προπτυχιακών προγραμμάτων σπουδών."
    )

    document.add_heading("1. Συνοπτική εικόνα Ιδρύματος", level=1)

    summary_df = pd.DataFrame(
        {
            "Δείκτης": [
                "Ενεργά Προπτυχιακά Προγράμματα",
                "Συνολικές Θέσεις",
                "Επιτυχόντες",
                "Κενές Θέσεις",
                "Συνολική Κάλυψη",
            ],
            "Τιμή": [
                format_int(report_data["total_programs"]),
                format_int(report_data["total_positions"]),
                format_int(report_data["total_admitted"]),
                format_int(report_data["total_empty"]),
                format_percent(report_data["total_coverage"]),
            ],
        }
    )

    add_dataframe_table(document, summary_df)

    document.add_heading("2. Κατηγορίες κάλυψης προγραμμάτων", level=1)

    coverage_counts_display = format_coverage_counts_table(
        report_data["coverage_counts"]
    )

    add_dataframe_table(document, coverage_counts_display)

    add_paragraph(
        document,
        "* Η πλήρης κάλυψη ΓΕΛ Ημερήσια σημαίνει ότι το πρόγραμμα κάλυψε το 100% "
        "των θέσεων στη βασική κατηγορία εισαγωγής, παρότι ενδέχεται να εμφανίζει "
        "κενά σε λοιπές κατηγορίες."
    )

    add_paragraph(
        document,
        "Ως «μικρά κενά» θεωρείται η περίπτωση όπου η συνολική κάλυψη είναι "
        "τουλάχιστον 95%, αλλά μικρότερη από 100%."
    )

    document.add_heading("3. Βασικά συμπεράσματα", level=1)

    add_basic_conclusions(
        document=document,
        report_data=report_data,
        year=year
    )

    department_summary = report_data["department_summary"]

    document.add_heading("4. Top-5 υψηλότερες βάσεις ΓΕΛ Ημερήσια", level=1)

    top_base = (
        department_summary
        .dropna(subset=["gel_day_base_score"])
        .sort_values("gel_day_base_score", ascending=False)
        .head(5)
    )

    add_dataframe_table(
        document,
        format_top_base_table(top_base)
    )

    document.add_heading("5. Top-5 περισσότερων επιτυχόντων", level=1)

    top_admitted = (
        department_summary
        .sort_values("total_admitted", ascending=False)
        .head(5)
    )

    add_dataframe_table(
        document,
        format_top_admitted_table(top_admitted)
    )

    document.add_heading("6. Top-5 περισσότερων κενών θέσεων", level=1)

    top_empty = (
        department_summary
        .sort_values("empty_positions", ascending=False)
        .head(5)
    )

    add_dataframe_table(
        document,
        format_top_empty_table(top_empty)
    )

    document.add_heading("7. Top-5 χαμηλότερης συνολικής κάλυψης", level=1)

    low_coverage = (
        department_summary
        .sort_values("coverage", ascending=True)
        .head(5)
    )

    add_dataframe_table(
        document,
        format_low_coverage_table(low_coverage)
    )

    document.add_heading("8. Ανάλυση ανά Σχολή", level=1)

    school_display = format_group_table(
        report_data["school_summary"].sort_values("coverage", ascending=False),
        group_field="school",
        group_label="Σχολή"
    )

    add_dataframe_table(document, school_display)

    document.add_heading("9. Ανάλυση ανά Πόλη", level=1)

    city_display = format_group_table(
        report_data["city_summary"].sort_values("coverage", ascending=False),
        group_field="city",
        group_label="Πόλη"
    )

    add_dataframe_table(document, city_display)

    document.add_heading("10. Αναλυτικός πίνακας προπτυχιακών προγραμμάτων", level=1)

    department_display = format_department_table(
        department_summary.sort_values(
            "gel_day_base_score",
            ascending=False,
            na_position="last"
        )
    )

    add_dataframe_table(document, department_display)

    document.add_heading("11. Μεθοδολογικές σημειώσεις", level=1)

    methodology_points = [
        "Η ανάλυση γίνεται για όλες τις κατηγορίες εισαγωγής.",
        "Οι Συνολικές Θέσεις υπολογίζονται από τις Αρχικές Θέσεις όλων των κατηγοριών.",
        "Η Συνολική Κάλυψη υπολογίζεται ως Επιτυχόντες / Συνολικές Θέσεις.",
        "Η Βάση Προγράμματος αντιστοιχεί στη Βάση ΓΕΛ Ημερήσια.",
        "Για τις θέσεις της ΓΕΛ Ημερήσια λαμβάνονται υπόψη οι θέσεις μετά τις τυχόν μεταφορές προς τη ΓΕΛ Ημερήσια.",
        "Δεν εμφανίζεται άθροισμα τελικών θέσεων.",
        "Δεν εμφανίζεται φαινόμενη μεταβολή θέσεων.",
        "Δεν χρησιμοποιούνται μέσοι όροι βάσεων σε επίπεδο Σχολής ή Πόλης.",
        "Η διάκριση πλήρους συνολικής κάλυψης και πλήρους κάλυψης ΓΕΛ Ημερήσια γίνεται για πιο δίκαιη διοικητική ερμηνεία των αποτελεσμάτων.",
    ]

    for point in methodology_points:
        document.add_paragraph(
            point,
            style="List Bullet"
        )

    output = io.BytesIO()
    document.save(output)
    output.seek(0)

    return output.getvalue()


# ---------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------

try:
    df = load_admissions_with_departments()

    if df.empty:
        st.warning("Δεν υπάρχουν ακόμη δεδομένα εισακτέων στη βάση.")
        st.stop()

    years = sorted(df["year"].dropna().unique().tolist())

    selected_year = st.selectbox(
        "Έτος αναφοράς",
        years,
        index=len(years) - 1
    )

    df_year = df[df["year"] == selected_year].copy()

    if df_year.empty:
        st.warning("Δεν υπάρχουν δεδομένα για το επιλεγμένο έτος.")
        st.stop()

    report_data = prepare_report_data(df_year)

    st.subheader(f"Προεπισκόπηση αναφοράς {selected_year}")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.metric(
            "Συνολικές Θέσεις",
            report_data["total_positions"]
        )

    with kpi2:
        st.metric(
            "Επιτυχόντες",
            report_data["total_admitted"]
        )

    with kpi3:
        st.metric(
            "Κενές Θέσεις",
            report_data["total_empty"]
        )

    with kpi4:
        st.metric(
            "Συνολική Κάλυψη",
            f"{report_data['total_coverage']:.1f}%"
        )

    st.markdown("### Κατηγορίες κάλυψης")

    st.dataframe(
        format_coverage_counts_table(report_data["coverage_counts"]),
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "* Πλήρης κάλυψη ΓΕΛ Ημερήσια σημαίνει 100% κάλυψη στη βασική κατηγορία "
        "εισαγωγής. Ως μικρά κενά θεωρούμε συνολική κάλυψη τουλάχιστον 95%."
    )

    st.divider()

    st.markdown("### Τι θα περιλαμβάνει το αρχείο Word")

    st.markdown("""
Το αρχείο θα περιλαμβάνει:

1. Συνοπτική εικόνα Ιδρύματος  
2. Κατηγορίες κάλυψης προγραμμάτων  
3. Βασικά συμπεράσματα  
4. Top-5 υψηλότερες βάσεις ΓΕΛ Ημερήσια  
5. Top-5 περισσότερους επιτυχόντες  
6. Top-5 περισσότερες κενές θέσεις  
7. Top-5 χαμηλότερη συνολική κάλυψη  
8. Ανάλυση ανά Σχολή  
9. Ανάλυση ανά Πόλη  
10. Αναλυτικό πίνακα προγραμμάτων  
11. Μεθοδολογικές σημειώσεις  
""")

    docx_bytes = create_management_report_docx(
        report_data=report_data,
        year=selected_year
    )

    st.download_button(
        label="⬇️ Λήψη Word Αναφοράς",
        data=docx_bytes,
        file_name=f"ekthesi_dioikisis_dipae_{selected_year}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

except Exception as e:
    st.error("Υπήρξε πρόβλημα κατά τη δημιουργία της αναφοράς.")
    st.exception(e)