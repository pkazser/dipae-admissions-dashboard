import streamlit as st
import plotly.express as px
from modules.database_manager import load_admissions_with_departments
from components.sidebar_branding import show_sidebar_branding

st.set_page_config(
    page_title="Ανάλυση Προγράμματος Σπουδών | ΔΙΠΑΕ",
    page_icon="🏛️",
    layout="wide"
)
show_sidebar_branding()

st.title("🏛️ Ανάλυση Προπτυχιακού Προγράμματος Σπουδών ΔΙ.ΠΑ.Ε.")

st.markdown("""
Σε αυτή τη σελίδα εξετάζουμε αναλυτικά κάθε ενεργό προπτυχιακό πρόγραμμα σπουδών
του ΔΙ.ΠΑ.Ε. για το επιλεγμένο έτος.

**Μεθοδολογικοί κανόνες της εφαρμογής:**

- Η ανάλυση γίνεται πάντα για **όλες τις κατηγορίες εισαγωγής**.
- Οι **Συνολικές Θέσεις** υπολογίζονται από τις **Αρχικές Θέσεις** όλων των κατηγοριών.
- Η **Συνολική Κάλυψη** υπολογίζεται ως: Επιτυχόντες / Συνολικές Θέσεις.
- Η **Βάση Προγράμματος** είναι η **Βάση ΓΕΛ Ημερήσια**.
- Ο **Πρώτος Προγράμματος** είναι ο **Πρώτος ΓΕΛ Ημερήσια**.
- Στη ΓΕΛ Ημερήσια χρησιμοποιούνται οι θέσεις μετά τις τυχόν μεταφορές από άλλες κατηγορίες.
- Δεν εμφανίζονται τελικές θέσεις ή φαινόμενη μεταβολή θέσεων ως ξεχωριστοί δείκτες.
""")

st.divider()


def safe_int(value, default=0):
    """
    Ασφαλής μετατροπή σε int.
    """

    try:
        if value is None:
            return default

        return int(value)
    except Exception:
        return default


def safe_float(value, default=None):
    """
    Ασφαλής μετατροπή σε float.
    """

    try:
        if value is None:
            return default

        return float(value)
    except Exception:
        return default


def get_gel_day_row(df_department):
    """
    Επιστρέφει τη γραμμή ΓΕΛ Ημερήσια για το επιλεγμένο πρόγραμμα.
    """

    df_gel = df_department[
        df_department["exam_category"] == "ΓΕΛ Ημερήσια"
    ].copy()

    if df_gel.empty:
        return None

    return df_gel.iloc[0]


def build_category_analysis_table(df_department):
    """
    Δημιουργεί πίνακα ανάλυσης ανά κατηγορία.

    Για τη ΓΕΛ Ημερήσια, οι θέσεις ανάλυσης λαμβάνονται από τις θέσεις
    μετά τις τυχόν μεταφορές από άλλες κατηγορίες.

    Για τις υπόλοιπες κατηγορίες, χρησιμοποιούνται οι αρχικές θέσεις.
    """

    df_display = df_department.copy()

    df_display["analysis_positions"] = df_display["initial_positions"]

    gel_mask = df_display["exam_category"] == "ΓΕΛ Ημερήσια"

    df_display.loc[gel_mask, "analysis_positions"] = (
        df_display.loc[gel_mask, "final_positions"]
        .fillna(df_display.loc[gel_mask, "initial_positions"])
    )

    df_display["empty_positions"] = (
        df_display["analysis_positions"]
        - df_display["admitted"]
    )

    df_display["category_coverage"] = (
        df_display["admitted"]
        / df_display["analysis_positions"]
        * 100
    )

    category_table = df_display[
        [
            "exam_category",
            "admission_type",
            "scientific_fields",
            "analysis_positions",
            "admitted",
            "empty_positions",
            "category_coverage",
            "first_score",
            "base_score",
        ]
    ].copy()

    category_table = category_table.rename(
        columns={
            "exam_category": "Κατηγορία",
            "admission_type": "Είδος Θέσης",
            "scientific_fields": "Επιστημονικά Πεδία",
            "analysis_positions": "Θέσεις",
            "admitted": "Επιτυχόντες",
            "empty_positions": "Κενές Θέσεις",
            "category_coverage": "Κάλυψη Κατηγορίας %",
            "first_score": "Βαθμός Πρώτου",
            "base_score": "Βάση Τελευταίου",
        }
    )

    for col in [
        "Θέσεις",
        "Επιτυχόντες",
        "Κενές Θέσεις",
    ]:
        category_table[col] = category_table[col].fillna(0).astype(int)

    category_table["Κάλυψη Κατηγορίας %"] = (
        category_table["Κάλυψη Κατηγορίας %"]
        .fillna(0)
        .round(2)
    )

    for col in [
        "Βαθμός Πρώτου",
        "Βάση Τελευταίου",
    ]:
        category_table[col] = (
            category_table[col]
            .fillna(0)
            .round(0)
            .astype(int)
        )

    return category_table


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


def highlight_gel_day_row(row):
    """
    Επισημαίνει ολόκληρη τη γραμμή της ΓΕΛ Ημερήσια.
    """

    category = str(row.get("Κατηγορία", ""))

    if category == "ΓΕΛ Ημερήσια":
        return [
            "background-color: #fff3cd; color: #664d03; font-weight: bold;"
            for _ in row
        ]

    return ["" for _ in row]


def style_category_table(df):
    """
    Styling αναλυτικού πίνακα ανά κατηγορία.

    Η στήλη Κάλυψη Κατηγορίας % εμφανίζεται πάντα με 2 δεκαδικά
    και με το σύμβολο %, ακόμη και όταν το Streamlit χρησιμοποιεί Styler.
    """

    style_obj = df.style

    format_dict = {}

    if "Κάλυψη Κατηγορίας %" in df.columns:
        format_dict["Κάλυψη Κατηγορίας %"] = "{:.2f}%"

    if format_dict:
        style_obj = style_obj.format(format_dict)

    try:
        style_obj = style_obj.apply(
            highlight_gel_day_row,
            axis=1
        )

        if "Κενές Θέσεις" in df.columns:
            style_obj = style_obj.map(
                highlight_empty_positions,
                subset=["Κενές Θέσεις"]
            )

        return style_obj

    except AttributeError:
        style_obj = df.style

        if format_dict:
            style_obj = style_obj.format(format_dict)

        style_obj = style_obj.apply(
            highlight_gel_day_row,
            axis=1
        )

        if "Κενές Θέσεις" in df.columns:
            style_obj = style_obj.applymap(
                highlight_empty_positions,
                subset=["Κενές Θέσεις"]
            )

        return style_obj


try:
    df = load_admissions_with_departments()

    if df.empty:
        st.warning("Δεν υπάρχουν ακόμη δεδομένα εισακτέων στη βάση.")
        st.stop()

    years = sorted(df["year"].dropna().unique().tolist())

    col_year, col_department = st.columns(2)

    with col_year:
        selected_year = st.selectbox(
            "Έτος",
            years,
            index=len(years) - 1
        )

    df_year = df[df["year"] == selected_year].copy()

    departments = (
        df_year[
            [
                "department_code",
                "department_name_clean",
                "department_name_raw",
                "school",
                "city",
            ]
        ]
        .drop_duplicates()
        .sort_values("department_name_clean")
    )

    department_options = departments["department_name_clean"].dropna().tolist()

    with col_department:
        selected_department = st.selectbox(
            "Προπτυχιακό Πρόγραμμα Σπουδών",
            department_options
        )

    df_department = df_year[
        df_year["department_name_clean"] == selected_department
    ].copy()

    if df_department.empty:
        st.warning("Δεν υπάρχουν δεδομένα για το επιλεγμένο πρόγραμμα.")
        st.stop()

    department_info = df_department.iloc[0]

    department_code = department_info.get("department_code", "")
    ministry_department_code = department_info.get("ministry_department_code", "")
    school = department_info.get("school", "")
    city = department_info.get("city", "")
    website = department_info.get("website", "")

    st.subheader(selected_department)

    info_col1, info_col2, info_col3, info_col4 = st.columns(4)

    with info_col1:
        st.metric("Κωδικός ΔΙ.ΠΑ.Ε.", department_code)

    with info_col2:
        st.metric("Κωδικός Υπουργείου", ministry_department_code)

    with info_col3:
        st.metric("Σχολή", school)

    with info_col4:
        st.metric("Πόλη", city)

    if website and str(website).lower() not in ["nan", "none"]:
        st.markdown(f"🌐 Ιστοσελίδα: {website}")

    st.divider()

    total_positions = safe_int(df_department["initial_positions"].sum())
    total_admitted = safe_int(df_department["admitted"].sum())

    empty_positions = total_positions - total_admitted

    total_coverage = (
        total_admitted / total_positions * 100
        if total_positions > 0
        else 0
    )

    gel_day_row = get_gel_day_row(df_department)

    if gel_day_row is not None:
        gel_day_positions = safe_int(
            gel_day_row.get("final_positions"),
            default=safe_int(gel_day_row.get("initial_positions"))
        )

        gel_day_admitted = safe_int(
            gel_day_row.get("admitted")
        )

        gel_day_empty_positions = (
            gel_day_positions
            - gel_day_admitted
        )

        gel_day_coverage = (
            gel_day_admitted / gel_day_positions * 100
            if gel_day_positions > 0
            else None
        )

        gel_day_first_score = safe_float(
            gel_day_row.get("first_score")
        )

        gel_day_base_score = safe_float(
            gel_day_row.get("base_score")
        )
    else:
        gel_day_positions = 0
        gel_day_admitted = 0
        gel_day_empty_positions = 0
        gel_day_coverage = None
        gel_day_first_score = None
        gel_day_base_score = None

    st.subheader("Βασικοί δείκτες Προγράμματος")

    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        st.metric(
            "Συνολικές Θέσεις",
            total_positions
        )

    with kpi_col2:
        st.metric(
            "Επιτυχόντες",
            total_admitted
        )

    with kpi_col3:
        st.metric(
            "Κενές Θέσεις",
            empty_positions
        )

    with kpi_col4:
        st.metric(
            "Συνολική Κάλυψη",
            f"{total_coverage:.2f}%"
        )

    kpi_col5, kpi_col6, kpi_col7, kpi_col8 = st.columns(4)

    with kpi_col5:
        st.metric(
            "ΓΕΛ Ημερήσια Θέσεις",
            gel_day_positions
        )

    with kpi_col6:
        st.metric(
            "ΓΕΛ Ημερήσια Επιτυχόντες",
            gel_day_admitted
        )

    with kpi_col7:
        if gel_day_coverage is not None:
            st.metric(
                "Κάλυψη ΓΕΛ Ημερήσια",
                f"{gel_day_coverage:.2f}%"
            )
        else:
            st.metric(
                "Κάλυψη ΓΕΛ Ημερήσια",
                "—"
            )

    with kpi_col8:
        if gel_day_base_score is not None:
            st.metric(
                "Βάση ΓΕΛ Ημερήσια",
                f"{gel_day_base_score:.0f}"
            )
        else:
            st.metric(
                "Βάση ΓΕΛ Ημερήσια",
                "—"
            )

    kpi_col9, kpi_col10 = st.columns(2)

    with kpi_col9:
        if gel_day_first_score is not None:
            st.metric(
                "Πρώτος ΓΕΛ Ημερήσια",
                f"{gel_day_first_score:.0f}"
            )
        else:
            st.metric(
                "Πρώτος ΓΕΛ Ημερήσια",
                "—"
            )

    with kpi_col10:
        st.metric(
            "Κενές ΓΕΛ Ημερήσια",
            gel_day_empty_positions
        )

    st.caption(
        "Η συνολική κάλυψη υπολογίζεται για όλες τις κατηγορίες εισαγωγής. "
        "Η Βάση και ο Πρώτος προέρχονται από τη ΓΕΛ Ημερήσια. "
        "Οι ΓΕΛ Ημερήσιες Θέσεις λαμβάνουν υπόψη τυχόν μεταφορές θέσεων προς τη ΓΕΛ Ημερήσια."
    )

    st.divider()

    st.subheader("Αναλυτικός πίνακας ανά κατηγορία εισαγωγής")

    category_table = build_category_analysis_table(df_department)

    st.dataframe(
        style_category_table(category_table),
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Στη στήλη «Θέσεις», για τη ΓΕΛ Ημερήσια εμφανίζονται οι θέσεις μετά τις τυχόν μεταφορές, "
        "ενώ για τις υπόλοιπες κατηγορίες εμφανίζονται οι αρχικές θέσεις. "
        "Οι Συνολικές Θέσεις του προγράμματος υπολογίζονται πάντα από τις αρχικές θέσεις όλων των κατηγοριών."
    )

    st.divider()

    st.subheader("Γραφήματα ανά κατηγορία")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        fig_positions = px.bar(
            category_table,
            x="Κατηγορία",
            y=["Θέσεις", "Επιτυχόντες"],
            barmode="group",
            title="Θέσεις και επιτυχόντες ανά κατηγορία"
        )

        fig_positions.update_layout(
            xaxis_title="Κατηγορία",
            yaxis_title="Πλήθος",
            legend_title=""
        )

        st.plotly_chart(
            fig_positions,
            use_container_width=True
        )

    with chart_col2:
        coverage_chart_df = category_table.copy()
        coverage_chart_df["Επισήμανση"] = coverage_chart_df["Κατηγορία"].apply(
            lambda x: "ΓΕΛ Ημερήσια" if x == "ΓΕΛ Ημερήσια" else "Λοιπές κατηγορίες"
        )

        fig_coverage = px.bar(
            coverage_chart_df,
            x="Κατηγορία",
            y="Κάλυψη Κατηγορίας %",
            text="Κάλυψη Κατηγορίας %",
            color="Επισήμανση",
            color_discrete_map={
                "ΓΕΛ Ημερήσια": "#f59f00",
                "Λοιπές κατηγορίες": "#1f77b4",
            },
            title="Κάλυψη ανά κατηγορία"
        )

        fig_coverage.update_traces(
            texttemplate="%{text:.2f}%",
            textposition="outside"
        )

        fig_coverage.update_layout(
            xaxis_title="Κατηγορία",
            yaxis_title="Κάλυψη %",
            yaxis_range=[0, 100],
            legend_title=""
        )

        st.plotly_chart(
            fig_coverage,
            use_container_width=True
        )

    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        empty_chart_df = category_table.copy()
        empty_chart_df["Επισήμανση"] = empty_chart_df["Κατηγορία"].apply(
            lambda x: "ΓΕΛ Ημερήσια" if x == "ΓΕΛ Ημερήσια" else "Λοιπές κατηγορίες"
        )

        fig_empty = px.bar(
            empty_chart_df,
            x="Κατηγορία",
            y="Κενές Θέσεις",
            text="Κενές Θέσεις",
            color="Επισήμανση",
            color_discrete_map={
                "ΓΕΛ Ημερήσια": "#f59f00",
                "Λοιπές κατηγορίες": "#1f77b4",
            },
            title="Κενές θέσεις ανά κατηγορία"
        )

        fig_empty.update_traces(
            textposition="outside"
        )

        fig_empty.update_layout(
            xaxis_title="Κατηγορία",
            yaxis_title="Κενές Θέσεις",
            yaxis=dict(dtick=1),
            legend_title=""
        )

        st.plotly_chart(
            fig_empty,
            use_container_width=True
        )

    with chart_col4:
        score_chart_df = category_table.copy()
        score_chart_df["Επισήμανση"] = score_chart_df["Κατηγορία"].apply(
            lambda x: "ΓΕΛ Ημερήσια" if x == "ΓΕΛ Ημερήσια" else "Λοιπές κατηγορίες"
        )

        fig_base_score = px.bar(
            score_chart_df,
            x="Κατηγορία",
            y="Βάση Τελευταίου",
            text="Βάση Τελευταίου",
            color="Επισήμανση",
            color_discrete_map={
                "ΓΕΛ Ημερήσια": "#f59f00",
                "Λοιπές κατηγορίες": "#1f77b4",
            },
            title="Βάση τελευταίου ανά κατηγορία"
        )

        fig_base_score.update_traces(
            texttemplate="%{text:.0f}",
            textposition="outside"
        )

        fig_base_score.update_layout(
            xaxis_title="Κατηγορία",
            yaxis_title="Βάση Τελευταίου",
            yaxis_range=[0, 20000],
            legend_title=""
        )

        st.plotly_chart(
            fig_base_score,
            use_container_width=True
        )

except Exception as e:
    st.error("Υπήρξε πρόβλημα κατά την ανάλυση προγράμματος.")
    st.exception(e)