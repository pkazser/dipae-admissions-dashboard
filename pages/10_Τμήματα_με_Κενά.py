import io
from pathlib import Path

import pandas as pd
import streamlit as st

from modules.database_manager import load_admissions_with_departments
from components.sidebar_branding import show_sidebar_branding


st.set_page_config(
    page_title="Τμήματα με Κενά | ΔΙΠΑΕ",
    page_icon="🔎",
    layout="wide"
)

show_sidebar_branding()


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports" / "interpretive"


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


def format_percent(value):
    try:
        return f"{float(value):.2f}%"
    except Exception:
        return "0.00%"


def format_score(value):
    try:
        if pd.isna(value):
            return ""
        return f"{float(value):.0f}"
    except Exception:
        return ""


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

    df_gel["gel_day_admitted"] = df_gel["admitted"].fillna(0)

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
    Δημιουργεί σύνοψη ανά πρόγραμμα ΔΙ.ΠΑ.Ε.

    Συνολική κάλυψη:
    - όλες οι κατηγορίες εισαγωγής
    - συνολικές θέσεις = αρχικές θέσεις
    """

    summary = (
        df_year
        .groupby(
            [
                "department_code",
                "ministry_department_code",
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
            summary[col] = None

    return summary


def build_display_table(df):
    """
    Πίνακας εμφάνισης στην εφαρμογή και στο Excel.
    """

    display = df[
        [
            "department_name_clean",
            "school",
            "city",
            "ministry_department_code",
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
    ].copy()

    display = display.rename(
        columns={
            "department_name_clean": "Προπτυχιακό Πρόγραμμα",
            "school": "Σχολή",
            "city": "Πόλη",
            "ministry_department_code": "Κωδικός Υπουργείου",
            "total_positions": "Συνολικές Θέσεις",
            "total_admitted": "Επιτυχόντες",
            "empty_positions": "Κενές Θέσεις",
            "total_coverage": "Συνολική Κάλυψη %",
            "gel_day_positions": "ΓΕΛ Ημερήσια Θέσεις",
            "gel_day_admitted": "ΓΕΛ Ημερήσια Επιτυχόντες",
            "gel_day_empty": "Κενές ΓΕΛ Ημερήσια",
            "gel_day_coverage": "Κάλυψη ΓΕΛ Ημερήσια %",
            "gel_day_first_score": "Πρώτος ΓΕΛ Ημ.",
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
        "Πρώτος ΓΕΛ Ημ.",
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
        "Κάλυψη ΓΕΛ Ημερήσια %",
    ]:
        display[col] = (
            display[col]
            .fillna(0)
            .round(2)
        )

    return display


def build_ai_prompts_table(df, selected_year):
    """
    Δημιουργεί δεύτερο φύλλο Excel με έτοιμα prompts για σύγκριση ομοειδών τμημάτων.
    """

    rows = []

    for _, row in df.iterrows():
        program = row["department_name_clean"]
        school = row["school"]
        city = row["city"]

        total_positions = safe_int(row["total_positions"])
        total_admitted = safe_int(row["total_admitted"])
        empty_positions = safe_int(row["empty_positions"])
        total_coverage = safe_float(row["total_coverage"])

        gel_positions = safe_int(row["gel_day_positions"])
        gel_admitted = safe_int(row["gel_day_admitted"])
        gel_empty = safe_int(row["gel_day_empty"])
        gel_coverage = safe_float(row["gel_day_coverage"])
        gel_base = format_score(row["gel_day_base_score"])
        gel_first = format_score(row["gel_day_first_score"])

        prompt = f"""Θέλω να συγκρίνεις το πρόγραμμα «{program}» του ΔΙ.ΠΑ.Ε. για το {selected_year} με αντίστοιχα ή ομοειδή τμήματα άλλων ελληνικών ΑΕΙ.

Στοιχεία ΔΙ.ΠΑ.Ε.:
- Σχολή: {school}
- Πόλη: {city}
- Συνολικές θέσεις όλων των κατηγοριών: {total_positions}
- Επιτυχόντες όλων των κατηγοριών: {total_admitted}
- Κενές θέσεις όλων των κατηγοριών: {empty_positions}
- Συνολική κάλυψη: {total_coverage:.2f}%
- ΓΕΛ Ημερήσια θέσεις: {gel_positions}
- ΓΕΛ Ημερήσια επιτυχόντες: {gel_admitted}
- Κενές ΓΕΛ Ημερήσια: {gel_empty}
- Κάλυψη ΓΕΛ Ημερήσια: {gel_coverage:.2f}%
- Βάση ΓΕΛ Ημερήσια: {gel_base}
- Πρώτος ΓΕΛ Ημερήσια: {gel_first}

Με βάση το επίσημο αρχείο του Υπουργείου για τις βάσεις {selected_year}, εντόπισε αντίστοιχα ή ομοειδή τμήματα άλλων Πανεπιστημίων.

Για κάθε ομοειδές τμήμα δώσε πίνακα με:
- Ίδρυμα
- Πόλη
- Τμήμα
- Βάση ΓΕΛ Ημερήσια {selected_year}
- Θέσεις ΓΕΛ Ημερήσια
- Επιτυχόντες ΓΕΛ Ημερήσια
- Κενές ΓΕΛ Ημερήσια
- Κάλυψη ΓΕΛ Ημερήσια %

Στο τέλος γράψε σύντομη διοικητική ερμηνεία:
- αν το φαινόμενο των κενών φαίνεται γενικότερο στο αντικείμενο ή ειδικότερο για το ΔΙ.ΠΑ.Ε.
- να αποφύγεις απόλυτες αιτιότητες
- να αναφέρεις ότι απαιτείται περαιτέρω διερεύνηση
- να διαχωρίζεις σαφώς τη συνολική κάλυψη όλων των κατηγοριών από τη ΓΕΛ Ημερήσια."""

        rows.append(
            {
                "Προπτυχιακό Πρόγραμμα": program,
                "Κενές Θέσεις": empty_positions,
                "Συνολική Κάλυψη %": round(total_coverage, 2),
                "Κενές ΓΕΛ Ημερήσια": gel_empty,
                "Κάλυψη ΓΕΛ Ημερήσια %": round(gel_coverage, 2),
                "Prompt για AI": prompt,
            }
        )

    return pd.DataFrame(rows)


def create_excel_file(gaps_display, prompts_display, selected_year):
    """
    Δημιουργεί Excel με:
    - Φύλλο 1: Τμήματα με αυξημένα κενά
    - Φύλλο 2: Prompts για AI
    """

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        gaps_display.to_excel(
            writer,
            index=False,
            sheet_name="Τμήματα με Κενά"
        )

        prompts_display.to_excel(
            writer,
            index=False,
            sheet_name="AI Prompts"
        )

        workbook = writer.book

        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]

            worksheet.freeze_panes = "A2"

            for column_cells in worksheet.columns:
                max_length = 0
                column_letter = column_cells[0].column_letter

                for cell in column_cells:
                    try:
                        value = str(cell.value)
                        if len(value) > max_length:
                            max_length = len(value)
                    except Exception:
                        pass

                adjusted_width = min(max_length + 2, 80)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        worksheet_prompts = writer.sheets["AI Prompts"]
        worksheet_prompts.column_dimensions["F"].width = 120

    output.seek(0)
    return output


def highlight_coverage(val):
    try:
        value = float(val)
    except Exception:
        return ""

    if value >= 100:
        return "background-color: #d4edda; color: #155724; font-weight: bold;"
    elif value >= 80:
        return "background-color: #fff3cd; color: #664d03; font-weight: bold;"
    else:
        return "background-color: #f8d7da; color: #721c24; font-weight: bold;"


def highlight_empty(val):
    try:
        value = float(val)
    except Exception:
        return ""

    if value >= 50:
        return "background-color: #f8d7da; color: #721c24; font-weight: bold;"
    elif value > 0:
        return "background-color: #fff3cd; color: #664d03; font-weight: bold;"
    else:
        return "background-color: #d4edda; color: #155724; font-weight: bold;"


def style_gaps_table(df):
    style_obj = df.style.format(
        {
            "Συνολική Κάλυψη %": "{:.2f}%",
            "Κάλυψη ΓΕΛ Ημερήσια %": "{:.2f}%",
        }
    )

    for col in [
        "Συνολική Κάλυψη %",
        "Κάλυψη ΓΕΛ Ημερήσια %",
    ]:
        if col in df.columns:
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

    for col in [
        "Κενές Θέσεις",
        "Κενές ΓΕΛ Ημερήσια",
    ]:
        if col in df.columns:
            try:
                style_obj = style_obj.map(
                    highlight_empty,
                    subset=[col]
                )
            except AttributeError:
                style_obj = style_obj.applymap(
                    highlight_empty,
                    subset=[col]
                )

    return style_obj


def find_existing_report(selected_year):
    """
    Αναζητά έτοιμη ερμηνευτική αναφορά για το επιλεγμένο έτος.
    Προτεραιότητα σε PDF, μετά DOCX.
    """

    pdf_path = REPORTS_DIR / f"interpretive_report_{selected_year}.pdf"
    docx_path = REPORTS_DIR / f"interpretive_report_{selected_year}.docx"

    if pdf_path.exists():
        return pdf_path

    if docx_path.exists():
        return docx_path

    return None


# ---------------------------------------------------------
# Κύρια σελίδα
# ---------------------------------------------------------

st.title("🔎 Τμήματα με αυξημένα κενά")

st.markdown("""
Η σελίδα αυτή εντοπίζει τα προπτυχιακά προγράμματα του ΔΙ.ΠΑ.Ε. με αυξημένα
κενά και δημιουργεί αρχείο Excel για περαιτέρω διερεύνηση και σύγκριση με
ομοειδή τμήματα άλλων Πανεπιστημίων.

Η διαδικασία είναι ημιαυτόματη και ασφαλής: η εφαρμογή εξάγει τα δεδομένα
του ΔΙ.ΠΑ.Ε., ενώ η συγκριτική ερμηνεία μπορεί να γίνει εξωτερικά με βάση
το επίσημο αρχείο του Υπουργείου και τελικό έλεγχο από τον χρήστη.
""")

st.divider()

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

    st.subheader("Κριτήρια εντοπισμού")

    col1, col2, col3 = st.columns(3)

    with col1:
        min_empty_positions = st.number_input(
            "Ελάχιστες συνολικές κενές θέσεις",
            min_value=0,
            max_value=300,
            value=20,
            step=5
        )

    with col2:
        max_total_coverage = st.number_input(
            "Μέγιστη συνολική κάλυψη %",
            min_value=0.0,
            max_value=100.0,
            value=90.0,
            step=5.0,
            format="%.2f"
        )

    with col3:
        min_gel_empty_positions = st.number_input(
            "Ελάχιστες κενές ΓΕΛ Ημερήσια",
            min_value=0,
            max_value=300,
            value=10,
            step=5
        )

    st.caption(
        "Ένα πρόγραμμα εμφανίζεται στον πίνακα όταν ικανοποιεί τουλάχιστον ένα από τα παραπάνω κριτήρια."
    )

    gaps_df = department_summary[
        (
            department_summary["empty_positions"].fillna(0)
            >= min_empty_positions
        )
        |
        (
            department_summary["total_coverage"].fillna(0)
            <= max_total_coverage
        )
        |
        (
            department_summary["gel_day_empty"].fillna(0)
            >= min_gel_empty_positions
        )
    ].copy()

    gaps_df = gaps_df.sort_values(
        [
            "empty_positions",
            "gel_day_empty",
            "total_coverage",
        ],
        ascending=[
            False,
            False,
            True,
        ]
    )

    total_programs = int(department_summary["department_code"].nunique())
    gap_programs = int(gaps_df["department_code"].nunique())

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.metric(
            "Σύνολο Προγραμμάτων",
            total_programs
        )

    with kpi2:
        st.metric(
            "Προγράμματα προς διερεύνηση",
            gap_programs
        )

    with kpi3:
        st.metric(
            "Συνολικές κενές στα επιλεγμένα",
            safe_int(gaps_df["empty_positions"].sum())
        )

    with kpi4:
        if not gaps_df.empty:
            avg_coverage = gaps_df["total_coverage"].mean()
        else:
            avg_coverage = 0

        st.metric(
            "Μέση κάλυψη επιλεγμένων",
            f"{avg_coverage:.2f}%"
        )

    st.divider()

    st.subheader("Προγράμματα προς διερεύνηση")

    if gaps_df.empty:
        st.success("Δεν εντοπίστηκαν προγράμματα με βάση τα επιλεγμένα κριτήρια.")
        st.stop()

    gaps_display = build_display_table(gaps_df)
    prompts_display = build_ai_prompts_table(gaps_df, selected_year)

    st.dataframe(
        style_gaps_table(gaps_display),
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Η «Συνολική Κάλυψη %» υπολογίζεται επί των συνολικών θέσεων όλων των κατηγοριών εισαγωγής. "
        "Η σύγκριση με ομοειδή τμήματα προτείνεται να γίνεται κυρίως με στοιχεία ΓΕΛ Ημερήσια, "
        "ώστε οι συγκρίσεις να είναι πιο καθαρές."
    )

    st.divider()

    st.subheader("Εξαγωγή για περαιτέρω διερεύνηση")

    excel_file = create_excel_file(
        gaps_display=gaps_display,
        prompts_display=prompts_display,
        selected_year=selected_year
    )

    st.download_button(
        label="⬇️ Κατέβασμα Excel με τμήματα και AI prompts",
        data=excel_file,
        file_name=f"dipae_tmimata_me_kena_{selected_year}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.info(
        "Το Excel περιλαμβάνει δύο φύλλα: "
        "1) τα προγράμματα με αυξημένα κενά και "
        "2) έτοιμα prompts για σύγκριση με ομοειδή τμήματα."
    )

    st.divider()

    st.subheader("Ερμηνευτική αναφορά διοίκησης")

    report_path = find_existing_report(selected_year)

    if report_path is None:
        st.warning(
            "Δεν έχει ανέβει ακόμη έτοιμη ερμηνευτική αναφορά για το επιλεγμένο έτος."
        )

        st.caption(
            "Η αναφορά μπορεί να δημιουργηθεί εξωτερικά, να ελεγχθεί και στη συνέχεια "
            "να τοποθετηθεί στον φάκελο reports/interpretive με όνομα "
            f"interpretive_report_{selected_year}.pdf ή interpretive_report_{selected_year}.docx."
        )

    else:
        file_suffix = report_path.suffix.lower()

        if file_suffix == ".pdf":
            mime_type = "application/pdf"
            label = "📄 Κατέβασμα ερμηνευτικής αναφοράς PDF"
        else:
            mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            label = "📄 Κατέβασμα ερμηνευτικής αναφοράς Word"

        with open(report_path, "rb") as f:
            st.download_button(
                label=label,
                data=f,
                file_name=report_path.name,
                mime=mime_type
            )

        st.success(
            f"Βρέθηκε ερμηνευτική αναφορά για το {selected_year}: {report_path.name}"
        )

except Exception as e:
    st.error("Υπήρξε πρόβλημα κατά την προβολή των τμημάτων με κενά.")
    st.exception(e)