from pathlib import Path

import pandas as pd
import streamlit as st

from modules.database_manager import (
    initialize_database,
    load_departments,
    load_admissions_with_departments,
)
from components.sidebar_branding import show_sidebar_branding


# ---------------------------------------------------------
# Ρυθμίσεις σελίδας
# ---------------------------------------------------------

st.set_page_config(
    page_title="Πλατφόρμα Ανάλυσης Εισακτέων ΔΙ.ΠΑ.Ε.",
    page_icon="🎓",
    layout="wide"
)

# Δεν εμφανίζουμε πλέον λογότυπα στο sidebar.
# Η συνάρτηση παραμένει για συμβατότητα με τις υπόλοιπες σελίδες.
show_sidebar_branding()


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"

DIPAE_LOGO_PATH = ASSETS_DIR / "dipae_logo.png"
MODIP_LOGO_PATH = ASSETS_DIR / "modip_logo.png"


# ---------------------------------------------------------
# Βοηθητικές συναρτήσεις
# ---------------------------------------------------------

def safe_int(value, default=0):
    """
    Ασφαλής μετατροπή σε ακέραιο.
    """

    try:
        if value is None:
            return default

        if pd.isna(value):
            return default

        return int(value)
    except Exception:
        return default


def safe_float(value, default=0.0):
    """
    Ασφαλής μετατροπή σε δεκαδικό.
    """

    try:
        if value is None:
            return default

        if pd.isna(value):
            return default

        return float(value)
    except Exception:
        return default


def show_home_logos():
    """
    Εμφανίζει τα λογότυπα ΔΙ.ΠΑ.Ε. και ΜΟ.ΔΙ.Π. στην αρχική σελίδα.
    """

    if not DIPAE_LOGO_PATH.exists() and not MODIP_LOGO_PATH.exists():
        return

    st.markdown("---")
    st.markdown("### Φορείς")

    logo_col1, logo_col2, logo_col3 = st.columns([1, 1.2, 2.8])

    with logo_col1:
        if DIPAE_LOGO_PATH.exists():
            st.image(
                str(DIPAE_LOGO_PATH),
                width=180
            )

    with logo_col2:
        if MODIP_LOGO_PATH.exists():
            st.image(
                str(MODIP_LOGO_PATH),
                width=230
            )

    st.markdown("---")


def build_latest_year_summary(df):
    """
    Υπολογίζει βασικούς δείκτες για το πιο πρόσφατο διαθέσιμο έτος.

    Μεθοδολογία:
    - Η ανάλυση γίνεται για όλες τις κατηγορίες.
    - Οι Συνολικές Θέσεις είναι οι Αρχικές Θέσεις.
    - Η Συνολική Κάλυψη είναι Επιτυχόντες / Συνολικές Θέσεις.
    """

    if df.empty:
        return None

    years = sorted(df["year"].dropna().unique().tolist())

    if not years:
        return None

    latest_year = years[-1]

    df_latest = df[df["year"] == latest_year].copy()

    if df_latest.empty:
        return None

    department_summary = (
        df_latest
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

    department_summary["empty_positions"] = (
        department_summary["total_positions"]
        - department_summary["total_admitted"]
    )

    total_programs = safe_int(department_summary["department_code"].nunique())
    total_schools = safe_int(department_summary["school"].nunique())
    total_cities = safe_int(department_summary["city"].nunique())

    total_positions = safe_int(department_summary["total_positions"].sum())
    total_admitted = safe_int(department_summary["total_admitted"].sum())
    total_empty = safe_int(department_summary["empty_positions"].sum())

    total_coverage = (
        total_admitted / total_positions * 100
        if total_positions > 0
        else 0
    )

    available_categories = sorted(
        df_latest["exam_category"]
        .dropna()
        .unique()
        .tolist()
    )

    return {
        "latest_year": latest_year,
        "total_programs": total_programs,
        "total_schools": total_schools,
        "total_cities": total_cities,
        "total_positions": total_positions,
        "total_admitted": total_admitted,
        "total_empty": total_empty,
        "total_coverage": total_coverage,
        "available_categories": available_categories,
    }


# ---------------------------------------------------------
# Αρχικοποίηση βάσης
# ---------------------------------------------------------

try:
    initialize_database()
    load_departments()
except Exception as e:
    st.error("Υπήρξε πρόβλημα κατά την αρχικοποίηση της βάσης δεδομένων.")
    st.exception(e)
    st.stop()


# ---------------------------------------------------------
# Κύρια οθόνη
# ---------------------------------------------------------

st.title("🎓 Πλατφόρμα Ανάλυσης Εισακτέων ΔΙ.ΠΑ.Ε.")

st.markdown("""
Η εφαρμογή συγκεντρώνει, επεξεργάζεται και παρουσιάζει τα δεδομένα εισακτέων
των ενεργών προπτυχιακών προγραμμάτων σπουδών του Διεθνούς Πανεπιστημίου της Ελλάδος.

Στόχος της πλατφόρμας είναι να υποστηρίξει τη διοικητική παρακολούθηση,
τη διαχρονική σύγκριση και την τεκμηριωμένη ανάλυση των εισακτέων ανά έτος,
πρόγραμμα σπουδών, σχολή και πόλη.
""")

show_home_logos()

st.markdown("""
### Τι περιλαμβάνει η εφαρμογή

Η πλατφόρμα παρέχει:

- συνολική εικόνα εισακτέων ανά έτος,
- ανάλυση ανά ενεργό προπτυχιακό πρόγραμμα σπουδών,
- συγκεντρωτική ανάλυση ανά σχολή και πόλη,
- κατατάξεις προγραμμάτων με βάση θέσεις, επιτυχόντες, κάλυψη και βάση εισαγωγής,
- dashboard διοίκησης με βασικούς δείκτες,
- σύγκριση μεταξύ ετών,
- εξαγωγή διοικητικής αναφοράς σε Word.

### Βασικοί μεθοδολογικοί κανόνες

- Η ανάλυση γίνεται πάντα για **όλες τις κατηγορίες εισαγωγής**.
- Οι **Συνολικές Θέσεις** υπολογίζονται από τις **Αρχικές Θέσεις**.
- Η **Συνολική Κάλυψη** υπολογίζεται ως: Επιτυχόντες / Συνολικές Θέσεις.
- Η **Βάση Προγράμματος** είναι η **Βάση ΓΕΛ Ημερήσια**.
- Ο **Πρώτος Προγράμματος** είναι ο **Πρώτος ΓΕΛ Ημερήσια**.
- Δεν χρησιμοποιούνται μέσοι όροι βάσεων.
- Δεν εμφανίζονται τελικές θέσεις ή φαινόμενη μεταβολή θέσεων ως βασικοί δείκτες.
""")

st.divider()


# ---------------------------------------------------------
# Φόρτωση δεδομένων
# ---------------------------------------------------------

try:
    df = load_admissions_with_departments()
except Exception as e:
    st.error("Υπήρξε πρόβλημα κατά τη φόρτωση των δεδομένων εισακτέων.")
    st.exception(e)
    st.stop()


if df.empty:
    st.warning(
        "Δεν υπάρχουν ακόμη δεδομένα εισακτέων στη βάση. "
        "Εισάγετε πρώτα δεδομένα τοπικά και ανεβάστε τη βάση δεδομένων στο GitHub."
    )
    st.stop()


summary = build_latest_year_summary(df)

if summary is None:
    st.warning("Δεν ήταν δυνατός ο υπολογισμός της συνολικής εικόνας.")
    st.stop()


# ---------------------------------------------------------
# Διαθέσιμα δεδομένα
# ---------------------------------------------------------

st.subheader("📌 Διαθέσιμα δεδομένα")

years = sorted(df["year"].dropna().unique().tolist())

year_text = ", ".join([str(year) for year in years])

st.markdown(
    f"""
Η βάση δεδομένων περιλαμβάνει στοιχεία για τα έτη:

**{year_text}**
"""
)

latest_year = summary["latest_year"]

st.markdown(
    f"""
Για το πιο πρόσφατο διαθέσιμο έτος **{latest_year}**:

- **Ενεργά Προπτυχιακά Προγράμματα Σπουδών:** {summary["total_programs"]}
- **Σχολές:** {summary["total_schools"]}
- **Πόλεις:** {summary["total_cities"]}
- **Συνολικές Θέσεις:** {summary["total_positions"]}
- **Επιτυχόντες:** {summary["total_admitted"]}
- **Κενές Θέσεις:** {summary["total_empty"]}
- **Συνολική Κάλυψη:** {summary["total_coverage"]:.2f}%
"""
)

st.divider()


# ---------------------------------------------------------
# Βασικοί δείκτες
# ---------------------------------------------------------

st.subheader(f"📊 Συνολική εικόνα {latest_year}")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.metric(
        "Ενεργά Προπτυχιακά Προγράμματα",
        summary["total_programs"]
    )

with kpi2:
    st.metric(
        "Συνολικές Θέσεις",
        summary["total_positions"]
    )

with kpi3:
    st.metric(
        "Επιτυχόντες",
        summary["total_admitted"]
    )

with kpi4:
    st.metric(
        "Συνολική Κάλυψη",
        f'{summary["total_coverage"]:.2f}%'
    )

kpi5, kpi6, kpi7 = st.columns(3)

with kpi5:
    st.metric(
        "Κενές Θέσεις",
        summary["total_empty"]
    )

with kpi6:
    st.metric(
        "Σχολές",
        summary["total_schools"]
    )

with kpi7:
    st.metric(
        "Πόλεις",
        summary["total_cities"]
    )

st.caption(
    "Οι δείκτες αφορούν όλες τις κατηγορίες εισαγωγής του πιο πρόσφατου διαθέσιμου έτους."
)

st.divider()


# ---------------------------------------------------------
# Κατηγορίες εισαγωγής
# ---------------------------------------------------------

st.subheader("🧾 Κατηγορίες εισαγωγής")

if summary["available_categories"]:
    categories_text = "\n".join(
        [
            f"- {category}"
            for category in summary["available_categories"]
        ]
    )

    st.markdown(categories_text)
else:
    st.info("Δεν εντοπίστηκαν κατηγορίες εισαγωγής για το πιο πρόσφατο έτος.")

st.divider()


# ---------------------------------------------------------
# Οδηγός πλοήγησης
# ---------------------------------------------------------

st.subheader("🧭 Οδηγός πλοήγησης")

st.markdown("""
Χρησιμοποίησε το μενού στα αριστερά για να μεταβείς στις επιμέρους ενότητες:

- **Admissions Data**: συνοπτικοί και αναλυτικοί πίνακες εισακτέων.
- **Department Analysis**: αναλυτική εικόνα ανά προπτυχιακό πρόγραμμα σπουδών.
- **School City Analysis**: συγκεντρωτική εικόνα ανά σχολή ή πόλη.
- **Top Rankings**: κατατάξεις προγραμμάτων με βάση θέσεις, επιτυχόντες, κάλυψη και βάση.
- **Management Dashboard**: συνοπτική διοικητική εικόνα για τη διοίκηση.
- **Year Comparison**: σύγκριση δύο ετών.
- **Management Report**: παραγωγή διοικητικής αναφοράς σε Word.
""")

st.info(
    "Η online έκδοση λειτουργεί ως εφαρμογή προβολής και ανάλυσης. "
    "Η εισαγωγή νέων αρχείων γίνεται τοπικά και στη συνέχεια ενημερώνεται η βάση δεδομένων."
)