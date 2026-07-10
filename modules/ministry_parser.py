import re
import zipfile
from io import BytesIO
from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"


def find_header_row(df_raw):
    """
    Εντοπίζει τη γραμμή που περιέχει τα πραγματικά ονόματα στηλών.
    Ψάχνει για τις στήλες 'ΚΩΔΙΚΟΣ ΣΧΟΛΗΣ' και 'ΙΔΡΥΜΑ'.
    """

    for idx, row in df_raw.iterrows():
        row_values = [str(x).strip() for x in row.values]

        has_school_code = any(
            "ΚΩΔΙΚΟΣ" in x and "ΣΧΟΛΗΣ" in x
            for x in row_values
        )

        has_institution = any(
            "ΙΔΡΥΜΑ" in x
            for x in row_values
        )

        if has_school_code and has_institution:
            return idx

    raise ValueError("Δεν βρέθηκε γραμμή επικεφαλίδων στο Excel.")


def clean_column_name(col):
    """
    Καθαρίζει ονόματα στηλών από κενά, αλλαγές γραμμής και περίεργους χαρακτήρες.
    """

    col = str(col)
    col = col.replace("\n", " ")
    col = col.replace("\r", " ")
    col = " ".join(col.split())
    return col.strip()


def parse_ministry_excel(file_obj, source_file, year, exam_category):
    """
    Διαβάζει ένα Excel βάσεων του Υπουργείου και επιστρέφει καθαρό DataFrame.

    Υποστηρίζει διαφορετικές δομές αρχείων:
    - ΓΕΛ
    - ΕΠΑΛ
    - Εσπερινά
    - 10%

    Η στήλη scientific_fields είναι προαιρετική,
    γιατί στα αρχεία ΕΠΑΛ μπορεί να μην υπάρχει.
    """

    df_raw = pd.read_excel(file_obj, header=None)

    header_row = find_header_row(df_raw)

    columns = df_raw.iloc[header_row].apply(clean_column_name).tolist()

    df = df_raw.iloc[header_row + 1:].copy()
    df.columns = columns

    df = df.dropna(how="all")

    rename_map = {
        "ΚΩΔΙΚΟΣ ΣΧΟΛΗΣ": "ministry_department_code",
        "ΙΔΡΥΜΑ": "institution",
        "ΟΝΟΜΑ ΣΧΟΛΗΣ": "department_name_raw",
        "ΕΙΔΟΣ ΘΕΣΗΣ": "admission_type",
        "ΕΠΙΣΤΗΜΟΝΙΚΑ ΠΕΔΙΑ": "scientific_fields",
        "ΑΡΧΙΚΕΣ ΘΕΣΕΙΣ": "initial_positions",
        "ΘΕΣΕΙΣ (Κατόπιν Μεταφοράς)": "final_positions",
        "ΕΠΙΤ/ΤΕΣ": "admitted",
        "ΒΑΘΜΟΣ ΠΡΩΤΟΥ": "first_score",
        "ΒΑΘΜΟΣ ΤΕΛΕΥΤΑΙΟΥ": "base_score",
    }

    df = df.rename(columns=rename_map)

    required_columns = [
        "ministry_department_code",
        "institution",
        "department_name_raw",
        "admission_type",
        "initial_positions",
        "final_positions",
        "admitted",
        "first_score",
        "base_score",
    ]

    optional_columns = [
        "scientific_fields",
    ]

    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        raise ValueError(f"Λείπουν υποχρεωτικές στήλες από το Excel: {missing}")

    for col in optional_columns:
        if col not in df.columns:
            df[col] = None

    final_columns = [
        "ministry_department_code",
        "institution",
        "department_name_raw",
        "admission_type",
        "scientific_fields",
        "initial_positions",
        "final_positions",
        "admitted",
        "first_score",
        "base_score",
    ]

    df = df[final_columns].copy()

    df["year"] = year
    df["exam_category"] = exam_category
    df["source_file"] = source_file

    numeric_columns = [
        "initial_positions",
        "final_positions",
        "admitted",
        "first_score",
        "base_score",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["coverage"] = (df["admitted"] / df["final_positions"]) * 100

    return df


def filter_dipae(df):
    """
    Κρατά μόνο τις εγγραφές που ανήκουν στο ΔΙ.ΠΑ.Ε.
    """

    institution = df["institution"].astype(str).str.upper()

    mask = (
        institution.str.contains("ΔΙ.ΠΑ", na=False)
        | institution.str.contains("ΔΙΠΑ", na=False)
        | institution.str.contains("ΔΙΕΘΝΕΣ ΠΑΝΕΠΙΣΤΗΜΙΟ", na=False)
    )

    return df[mask].copy()


def detect_exam_category(file_name):
    """
    Αναγνωρίζει την κατηγορία εισαγωγής από το όνομα του αρχείου.

    Κοιτάμε μόνο το basename του αρχείου, όχι όλο το path του ZIP,
    γιατί το path μπορεί να περιέχει φράσεις όπως 'ΓΕΛ, ΕΠΑΛ'
    και να μπερδεύει την αναγνώριση.
    """

    name = Path(str(file_name)).name.upper()

    name = name.replace("_", " ")
    name = name.replace("-", " ")
    name = " ".join(name.split())

    if "10%" in name:
        year_match = re.search(r"(20\d{2})", name)
        candidate_year = year_match.group(1) if year_match else None

        if "ΕΠΑΛ" in name and candidate_year:
            return f"10% ΕΠΑΛ {candidate_year}"

        if "ΓΕΛ" in name and candidate_year:
            return f"10% ΓΕΛ {candidate_year}"

        if "ΕΠΑΛ" in name:
            return "10% ΕΠΑΛ"

        if "ΓΕΛ" in name:
            return "10% ΓΕΛ"

        return "10% Άγνωστο"

    if "ΕΠΑΛ" in name and "ΗΜΕΡΗΣΙΑ" in name:
        return "ΕΠΑΛ Ημερήσια"

    if "ΕΠΑΛ" in name and "ΕΣΠΕΡΙΝΑ" in name:
        return "ΕΠΑΛ Εσπερινά"

    if "ΓΕΛ" in name and "ΗΜΕΡΗΣΙΑ" in name:
        return "ΓΕΛ Ημερήσια"

    if "ΓΕΛ" in name and "ΕΣΠΕΡΙΝΑ" in name:
        return "ΓΕΛ Εσπερινά"

    return "Άγνωστη κατηγορία"
    
def parse_gel_day_from_zip(year):
    """
    Διαβάζει από το ZIP του έτους μόνο το αρχείο ΓΕΛ-ΗΜΕΡΗΣΙΑ.
    Χρήσιμο για αρχικό έλεγχο.
    """

    zip_path = RAW_DATA_DIR / str(year) / f"bases_{year}.zip"

    if not zip_path.exists():
        raise FileNotFoundError(f"Δεν βρέθηκε το αρχείο: {zip_path}")

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        excel_files = [
            name for name in zip_ref.namelist()
            if name.lower().endswith((".xls", ".xlsx"))
        ]

        target_files = [
            name for name in excel_files
            if "ΓΕΛ-ΗΜΕΡΗΣΙΑ" in name
        ]

        if not target_files:
            raise FileNotFoundError("Δεν βρέθηκε αρχείο ΓΕΛ-ΗΜΕΡΗΣΙΑ μέσα στο ZIP.")

        selected_file = target_files[0]

        with zip_ref.open(selected_file) as extracted_file:
            excel_bytes = BytesIO(extracted_file.read())

        df = parse_ministry_excel(
            file_obj=excel_bytes,
            source_file=selected_file,
            year=year,
            exam_category="ΓΕΛ Ημερήσια"
        )

    return df


def parse_all_excels_from_zip(year):
    """
    Διαβάζει όλα τα Excel του ZIP ενός έτους,
    τα μετατρέπει σε καθαρά DataFrames και τα ενώνει σε ένα DataFrame.

    Επιστρέφει:
    - combined_df: όλες οι εγγραφές από όσα αρχεία διαβάστηκαν σωστά
    - failed_files: λίστα με αρχεία που απέτυχαν και το μήνυμα λάθους
    """

    zip_path = RAW_DATA_DIR / str(year) / f"bases_{year}.zip"

    if not zip_path.exists():
        raise FileNotFoundError(f"Δεν βρέθηκε το αρχείο: {zip_path}")

    all_dfs = []
    failed_files = []

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        excel_files = [
            name for name in zip_ref.namelist()
            if name.lower().endswith((".xls", ".xlsx"))
        ]

        for excel_name in excel_files:
            exam_category = detect_exam_category(excel_name)

            try:
                with zip_ref.open(excel_name) as extracted_file:
                    excel_bytes = BytesIO(extracted_file.read())

                df = parse_ministry_excel(
                    file_obj=excel_bytes,
                    source_file=excel_name,
                    year=year,
                    exam_category=exam_category
                )

                all_dfs.append(df)

            except Exception as e:
                failed_files.append(
                    {
                        "file": excel_name,
                        "error": str(e)
                    }
                )

    if len(all_dfs) == 0:
        raise ValueError("Δεν διαβάστηκε κανένα Excel από το ZIP.")

    combined_df = pd.concat(all_dfs, ignore_index=True)

    return combined_df, failed_files
def parse_all_excels_from_uploaded_zip(uploaded_file, year):
    """
    Διαβάζει όλα τα Excel από ZIP που ανέβηκε μέσω Streamlit file_uploader.

    Επιστρέφει:
    - combined_df: όλες οι εγγραφές από όσα αρχεία διαβάστηκαν σωστά
    - failed_files: λίστα με αρχεία που απέτυχαν
    """

    all_dfs = []
    failed_files = []

    zip_bytes = BytesIO(uploaded_file.read())

    with zipfile.ZipFile(zip_bytes, "r") as zip_ref:
        excel_files = [
            name for name in zip_ref.namelist()
            if name.lower().endswith((".xls", ".xlsx"))
        ]

        for excel_name in excel_files:
            exam_category = detect_exam_category(excel_name)

            try:
                with zip_ref.open(excel_name) as extracted_file:
                    excel_bytes = BytesIO(extracted_file.read())

                df = parse_ministry_excel(
                    file_obj=excel_bytes,
                    source_file=excel_name,
                    year=year,
                    exam_category=exam_category
                )

                all_dfs.append(df)

            except Exception as e:
                failed_files.append(
                    {
                        "file": excel_name,
                        "error": str(e)
                    }
                )

    if len(all_dfs) == 0:
        raise ValueError("Δεν διαβάστηκε κανένα Excel από το ZIP.")

    combined_df = pd.concat(all_dfs, ignore_index=True)

    return combined_df, failed_files