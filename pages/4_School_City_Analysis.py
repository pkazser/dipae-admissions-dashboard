import streamlit as st
import plotly.express as px
from modules.database_manager import load_admissions_with_departments
from components.sidebar_branding import show_sidebar_branding

st.set_page_config(
    page_title="Ανάλυση Σχολών & Πόλεων | ΔΙΠΑΕ",
    page_icon="🏫",
    layout="wide"
)
show_sidebar_branding()

st.title("🏫 Ανάλυση Σχολών και Πόλεων ΔΙ.ΠΑ.Ε.")

st.markdown("""
Σε αυτή τη σελίδα εξετάζουμε τα δεδομένα εισακτέων συγκεντρωτικά ανά **Σχολή**
ή ανά **Πόλη**.

**Μεθοδολογικοί κανόνες της εφαρμογής:**

- Η ανάλυση γίνεται πάντα για **όλες τις κατηγορίες εισαγωγής**.
- Οι **Συνολικές Θέσεις** υπολογίζονται από τις **Αρχικές Θέσεις**.
- Η **Κάλυψη** υπολογίζεται ως: Επιτυχόντες / Συνολικές Θέσεις.
- Δεν εμφανίζονται τελικές θέσεις ή φαινόμενη μεταβολή θέσεων.
- Δεν χρησιμοποιούνται μέσοι όροι βάσεων σε επίπεδο Σχολής ή Πόλης.
- Η **Βάση ΓΕΛ Ημερήσια** εμφανίζεται μόνο σε επίπεδο προπτυχιακού προγράμματος.
""")

st.divider()


def get_gel_day_scores(df_year):
    """
    Επιστρέφει τη Βάση ΓΕΛ Ημερήσια ανά πρόγραμμα.
    Χρησιμοποιείται μόνο στον αναλυτικό πίνακα προγραμμάτων.
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

    return scores


def build_department_summary(df_year):
    """
    Δημιουργεί σύνοψη ανά ενεργό προπτυχιακό πρόγραμμα σπουδών.

    Οι συνολικές θέσεις είναι οι αρχικές θέσεις.
    Η βάση προέρχεται από τη ΓΕΛ Ημερήσια.
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
        summary["gel_day_base_score"] = None

    return summary


def build_group_summary(department_summary, group_field):
    """
    Δημιουργεί σύνοψη ανά Σχολή ή Πόλη.

    Δεν υπολογίζει βάσεις ή μέσους όρους βάσεων.
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


def format_group_table(df, group_field, group_label):
    """
    Μορφοποιεί τον πίνακα ανά Σχολή ή Πόλη.
    """

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

    display["Προπτυχιακά Προγράμματα"] = (
        display["Προπτυχιακά Προγράμματα"]
        .fillna(0)
        .round(0)
        .astype(int)
    )

    display["Συνολικές Θέσεις"] = (
        display["Συνολικές Θέσεις"]
        .fillna(0)
        .round(0)
        .astype(int)
    )

    display["Επιτυχόντες"] = (
        display["Επιτυχόντες"]
        .fillna(0)
        .round(0)
        .astype(int)
    )

    display["Κενές Θέσεις"] = (
        display["Κενές Θέσεις"]
        .fillna(0)
        .round(0)
        .astype(int)
    )

    display["Κάλυψη %"] = display["Κάλυψη %"].round(2)

    return display


def format_department_table(df):
    """
    Μορφοποιεί τον αναλυτικό πίνακα προγραμμάτων.

    Κρατάμε μόνο τις στήλες που είναι χρήσιμες εδώ:
    Πρόγραμμα, Σχολή, Πόλη, Θέσεις, Επιτυχόντες, Κάλυψη, Βάση ΓΕΛ.
    """

    display = df[
        [
            "department_name_clean",
            "school",
            "city",
            "total_positions",
            "total_admitted",
            "coverage",
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
            "coverage": "Κάλυψη %",
            "gel_day_base_score": "Βάση ΓΕΛ Ημ.",
        }
    )

    display["Συνολικές Θέσεις"] = (
        display["Συνολικές Θέσεις"]
        .fillna(0)
        .round(0)
        .astype(int)
    )

    display["Επιτυχόντες"] = (
        display["Επιτυχόντες"]
        .fillna(0)
        .round(0)
        .astype(int)
    )

    display["Κάλυψη %"] = display["Κάλυψη %"].round(2)

    display["Βάση ΓΕΛ Ημ."] = (
        display["Βάση ΓΕΛ Ημ."]
        .fillna(0)
        .round(0)
        .astype(int)
    )

    return display


def highlight_empty_positions(val):
    """
    Χρωματισμός κενών θέσεων.
    """

    try:
        value = float(val)
    except Exception:
        return ""

    if value > 0:
        return "background-color: #f8d7da; color: #721c24; font-weight: bold;"
    else:
        return "background-color: #d4edda; color: #155724; font-weight: bold;"


def highlight_coverage(val):
    """
    Χρωματισμός κάλυψης.
    """

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


def style_group_table(df):
    """
    Styling για πίνακες Σχολών/Πόλεων.

    Η Κάλυψη % εμφανίζεται πάντα με 2 δεκαδικά και σύμβολο %.
    """

    style_obj = df.style

    format_dict = {}

    if "Κάλυψη %" in df.columns:
        format_dict["Κάλυψη %"] = "{:.2f}%"

    if format_dict:
        style_obj = style_obj.format(format_dict)

    if "Κενές Θέσεις" in df.columns:
        try:
            style_obj = style_obj.map(
                highlight_empty_positions,
                subset=["Κενές Θέσεις"]
            )
        except AttributeError:
            style_obj = style_obj.applymap(
                highlight_empty_positions,
                subset=["Κενές Θέσεις"]
            )

    if "Κάλυψη %" in df.columns:
        try:
            style_obj = style_obj.map(
                highlight_coverage,
                subset=["Κάλυψη %"]
            )
        except AttributeError:
            style_obj = style_obj.applymap(
                highlight_coverage,
                subset=["Κάλυψη %"]
            )

    return style_obj


def style_department_table(df):
    """
    Styling για αναλυτικό πίνακα προγραμμάτων.

    Η Κάλυψη % εμφανίζεται πάντα με 2 δεκαδικά και σύμβολο %.
    """

    style_obj = df.style

    format_dict = {}

    if "Κάλυψη %" in df.columns:
        format_dict["Κάλυψη %"] = "{:.2f}%"

    if format_dict:
        style_obj = style_obj.format(format_dict)

    if "Κάλυψη %" in df.columns:
        try:
            style_obj = style_obj.map(
                highlight_coverage,
                subset=["Κάλυψη %"]
            )
        except AttributeError:
            style_obj = style_obj.applymap(
                highlight_coverage,
                subset=["Κάλυψη %"]
            )

    return style_obj


def show_group_dashboard(group_display, group_label):
    """
    Εμφανίζει dashboard για Σχολές ή Πόλεις.
    """

    st.subheader(f"Ανάλυση ανά {group_label}")

    st.dataframe(
        style_group_table(group_display),
        use_container_width=True,
        hide_index=True
    )

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        fig_positions = px.bar(
            group_display.sort_values("Συνολικές Θέσεις", ascending=False),
            x=group_label,
            y=["Συνολικές Θέσεις", "Επιτυχόντες"],
            barmode="group",
            title=f"Συνολικές θέσεις και επιτυχόντες ανά {group_label}"
        )

        fig_positions.update_layout(
            xaxis_title=group_label,
            yaxis_title="Πλήθος",
            legend_title=""
        )

        st.plotly_chart(
            fig_positions,
            use_container_width=True
        )

    with chart_col2:
        fig_coverage = px.bar(
            group_display.sort_values("Κάλυψη %", ascending=False),
            x=group_label,
            y="Κάλυψη %",
            text="Κάλυψη %",
            title=f"Κάλυψη ανά {group_label}"
        )

        fig_coverage.update_traces(
            texttemplate="%{text:.2f}%",
            textposition="outside"
        )

        fig_coverage.update_layout(
            xaxis_title=group_label,
            yaxis_title="Κάλυψη %",
            yaxis_range=[0, 100]
        )

        st.plotly_chart(
            fig_coverage,
            use_container_width=True
        )

    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        fig_admitted = px.bar(
            group_display.sort_values("Επιτυχόντες", ascending=False),
            x=group_label,
            y="Επιτυχόντες",
            text="Επιτυχόντες",
            title=f"Επιτυχόντες ανά {group_label}"
        )

        fig_admitted.update_traces(
            textposition="outside"
        )

        fig_admitted.update_layout(
            xaxis_title=group_label,
            yaxis_title="Επιτυχόντες"
        )

        st.plotly_chart(
            fig_admitted,
            use_container_width=True
        )

    with chart_col4:
        fig_empty = px.bar(
            group_display.sort_values("Κενές Θέσεις", ascending=False),
            x=group_label,
            y="Κενές Θέσεις",
            text="Κενές Θέσεις",
            title=f"Κενές θέσεις ανά {group_label}"
        )

        fig_empty.update_traces(
            textposition="outside"
        )

        fig_empty.update_layout(
            xaxis_title=group_label,
            yaxis_title="Κενές Θέσεις"
        )

        st.plotly_chart(
            fig_empty,
            use_container_width=True
        )


try:
    df = load_admissions_with_departments()

    if df.empty:
        st.warning("Δεν υπάρχουν ακόμη δεδομένα εισακτέων στη βάση.")
        st.stop()

    years = sorted(df["year"].dropna().unique().tolist())

    col_year, col_level = st.columns(2)

    with col_year:
        selected_year = st.selectbox(
            "Έτος",
            years,
            index=len(years) - 1
        )

    with col_level:
        analysis_level = st.radio(
            "Επίπεδο ανάλυσης",
            [
                "Σχολές",
                "Πόλεις",
            ],
            horizontal=True
        )

    df_year = df[df["year"] == selected_year].copy()

    if df_year.empty:
        st.warning("Δεν υπάρχουν δεδομένα για το επιλεγμένο έτος.")
        st.stop()

    department_summary = build_department_summary(df_year)

    school_summary = build_group_summary(
        department_summary,
        "school"
    )

    city_summary = build_group_summary(
        department_summary,
        "city"
    )

    total_programs = int(department_summary["department_code"].nunique())
    total_schools = int(department_summary["school"].nunique())
    total_cities = int(department_summary["city"].nunique())

    total_positions = int(department_summary["total_positions"].sum())
    total_admitted = int(department_summary["total_admitted"].sum())
    total_empty_positions = int(department_summary["empty_positions"].sum())

    total_coverage = (
        total_admitted / total_positions * 100
        if total_positions > 0
        else 0
    )

    st.subheader(f"Συνολική εικόνα {selected_year}")

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

    kpi5, kpi6, kpi7 = st.columns(3)

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

    st.caption(
        "Η ανάλυση περιλαμβάνει όλες τις κατηγορίες εισαγωγής. "
        "Οι Συνολικές Θέσεις είναι οι αρχικές θέσεις."
    )

    st.divider()

    if analysis_level == "Σχολές":
        school_display = format_group_table(
            school_summary.sort_values("coverage", ascending=False),
            group_field="school",
            group_label="Σχολή"
        )

        show_group_dashboard(
            group_display=school_display,
            group_label="Σχολή"
        )

    else:
        city_display = format_group_table(
            city_summary.sort_values("coverage", ascending=False),
            group_field="city",
            group_label="Πόλη"
        )

        show_group_dashboard(
            group_display=city_display,
            group_label="Πόλη"
        )

    st.divider()

    st.subheader("Αναλυτικός πίνακας ενεργών προπτυχιακών προγραμμάτων")

    department_display = format_department_table(
        department_summary.sort_values(
            "gel_day_base_score",
            ascending=False,
            na_position="last"
        )
    )

    if analysis_level == "Σχολές":
        selected_group_options = ["Όλες οι Σχολές"] + sorted(
            department_display["Σχολή"].dropna().unique().tolist()
        )

        selected_group = st.selectbox(
            "Φίλτρο Σχολής στον αναλυτικό πίνακα",
            selected_group_options
        )

        if selected_group != "Όλες οι Σχολές":
            department_display = department_display[
                department_display["Σχολή"] == selected_group
            ].copy()

    else:
        selected_group_options = ["Όλες οι Πόλεις"] + sorted(
            department_display["Πόλη"].dropna().unique().tolist()
        )

        selected_group = st.selectbox(
            "Φίλτρο Πόλης στον αναλυτικό πίνακα",
            selected_group_options
        )

        if selected_group != "Όλες οι Πόλεις":
            department_display = department_display[
                department_display["Πόλη"] == selected_group
            ].copy()

    st.dataframe(
        style_department_table(department_display),
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Στον αναλυτικό πίνακα εμφανίζεται η Βάση ΓΕΛ Ημερήσια χωρίς δεκαδικά. "
        "Δεν εμφανίζονται Μόρια Πρώτου και Κενές Θέσεις ώστε ο πίνακας να είναι πιο ευανάγνωστος."
    )

except Exception as e:
    st.error("Υπήρξε πρόβλημα κατά την ανάλυση ανά Σχολή ή Πόλη.")
    st.exception(e)