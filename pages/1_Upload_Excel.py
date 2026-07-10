import streamlit as st
import pandas as pd
import zipfile
from io import BytesIO

from modules.ministry_parser import (
    parse_all_excels_from_uploaded_zip,
    filter_dipae
)

from modules.database_manager import (
    initialize_database,
    save_admissions_dataframe,
    load_admissions
)


st.set_page_config(
    page_title="Upload Excel | Εισακτέοι ΔΙΠΑΕ",
    page_icon="📤",
    layout="wide"
)


st.title("📤 Εισαγωγή αρχείων Υπουργείου")

st.markdown("""
Σε αυτή τη σελίδα φορτώνουμε το ZIP του Υπουργείου, διαβάζουμε όλα τα Excel
που περιέχει, κρατάμε μόνο τα Τμήματα του ΔΙ.ΠΑ.Ε. και αποθηκεύουμε τα δεδομένα
στη βάση της εφαρμογής.
""")

st.divider()


selected_year = st.number_input(
    "Έτος βάσεων",
    min_value=2000,
    max_value=2100,
    value=2024,
    step=1
)

uploaded_file = st.file_uploader(
    "Ανέβασε ZIP αρχείο Υπουργείου",
    type=["zip"]
)


def preview_zip(uploaded_file):
    """
    Εμφανίζει τα Excel που υπάρχουν μέσα στο ZIP.
    """

    zip_bytes = BytesIO(uploaded_file.getvalue())

    with zipfile.ZipFile(zip_bytes, "r") as zip_ref:
        excel_files = [
            name for name in zip_ref.namelist()
            if name.lower().endswith((".xls", ".xlsx"))
        ]

    return excel_files


if uploaded_file is None:
    st.info("Ανέβασε ένα ZIP αρχείο του Υπουργείου για να ξεκινήσει η εισαγωγή.")
    st.stop()


st.success("Το αρχείο φορτώθηκε επιτυχώς.")

try:
    excel_files = preview_zip(uploaded_file)

    st.subheader("Excel αρχεία που βρέθηκαν στο ZIP")

    if len(excel_files) == 0:
        st.error("Δεν βρέθηκαν Excel αρχεία μέσα στο ZIP.")
        st.stop()

    st.write(excel_files)

    st.metric("Πλήθος Excel αρχείων", len(excel_files))

except Exception as e:
    st.error("Υπήρξε πρόβλημα κατά την ανάγνωση του ZIP.")
    st.exception(e)
    st.stop()


st.divider()

st.subheader("Έλεγχος και εισαγωγή στη βάση")

st.warning(
    "Η εισαγωγή θα αντικαταστήσει τυχόν παλιές εγγραφές του ίδιου έτους "
    "στον πίνακα admissions."
)

if st.button("🔍 Ανάλυση αρχείου", type="secondary"):

    try:
        df_all, failed_files = parse_all_excels_from_uploaded_zip(
            uploaded_file=uploaded_file,
            year=int(selected_year)
        )

        df_dipae = filter_dipae(df_all)

        st.session_state["uploaded_import_df"] = df_dipae
        st.session_state["uploaded_failed_files"] = failed_files
        st.session_state["uploaded_year"] = int(selected_year)

        st.success("Η ανάλυση ολοκληρώθηκε.")

    except Exception as e:
        st.error("Υπήρξε πρόβλημα κατά την ανάλυση του αρχείου.")
        st.exception(e)


if "uploaded_import_df" in st.session_state:

    df_dipae = st.session_state["uploaded_import_df"]
    failed_files = st.session_state["uploaded_failed_files"]
    import_year = st.session_state["uploaded_year"]

    st.subheader("Αποτελέσματα ανάλυσης")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Έτος", import_year)

    with col2:
        st.metric("Εγγραφές ΔΙ.ΠΑ.Ε.", len(df_dipae))

    with col3:
        st.metric("Κατηγορίες", df_dipae["exam_category"].nunique())

    st.markdown("### Εγγραφές ανά κατηγορία")

    category_counts = (
        df_dipae["exam_category"]
        .value_counts()
        .reset_index()
    )

    category_counts.columns = ["Κατηγορία", "Εγγραφές"]

    st.dataframe(
        category_counts,
        use_container_width=True,
        hide_index=True
    )

    if failed_files:
        st.warning("Κάποια αρχεία δεν διαβάστηκαν σωστά.")
        st.write(failed_files)
    else:
        st.success("Όλα τα Excel διαβάστηκαν επιτυχώς.")

    st.markdown("### Προεπισκόπηση δεδομένων ΔΙ.ΠΑ.Ε.")

    preview_df = df_dipae[
        [
            "year",
            "exam_category",
            "ministry_department_code",
            "institution",
            "department_name_raw",
            "final_positions",
            "admitted",
            "coverage",
            "first_score",
            "base_score",
        ]
    ].copy()

    preview_df["coverage"] = preview_df["coverage"].round(2)

    st.dataframe(
        preview_df.head(50),
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    if st.button("💾 Εισαγωγή στη βάση", type="primary"):

        try:
            initialize_database()

            save_admissions_dataframe(
                df=df_dipae,
                year=import_year
            )

            df_db = load_admissions(year=import_year)

            st.success("Η εισαγωγή στη βάση ολοκληρώθηκε επιτυχώς.")

            col_db1, col_db2 = st.columns(2)

            with col_db1:
                st.metric("Εγγραφές στη βάση", len(df_db))

            with col_db2:
                st.metric("Κατηγορίες στη βάση", df_db["exam_category"].nunique())

        except Exception as e:
            st.error("Υπήρξε πρόβλημα κατά την εισαγωγή στη βάση.")
            st.exception(e)