import io

import pandas as pd
import streamlit as st
import plotly.express as px

from modules.database_manager import load_admissions_with_departments


st.set_page_config(
    page_title="Σύγκριση Ετών | ΔΙΠΑΕ",
    page_icon="📈",
    layout="wide"
)


st.title("📈 Σύγκριση Ετών Εισακτέων ΔΙ.ΠΑ.Ε.")

st.markdown("""
Σε αυτή τη σελίδα συγκρίνουμε τα δεδομένα εισακτέων των ενεργών προπτυχιακών
προγραμμάτων σπουδών του ΔΙ.ΠΑ.Ε. μεταξύ δύο ετών.

**Μεθοδολογικοί κανόνες της εφαρμογής:**

- Η σύγκριση γίνεται πάντα για **όλες τις κατηγορίες εισαγωγής**.
- Οι **Συνολικές Θέσεις** υπολογίζονται από τις **Αρχικές Θέσεις**.
- Η **Κάλυψη** υπολογίζεται ως: Επιτυχόντες / Συνολικές Θέσεις.
- Δεν εμφανίζονται τελικές θέσεις ή φαινόμενη μεταβολή θέσεων.
- Δεν χρησιμοποιούνται μέσοι όροι βάσεων ή μέσοι όροι πρώτου υποψηφίου σε επίπεδο Σχολής/Πόλης.
- Η **Βάση ΓΕΛ Ημερήσια** και ο **Πρώτος ΓΕΛ Ημερήσια** χρησιμοποιούνται μόνο σε επίπεδο προπτυχιακού προγράμματος.
""")

st.divider()


def get_gel_day_scores(df_year):
    """
    Επιστρέφει βάση τελευταίου και βαθμό πρώτου από τη ΓΕΛ Ημερήσια ανά πρόγραμμα.
    Χρησιμοποιείται μόνο σε επίπεδο προπτυχιακού προγράμματος.
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
    Δημιουργεί σύνοψη ανά ενεργό προπτυχιακό πρόγραμμα για όλες τις κατηγορίες.

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

    Δεν υπολογίζει μέσους όρους βάσεων ή πρώτων.
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


def compare_department_summaries(old_df, new_df, old_year, new_year):
    """
    Συγκρίνει δύο ετήσιες συνόψεις προγραμμάτων.
    """

    old = old_df.rename(
        columns={
            "total_positions": f"total_positions_{old_year}",
            "total_admitted": f"total_admitted_{old_year}",
            "empty_positions": f"empty_positions_{old_year}",
            "coverage": f"coverage_{old_year}",
            "gel_day_first_score": f"gel_day_first_score_{old_year}",
            "gel_day_base_score": f"gel_day_base_score_{old_year}",
        }
    )

    new = new_df.rename(
        columns={
            "total_positions": f"total_positions_{new_year}",
            "total_admitted": f"total_admitted_{new_year}",
            "empty_positions": f"empty_positions_{new_year}",
            "coverage": f"coverage_{new_year}",
            "gel_day_first_score": f"gel_day_first_score_{new_year}",
            "gel_day_base_score": f"gel_day_base_score_{new_year}",
        }
    )

    comparison = old.merge(
        new,
        on=[
            "department_code",
            "department_name_clean",
            "school",
            "city",
        ],
        how="outer"
    )

    numeric_columns = [
        f"total_positions_{old_year}",
        f"total_positions_{new_year}",
        f"total_admitted_{old_year}",
        f"total_admitted_{new_year}",
        f"empty_positions_{old_year}",
        f"empty_positions_{new_year}",
        f"coverage_{old_year}",
        f"coverage_{new_year}",
        f"gel_day_first_score_{old_year}",
        f"gel_day_first_score_{new_year}",
        f"gel_day_base_score_{old_year}",
        f"gel_day_base_score_{new_year}",
    ]

    for col in numeric_columns:
        if col not in comparison.columns:
            comparison[col] = None

    for col in [
        f"total_positions_{old_year}",
        f"total_positions_{new_year}",
        f"total_admitted_{old_year}",
        f"total_admitted_{new_year}",
        f"empty_positions_{old_year}",
        f"empty_positions_{new_year}",
    ]:
        comparison[col] = comparison[col].fillna(0)

    comparison["diff_total_positions"] = (
        comparison[f"total_positions_{new_year}"]
        - comparison[f"total_positions_{old_year}"]
    )

    comparison["diff_total_admitted"] = (
        comparison[f"total_admitted_{new_year}"]
        - comparison[f"total_admitted_{old_year}"]
    )

    comparison["diff_empty_positions"] = (
        comparison[f"empty_positions_{new_year}"]
        - comparison[f"empty_positions_{old_year}"]
    )

    comparison["diff_coverage"] = (
        comparison[f"coverage_{new_year}"]
        - comparison[f"coverage_{old_year}"]
    )

    comparison["diff_gel_day_first_score"] = (
        comparison[f"gel_day_first_score_{new_year}"]
        - comparison[f"gel_day_first_score_{old_year}"]
    )

    comparison["diff_gel_day_base_score"] = (
        comparison[f"gel_day_base_score_{new_year}"]
        - comparison[f"gel_day_base_score_{old_year}"]
    )

    return comparison


def compare_group_summaries(old_df, new_df, group_field, old_year, new_year):
    """
    Συγκρίνει δύο ετήσιες συνόψεις Σχολών ή Πόλεων.
    Δεν περιλαμβάνει βάσεις.
    """

    old = old_df.rename(
        columns={
            "programs": f"programs_{old_year}",
            "total_positions": f"total_positions_{old_year}",
            "total_admitted": f"total_admitted_{old_year}",
            "empty_positions": f"empty_positions_{old_year}",
            "coverage": f"coverage_{old_year}",
        }
    )

    new = new_df.rename(
        columns={
            "programs": f"programs_{new_year}",
            "total_positions": f"total_positions_{new_year}",
            "total_admitted": f"total_admitted_{new_year}",
            "empty_positions": f"empty_positions_{new_year}",
            "coverage": f"coverage_{new_year}",
        }
    )

    comparison = old.merge(
        new,
        on=group_field,
        how="outer"
    )

    for col in [
        f"programs_{old_year}",
        f"programs_{new_year}",
        f"total_positions_{old_year}",
        f"total_positions_{new_year}",
        f"total_admitted_{old_year}",
        f"total_admitted_{new_year}",
        f"empty_positions_{old_year}",
        f"empty_positions_{new_year}",
    ]:
        if col not in comparison.columns:
            comparison[col] = 0

        comparison[col] = comparison[col].fillna(0)

    for col in [
        f"coverage_{old_year}",
        f"coverage_{new_year}",
    ]:
        if col not in comparison.columns:
            comparison[col] = None

    comparison["diff_programs"] = (
        comparison[f"programs_{new_year}"]
        - comparison[f"programs_{old_year}"]
    )

    comparison["diff_total_positions"] = (
        comparison[f"total_positions_{new_year}"]
        - comparison[f"total_positions_{old_year}"]
    )

    comparison["diff_total_admitted"] = (
        comparison[f"total_admitted_{new_year}"]
        - comparison[f"total_admitted_{old_year}"]
    )

    comparison["diff_empty_positions"] = (
        comparison[f"empty_positions_{new_year}"]
        - comparison[f"empty_positions_{old_year}"]
    )

    comparison["diff_coverage"] = (
        comparison[f"coverage_{new_year}"]
        - comparison[f"coverage_{old_year}"]
    )

    return comparison


def format_department_comparison_table(df, old_year, new_year):
    """
    Μορφοποιεί τον αναλυτικό πίνακα σύγκρισης προγραμμάτων.
    """

    display = df[
        [
            "department_name_clean",
            "school",
            "city",
            f"total_positions_{old_year}",
            f"total_positions_{new_year}",
            "diff_total_positions",
            f"total_admitted_{old_year}",
            f"total_admitted_{new_year}",
            "diff_total_admitted",
            f"empty_positions_{old_year}",
            f"empty_positions_{new_year}",
            "diff_empty_positions",
            f"coverage_{old_year}",
            f"coverage_{new_year}",
            "diff_coverage",
            f"gel_day_first_score_{old_year}",
            f"gel_day_first_score_{new_year}",
            "diff_gel_day_first_score",
            f"gel_day_base_score_{old_year}",
            f"gel_day_base_score_{new_year}",
            "diff_gel_day_base_score",
        ]
    ].copy()

    display = display.rename(
        columns={
            "department_name_clean": "Προπτυχιακό Πρόγραμμα",
            "school": "Σχολή",
            "city": "Πόλη",
            f"total_positions_{old_year}": f"Συνολικές Θέσεις {old_year}",
            f"total_positions_{new_year}": f"Συνολικές Θέσεις {new_year}",
            "diff_total_positions": "Διαφορά Θέσεων",
            f"total_admitted_{old_year}": f"Επιτυχόντες {old_year}",
            f"total_admitted_{new_year}": f"Επιτυχόντες {new_year}",
            "diff_total_admitted": "Διαφορά Επιτυχόντων",
            f"empty_positions_{old_year}": f"Κενές Θέσεις {old_year}",
            f"empty_positions_{new_year}": f"Κενές Θέσεις {new_year}",
            "diff_empty_positions": "Διαφορά Κενών",
            f"coverage_{old_year}": f"Κάλυψη % {old_year}",
            f"coverage_{new_year}": f"Κάλυψη % {new_year}",
            "diff_coverage": "Διαφορά Κάλυψης",
            f"gel_day_first_score_{old_year}": f"Πρώτος ΓΕΛ Ημ. {old_year}",
            f"gel_day_first_score_{new_year}": f"Πρώτος ΓΕΛ Ημ. {new_year}",
            "diff_gel_day_first_score": "Διαφορά Πρώτου ΓΕΛ Ημ.",
            f"gel_day_base_score_{old_year}": f"Βάση ΓΕΛ Ημ. {old_year}",
            f"gel_day_base_score_{new_year}": f"Βάση ΓΕΛ Ημ. {new_year}",
            "diff_gel_day_base_score": "Διαφορά Βάσης ΓΕΛ Ημ.",
        }
    )

    for col in [
        f"Συνολικές Θέσεις {old_year}",
        f"Συνολικές Θέσεις {new_year}",
        "Διαφορά Θέσεων",
        f"Επιτυχόντες {old_year}",
        f"Επιτυχόντες {new_year}",
        "Διαφορά Επιτυχόντων",
        f"Κενές Θέσεις {old_year}",
        f"Κενές Θέσεις {new_year}",
        "Διαφορά Κενών",
    ]:
        display[col] = display[col].fillna(0).round(0).astype(int)

    for col in [
        f"Κάλυψη % {old_year}",
        f"Κάλυψη % {new_year}",
        "Διαφορά Κάλυψης",
    ]:
        display[col] = display[col].round(2)

    for col in [
        f"Πρώτος ΓΕΛ Ημ. {old_year}",
        f"Πρώτος ΓΕΛ Ημ. {new_year}",
        "Διαφορά Πρώτου ΓΕΛ Ημ.",
        f"Βάση ΓΕΛ Ημ. {old_year}",
        f"Βάση ΓΕΛ Ημ. {new_year}",
        "Διαφορά Βάσης ΓΕΛ Ημ.",
    ]:
        display[col] = display[col].fillna(0).round(0).astype(int)

    return display


def format_clean_department_table(df, old_year, new_year):
    """
    Καθαρότερος πίνακας σύγκρισης προγραμμάτων.
    """

    full = format_department_comparison_table(df, old_year, new_year)

    display = full[
        [
            "Προπτυχιακό Πρόγραμμα",
            "Σχολή",
            "Πόλη",
            f"Συνολικές Θέσεις {old_year}",
            f"Συνολικές Θέσεις {new_year}",
            "Διαφορά Θέσεων",
            f"Επιτυχόντες {old_year}",
            f"Επιτυχόντες {new_year}",
            "Διαφορά Επιτυχόντων",
            f"Κάλυψη % {old_year}",
            f"Κάλυψη % {new_year}",
            "Διαφορά Κάλυψης",
            f"Βάση ΓΕΛ Ημ. {old_year}",
            f"Βάση ΓΕΛ Ημ. {new_year}",
            "Διαφορά Βάσης ΓΕΛ Ημ.",
        ]
    ].copy()

    return display


def format_group_comparison_table(df, group_field, group_label, old_year, new_year):
    """
    Μορφοποιεί πίνακα σύγκρισης Σχολής ή Πόλης.
    """

    display = df[
        [
            group_field,
            f"programs_{old_year}",
            f"programs_{new_year}",
            "diff_programs",
            f"total_positions_{old_year}",
            f"total_positions_{new_year}",
            "diff_total_positions",
            f"total_admitted_{old_year}",
            f"total_admitted_{new_year}",
            "diff_total_admitted",
            f"empty_positions_{old_year}",
            f"empty_positions_{new_year}",
            "diff_empty_positions",
            f"coverage_{old_year}",
            f"coverage_{new_year}",
            "diff_coverage",
        ]
    ].copy()

    display = display.rename(
        columns={
            group_field: group_label,
            f"programs_{old_year}": f"Προγράμματα {old_year}",
            f"programs_{new_year}": f"Προγράμματα {new_year}",
            "diff_programs": "Διαφορά Προγραμμάτων",
            f"total_positions_{old_year}": f"Συνολικές Θέσεις {old_year}",
            f"total_positions_{new_year}": f"Συνολικές Θέσεις {new_year}",
            "diff_total_positions": "Διαφορά Θέσεων",
            f"total_admitted_{old_year}": f"Επιτυχόντες {old_year}",
            f"total_admitted_{new_year}": f"Επιτυχόντες {new_year}",
            "diff_total_admitted": "Διαφορά Επιτυχόντων",
            f"empty_positions_{old_year}": f"Κενές Θέσεις {old_year}",
            f"empty_positions_{new_year}": f"Κενές Θέσεις {new_year}",
            "diff_empty_positions": "Διαφορά Κενών",
            f"coverage_{old_year}": f"Κάλυψη % {old_year}",
            f"coverage_{new_year}": f"Κάλυψη % {new_year}",
            "diff_coverage": "Διαφορά Κάλυψης",
        }
    )

    for col in [
        f"Προγράμματα {old_year}",
        f"Προγράμματα {new_year}",
        "Διαφορά Προγραμμάτων",
        f"Συνολικές Θέσεις {old_year}",
        f"Συνολικές Θέσεις {new_year}",
        "Διαφορά Θέσεων",
        f"Επιτυχόντες {old_year}",
        f"Επιτυχόντες {new_year}",
        "Διαφορά Επιτυχόντων",
        f"Κενές Θέσεις {old_year}",
        f"Κενές Θέσεις {new_year}",
        "Διαφορά Κενών",
    ]:
        display[col] = display[col].fillna(0).round(0).astype(int)

    for col in [
        f"Κάλυψη % {old_year}",
        f"Κάλυψη % {new_year}",
        "Διαφορά Κάλυψης",
    ]:
        display[col] = display[col].round(2)

    return display


def highlight_difference(val):
    """
    Χρωματισμός διαφορών.
    Θετική τιμή: πράσινο
    Αρνητική τιμή: κόκκινο
    Μηδέν: γκρι
    """

    try:
        value = float(val)
    except Exception:
        return ""

    if value > 0:
        return "background-color: #d4edda; color: #155724; font-weight: bold;"
    elif value < 0:
        return "background-color: #f8d7da; color: #721c24; font-weight: bold;"
    else:
        return "background-color: #f1f3f5; color: #495057;"


def style_comparison_table(df):
    """
    Styling πινάκων σύγκρισης.

    Όλες οι στήλες κάλυψης και διαφοράς κάλυψης εμφανίζονται με 2 δεκαδικά και %.
    """

    style_obj = df.style

    format_dict = {}

    for col in df.columns:
        if "Κάλυψη %" in col or col == "Διαφορά Κάλυψης":
            format_dict[col] = "{:.2f}%"

    if format_dict:
        style_obj = style_obj.format(format_dict)

    diff_columns = [
        col for col in df.columns
        if col.startswith("Διαφορά")
    ]

    if diff_columns:
        try:
            style_obj = style_obj.map(
                highlight_difference,
                subset=diff_columns
            )
        except AttributeError:
            style_obj = style_obj.applymap(
                highlight_difference,
                subset=diff_columns
            )

    return style_obj


def create_excel_export(
    clean_department_display,
    full_department_display,
    school_display,
    city_display,
    old_year,
    new_year
):
    """
    Δημιουργεί αρχείο Excel με τα αποτελέσματα σύγκρισης.
    """

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        clean_department_display.to_excel(
            writer,
            index=False,
            sheet_name="Ανά Πρόγραμμα"
        )

        full_department_display.to_excel(
            writer,
            index=False,
            sheet_name="Αναλυτικά Προγράμματα"
        )

        school_display.to_excel(
            writer,
            index=False,
            sheet_name="Ανά Σχολή"
        )

        city_display.to_excel(
            writer,
            index=False,
            sheet_name="Ανά Πόλη"
        )

        notes = pd.DataFrame(
            {
                "Σημείωση": [
                    "Η σύγκριση γίνεται για όλες τις κατηγορίες εισαγωγής.",
                    "Οι Συνολικές Θέσεις υπολογίζονται από τις Αρχικές Θέσεις.",
                    "Η Κάλυψη υπολογίζεται ως Επιτυχόντες / Συνολικές Θέσεις.",
                    "Δεν εμφανίζονται τελικές θέσεις ή φαινόμενη μεταβολή θέσεων.",
                    "Δεν υπολογίζονται μέσοι όροι βάσεων σε επίπεδο Σχολής ή Πόλης.",
                    "Η Βάση ΓΕΛ Ημερήσια και ο Πρώτος ΓΕΛ Ημερήσια εμφανίζονται μόνο σε επίπεδο προπτυχιακού προγράμματος.",
                    "Οι βάσεις και τα μόρια πρώτου εμφανίζονται χωρίς δεκαδικά.",
                    "Τα ποσοστά κάλυψης και οι διαφορές κάλυψης εμφανίζονται με δύο δεκαδικά.",
                ]
            }
        )

        notes.to_excel(
            writer,
            index=False,
            sheet_name="Σημειώσεις"
        )

    output.seek(0)
    return output


try:
    df = load_admissions_with_departments()

    if df.empty:
        st.warning("Δεν υπάρχουν ακόμη δεδομένα εισακτέων στη βάση.")
        st.stop()

    years = sorted(df["year"].dropna().unique().tolist())

    if len(years) < 2:
        st.warning("Χρειάζονται τουλάχιστον δύο έτη δεδομένων για σύγκριση.")
        st.stop()

    col_old, col_new = st.columns(2)

    with col_old:
        old_year = st.selectbox(
            "Παλαιότερο έτος",
            years,
            index=max(0, len(years) - 2)
        )

    available_new_years = [
        year for year in years
        if year != old_year
    ]

    default_new_index = (
        available_new_years.index(max(available_new_years))
        if available_new_years
        else 0
    )

    with col_new:
        new_year = st.selectbox(
            "Νεότερο έτος",
            available_new_years,
            index=default_new_index
        )

    if old_year == new_year:
        st.warning("Επίλεξε δύο διαφορετικά έτη.")
        st.stop()

    if old_year > new_year:
        st.info(
            "Έγινε αυτόματη αντιστροφή ώστε το πρώτο έτος να είναι το παλαιότερο "
            "και το δεύτερο το νεότερο."
        )
        old_year, new_year = new_year, old_year

    df_old = df[df["year"] == old_year].copy()
    df_new = df[df["year"] == new_year].copy()

    if df_old.empty or df_new.empty:
        st.warning("Δεν υπάρχουν πλήρη δεδομένα για τα επιλεγμένα έτη.")
        st.stop()

    old_department_summary = build_department_summary(df_old)
    new_department_summary = build_department_summary(df_new)

    old_school_summary = build_group_summary(
        old_department_summary,
        "school"
    )

    new_school_summary = build_group_summary(
        new_department_summary,
        "school"
    )

    old_city_summary = build_group_summary(
        old_department_summary,
        "city"
    )

    new_city_summary = build_group_summary(
        new_department_summary,
        "city"
    )

    department_comparison = compare_department_summaries(
        old_department_summary,
        new_department_summary,
        old_year,
        new_year
    )

    school_comparison = compare_group_summaries(
        old_school_summary,
        new_school_summary,
        "school",
        old_year,
        new_year
    )

    city_comparison = compare_group_summaries(
        old_city_summary,
        new_city_summary,
        "city",
        old_year,
        new_year
    )

    old_total_positions = int(old_department_summary["total_positions"].sum())
    new_total_positions = int(new_department_summary["total_positions"].sum())

    old_total_admitted = int(old_department_summary["total_admitted"].sum())
    new_total_admitted = int(new_department_summary["total_admitted"].sum())

    old_total_empty = int(old_department_summary["empty_positions"].sum())
    new_total_empty = int(new_department_summary["empty_positions"].sum())

    old_total_coverage = (
        old_total_admitted / old_total_positions * 100
        if old_total_positions > 0
        else 0
    )

    new_total_coverage = (
        new_total_admitted / new_total_positions * 100
        if new_total_positions > 0
        else 0
    )

    old_gel_available = int(
        old_department_summary["gel_day_base_score"].notna().sum()
    )

    new_gel_available = int(
        new_department_summary["gel_day_base_score"].notna().sum()
    )

    st.subheader(f"Σύγκριση {old_year} → {new_year}")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.metric(
            "Συνολικές Θέσεις",
            int(new_total_positions),
            delta=int(new_total_positions - old_total_positions)
        )

    with kpi2:
        st.metric(
            "Επιτυχόντες",
            int(new_total_admitted),
            delta=int(new_total_admitted - old_total_admitted)
        )

    with kpi3:
        st.metric(
            "Κενές Θέσεις",
            int(new_total_empty),
            delta=int(new_total_empty - old_total_empty),
            delta_color="inverse"
        )

    with kpi4:
        st.metric(
            "Συνολική Κάλυψη",
            f"{new_total_coverage:.2f}%",
            delta=f"{new_total_coverage - old_total_coverage:.2f}%"
        )

    kpi5, kpi6 = st.columns(2)

    with kpi5:
        st.metric(
            f"Προγράμματα με Βάση ΓΕΛ Ημ. {old_year}",
            int(old_gel_available)
        )

    with kpi6:
        st.metric(
            f"Προγράμματα με Βάση ΓΕΛ Ημ. {new_year}",
            int(new_gel_available),
            delta=int(new_gel_available - old_gel_available)
        )

    st.caption(
        "Η σύγκριση γίνεται για όλες τις κατηγορίες εισαγωγής. "
        "Οι Συνολικές Θέσεις είναι οι αρχικές θέσεις. "
        "Οι βάσεις ΓΕΛ Ημερήσια εμφανίζονται μόνο σε επίπεδο προπτυχιακού προγράμματος."
    )

    st.divider()

    st.subheader("Γραφήματα μεταβολών ανά πρόγραμμα")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        fig_admitted = px.bar(
            department_comparison.sort_values(
                "diff_total_admitted",
                ascending=False
            ).head(10),
            x="department_name_clean",
            y="diff_total_admitted",
            text="diff_total_admitted",
            title=f"Top-10 αυξήσεις επιτυχόντων {old_year} → {new_year}"
        )

        fig_admitted.update_traces(
            textposition="outside"
        )

        fig_admitted.update_layout(
            xaxis_title="Προπτυχιακό Πρόγραμμα",
            yaxis_title="Διαφορά Επιτυχόντων"
        )

        st.plotly_chart(
            fig_admitted,
            use_container_width=True
        )

    with chart_col2:
        fig_admitted_down = px.bar(
            department_comparison.sort_values(
                "diff_total_admitted",
                ascending=True
            ).head(10),
            x="department_name_clean",
            y="diff_total_admitted",
            text="diff_total_admitted",
            title=f"Top-10 μειώσεις επιτυχόντων {old_year} → {new_year}"
        )

        fig_admitted_down.update_traces(
            textposition="outside"
        )

        fig_admitted_down.update_layout(
            xaxis_title="Προπτυχιακό Πρόγραμμα",
            yaxis_title="Διαφορά Επιτυχόντων"
        )

        st.plotly_chart(
            fig_admitted_down,
            use_container_width=True
        )

    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        fig_base_up = px.bar(
            department_comparison
            .dropna(subset=["diff_gel_day_base_score"])
            .sort_values(
                "diff_gel_day_base_score",
                ascending=False
            )
            .head(10),
            x="department_name_clean",
            y="diff_gel_day_base_score",
            text="diff_gel_day_base_score",
            title=f"Top-10 αυξήσεις Βάσης ΓΕΛ Ημ. {old_year} → {new_year}"
        )

        fig_base_up.update_traces(
            texttemplate="%{text:.0f}",
            textposition="outside"
        )

        fig_base_up.update_layout(
            xaxis_title="Προπτυχιακό Πρόγραμμα",
            yaxis_title="Διαφορά Βάσης ΓΕΛ Ημ."
        )

        st.plotly_chart(
            fig_base_up,
            use_container_width=True
        )

    with chart_col4:
        fig_base_down = px.bar(
            department_comparison
            .dropna(subset=["diff_gel_day_base_score"])
            .sort_values(
                "diff_gel_day_base_score",
                ascending=True
            )
            .head(10),
            x="department_name_clean",
            y="diff_gel_day_base_score",
            text="diff_gel_day_base_score",
            title=f"Top-10 μειώσεις Βάσης ΓΕΛ Ημ. {old_year} → {new_year}"
        )

        fig_base_down.update_traces(
            texttemplate="%{text:.0f}",
            textposition="outside"
        )

        fig_base_down.update_layout(
            xaxis_title="Προπτυχιακό Πρόγραμμα",
            yaxis_title="Διαφορά Βάσης ΓΕΛ Ημ."
        )

        st.plotly_chart(
            fig_base_down,
            use_container_width=True
        )

    chart_col5, chart_col6 = st.columns(2)

    with chart_col5:
        fig_coverage = px.bar(
            department_comparison.sort_values(
                "diff_coverage",
                ascending=False
            ).head(10),
            x="department_name_clean",
            y="diff_coverage",
            text="diff_coverage",
            title=f"Top-10 αυξήσεις κάλυψης {old_year} → {new_year}"
        )

        fig_coverage.update_traces(
            texttemplate="%{text:.2f}%",
            textposition="outside"
        )

        fig_coverage.update_layout(
            xaxis_title="Προπτυχιακό Πρόγραμμα",
            yaxis_title="Διαφορά Κάλυψης"
        )

        st.plotly_chart(
            fig_coverage,
            use_container_width=True
        )

    with chart_col6:
        fig_coverage_down = px.bar(
            department_comparison.sort_values(
                "diff_coverage",
                ascending=True
            ).head(10),
            x="department_name_clean",
            y="diff_coverage",
            text="diff_coverage",
            title=f"Top-10 μειώσεις κάλυψης {old_year} → {new_year}"
        )

        fig_coverage_down.update_traces(
            texttemplate="%{text:.2f}%",
            textposition="outside"
        )

        fig_coverage_down.update_layout(
            xaxis_title="Προπτυχιακό Πρόγραμμα",
            yaxis_title="Διαφορά Κάλυψης"
        )

        st.plotly_chart(
            fig_coverage_down,
            use_container_width=True
        )

    st.divider()

    st.subheader("Αναλυτικοί πίνακες σύγκρισης")

    full_department_display = format_department_comparison_table(
        department_comparison.sort_values(
            "diff_gel_day_base_score",
            ascending=False,
            na_position="last"
        ),
        old_year,
        new_year
    )

    clean_department_display = format_clean_department_table(
        department_comparison.sort_values(
            "diff_gel_day_base_score",
            ascending=False,
            na_position="last"
        ),
        old_year,
        new_year
    )

    school_display = format_group_comparison_table(
        school_comparison.sort_values(
            "diff_total_admitted",
            ascending=False
        ),
        "school",
        "Σχολή",
        old_year,
        new_year
    )

    city_display = format_group_comparison_table(
        city_comparison.sort_values(
            "diff_total_admitted",
            ascending=False
        ),
        "city",
        "Πόλη",
        old_year,
        new_year
    )

    tab_clean, tab_full, tab_school, tab_city = st.tabs(
        [
            "Συνοπτικά ανά Πρόγραμμα",
            "Αναλυτικά ανά Πρόγραμμα",
            "Ανά Σχολή",
            "Ανά Πόλη",
        ]
    )

    with tab_clean:
        st.dataframe(
            style_comparison_table(clean_department_display),
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "Συνοπτικός πίνακας με τις βασικές μεταβολές: θέσεις, επιτυχόντες, κάλυψη και Βάση ΓΕΛ Ημερήσια."
        )

    with tab_full:
        st.dataframe(
            style_comparison_table(full_department_display),
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "Αναλυτικός πίνακας που περιλαμβάνει και Κενές Θέσεις / Πρώτο ΓΕΛ Ημερήσια."
        )

    with tab_school:
        st.dataframe(
            style_comparison_table(school_display),
            use_container_width=True,
            hide_index=True
        )

    with tab_city:
        st.dataframe(
            style_comparison_table(city_display),
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    st.subheader("Εξαγωγή αποτελεσμάτων")

    excel_file = create_excel_export(
        clean_department_display=clean_department_display,
        full_department_display=full_department_display,
        school_display=school_display,
        city_display=city_display,
        old_year=old_year,
        new_year=new_year
    )

    st.download_button(
        label="⬇️ Λήψη Excel σύγκρισης",
        data=excel_file,
        file_name=f"dipae_year_comparison_{old_year}_{new_year}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

except Exception as e:
    st.error("Υπήρξε πρόβλημα κατά τη σύγκριση ετών.")
    st.exception(e)