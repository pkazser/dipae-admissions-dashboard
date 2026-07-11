from components.sidebar_branding import show_sidebar_branding
import streamlit as st
from modules.database_manager import (
    initialize_database,
    load_departments,
    load_admissions_with_departments,
)


st.set_page_config(
    page_title="Εισακτέοι ΔΙ.ΠΑ.Ε.",
    page_icon="🎓",
    layout="wide"
)

show_sidebar_branding()
# ---------------------------------------------------------
# Αρχικοποίηση βάσης
# ---------------------------------------------------------

try:
    initialize_database()
except Exception as e:
    st.error("Υπήρξε πρόβλημα κατά την αρχικοποίηση της βάσης δεδομένων.")
    st.exception(e)
    st.stop()


# ---------------------------------------------------------
# Τίτλος
# ---------------------------------------------------------

st.title("🎓 Πλατφόρμα Ανάλυσης Εισακτέων ΔΙ.ΠΑ.Ε.")

st.markdown(
    """
Η εφαρμογή παρουσιάζει και αναλύει τα δεδομένα εισακτέων των **ενεργών προπτυχιακών
προγραμμάτων σπουδών του Διεθνούς Πανεπιστημίου της Ελλάδος (ΔΙ.ΠΑ.Ε.)**.

Στόχος είναι να παρέχει γρήγορη και κατανοητή εικόνα για:

- τις συνολικές θέσεις,
- τους επιτυχόντες,
- τις κενές θέσεις,
- το ποσοστό κάλυψης,
- τις βάσεις εισαγωγής ΓΕΛ Ημερήσια,
- τις συγκρίσεις μεταξύ ετών,
- και τη συνολική εικόνα ανά πρόγραμμα, Σχολή και Πόλη.
"""
)

st.divider()


# ---------------------------------------------------------
# Φόρτωση δεδομένων
# ---------------------------------------------------------

try:
    departments_df = load_departments()
    admissions_df = load_admissions_with_departments()
except Exception as e:
    st.error("Υπήρξε πρόβλημα κατά τη φόρτωση των δεδομένων.")
    st.exception(e)
    st.stop()


# ---------------------------------------------------------
# Βασικοί δείκτες αρχικής σελίδας
# ---------------------------------------------------------

active_programs = 0
total_schools = 0
total_cities = 0

if departments_df is not None and not departments_df.empty:
    active_programs = int(departments_df["department_code"].nunique())

    if "school" in departments_df.columns:
        total_schools = int(departments_df["school"].dropna().nunique())

    if "city" in departments_df.columns:
        total_cities = int(departments_df["city"].dropna().nunique())

available_years = []

if admissions_df is not None and not admissions_df.empty:
    available_years = sorted(
        admissions_df["year"].dropna().unique().tolist()
    )

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.metric(
        "Ενεργά Προπτυχιακά Προγράμματα",
        active_programs
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
    if available_years:
        st.metric(
            "Έτη Δεδομένων",
            f"{min(available_years)}–{max(available_years)}"
        )
    else:
        st.metric(
            "Έτη Δεδομένων",
            "—"
        )


# ---------------------------------------------------------
# Μεθοδολογία
# ---------------------------------------------------------

st.divider()

st.subheader("📌 Μεθοδολογικοί κανόνες")

st.markdown(
    """
Η εφαρμογή ακολουθεί ενιαία λογική σε όλες τις σελίδες:

1. Η ανάλυση γίνεται πάντα για όλες τις κατηγορίες εισαγωγής.

2. Οι Συνολικές Θέσεις υπολογίζονται από τις Αρχικές Θέσεις.

3. Η Συνολική Κάλυψη υπολογίζεται ως Επιτυχόντες / Συνολικές Θέσεις.

4. Η Βάση Προγράμματος είναι η Βάση ΓΕΛ Ημερήσια.

5. Ο Πρώτος Προγράμματος είναι ο Πρώτος ΓΕΛ Ημερήσια.

6. Δεν εμφανίζεται άθροισμα τελικών θέσεων.

7. Δεν εμφανίζεται φαινόμενη μεταβολή θέσεων.

8. Δεν χρησιμοποιούνται μέσοι όροι βάσεων σε επίπεδο Σχολής ή Πόλης.
"""
)


# ---------------------------------------------------------
# Σελίδες εφαρμογής
# ---------------------------------------------------------

st.divider()

st.subheader("🧭 Διαθέσιμες ενότητες")

st.markdown(
    """
Από το αριστερό μενού μπορείς να χρησιμοποιήσεις τις βασικές ενότητες της εφαρμογής:

### 📋 Δεδομένα Εισακτέων
Προβολή συνολικών δεδομένων ανά έτος, με πίνακες και γραφήματα για όλα τα ενεργά
προπτυχιακά προγράμματα.

### 🏛️ Ανάλυση Προγράμματος
Αναλυτική εικόνα για ένα συγκεκριμένο προπτυχιακό πρόγραμμα: θέσεις, επιτυχόντες,
κάλυψη, βάση ΓΕΛ Ημερήσια και στοιχεία ανά κατηγορία εισαγωγής.

### 🏫 Ανάλυση Σχολών και Πόλεων
Συγκεντρωτική εικόνα ανά Σχολή ή ανά Πόλη, χωρίς μέσους όρους βάσεων.

### 🏆 Top Rankings
Κατατάξεις προγραμμάτων με βάση τη Βάση ΓΕΛ Ημερήσια, τους επιτυχόντες,
την κάλυψη, τις κενές θέσεις και τις συνολικές θέσεις.

### 📊 Dashboard Διοίκησης
Στοχευμένη διοικητική εικόνα για το σύνολο του Ιδρύματος, με βασικούς δείκτες
και Top-5 επισημάνσεις.

### 📈 Σύγκριση Ετών
Σύγκριση δύο ετών ως προς θέσεις, επιτυχόντες, κάλυψη, κενές θέσεις και βάσεις
ΓΕΛ Ημερήσια.
"""
)


# ---------------------------------------------------------
# Διαθέσιμα δεδομένα
# ---------------------------------------------------------

st.divider()

st.subheader("📂 Διαθέσιμα δεδομένα")

if admissions_df is None or admissions_df.empty:
    st.warning(
        "Δεν υπάρχουν ακόμη δεδομένα εισακτέων στη βάση. "
        "Για την online έκδοση πρέπει να έχει ανέβει ενημερωμένο αρχείο database/admissions.db."
    )
else:
    latest_year = max(available_years)

    latest_df = admissions_df[
        admissions_df["year"] == latest_year
    ].copy()

    total_positions_latest = int(latest_df["initial_positions"].sum())
    total_admitted_latest = int(latest_df["admitted"].sum())
    total_empty_latest = total_positions_latest - total_admitted_latest

    total_coverage_latest = (
        total_admitted_latest / total_positions_latest * 100
        if total_positions_latest > 0
        else 0
    )

    st.markdown(
        f"""
Για το πιο πρόσφατο διαθέσιμο έτος **{latest_year}**:

- **Συνολικές Θέσεις:** {total_positions_latest}
- **Επιτυχόντες:** {total_admitted_latest}
- **Κενές Θέσεις:** {total_empty_latest}
- **Συνολική Κάλυψη:** {total_coverage_latest:.1f}%
"""
    )

    st.caption(
        "Οι τιμές αυτές υπολογίζονται για όλες τις κατηγορίες εισαγωγής και "
        "οι Συνολικές Θέσεις βασίζονται στις Αρχικές Θέσεις."
    )


# ---------------------------------------------------------
# Τελική σημείωση
# ---------------------------------------------------------

st.divider()

st.info(
    "Η online έκδοση λειτουργεί ως dashboard προβολής και ανάλυσης. "
    "Η εισαγωγή νέων αρχείων Υπουργείου γίνεται τοπικά και στη συνέχεια ενημερώνεται "
    "το online περιβάλλον με νέο database/admissions.db."
)