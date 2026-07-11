import pandas as pd
import streamlit as st
import plotly.express as px
from modules.database_manager import load_admissions_with_departments


st.set_page_config(
    page_title="Dashboard Διοίκησης | ΔΙΠΑΕ",
    page_icon="📊",
    layout="wide"
)


st.title("📊 Dashboard Διοίκησης Εισακτέων ΔΙ.ΠΑ.Ε.")

st.markdown("""
Συνοπτική διοικητική εικόνα των εισακτέων του ΔΙ.ΠΑ.Ε. ανά έτος.

Το dashboard είναι σχεδιασμένο ώστε να δίνει γρήγορα τις βασικές πληροφορίες
που ενδιαφέρουν τη διοίκηση του Ιδρύματος.

**Μεθοδολογικοί κανόνες της εφαρμογής:**

- Η ανάλυση γίνεται πάντα για **όλες τις κατηγορίες εισαγωγής**.
- Οι **Συνολικές Θέσεις** υπολογίζονται από τις **Αρχικές Θέσεις**.
- Η **Συνολική Κάλυψη** υπολογίζεται ως: Επιτυχόντες / Συνολικές Θέσεις.
- Η **Βάση Προγράμματος** είναι η **Βάση ΓΕΛ Ημερήσια**.
- Η **Κάλυψη ΓΕΛ Ημερήσια** χρησιμοποιείται ως ένδειξη κάλυψης της βασικής κατηγορίας εισαγωγής.
- Δεν εμφανίζονται τελικές θέσεις ή φαινόμενη μεταβολή θέσεων.
- Δεν χρησιμοποιούνται μέσοι όροι βάσεων.
""")

st.divider()


def get_gel_day_data(df_year):
    """
    Επιστρέφει στοιχεία ΓΕΛ Ημερήσια ανά ενεργό προπτυχιακό πρόγραμμα.

    Για τις θέσεις ΓΕΛ Ημερήσια χρησιμοποιούνται οι final_positions,
    γιατί εκεί αποτυπώνονται οι τυχόν μεταφορές θέσεων προς τη ΓΕΛ Ημερήσια.
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

    return gel_data


def classify_coverage(row):
    """
    Κατηγοριοποιεί την κάλυψη κάθε προγράμματος.

    Κανόνες:
    1. Πλήρης συνολική κάλυψη:
       Συνολική κάλυψη >= 100%.

    2. Πλήρης κάλυψη ΓΕΛ Ημερήσια με μικρά κενά:
       ΓΕΛ Ημερήσια >= 100% και συνολική κάλυψη από 95% έως κάτω από 100%.

    3. Πλήρης κάλυψη ΓΕΛ Ημερήσια με σημαντικά κενά:
       ΓΕΛ Ημερήσια >= 100% αλλά συνολική κάλυψη κάτω από 95%.

    4. Μη πλήρης κάλυψη ΓΕΛ Ημερήσια:
       ΓΕΛ Ημερήσια κάτω από 100%.
    """

    total_coverage = row.get("coverage")
    gel_day_coverage = row.get("gel_day_coverage")

    if pd.isna(gel_day_coverage):
        return "Χωρίς στοιχεία ΓΕΛ Ημ."

    if total_coverage >= 99.999:
        return "Πλήρης συνολική κάλυψη"

    if gel_day_coverage >= 99.999 and total_coverage >= 95:
        return "Πλήρης ΓΕΛ Ημ. με μικρά κενά*"

    if gel_day_coverage >= 99.999:
        return "Πλήρης ΓΕΛ Ημ. με σημαντικά κενά*"

    return "Μη πλήρης ΓΕΛ Ημ."


def build_department_summary(df_year):
    """
    Δημιουργεί σύνοψη ανά ενεργό προπτυχιακό πρόγραμμα.

    Η ανάλυση γίνεται για όλες τις κατηγορίες.
    Οι συνολικές θέσεις είναι οι αρχικές θέσεις.
    Η βάση και η κάλυψη ΓΕΛ προέρχονται από τη ΓΕΛ Ημερήσια.
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

    summary["coverage_category"] = summary.apply(
        classify_coverage,
        axis=1
    )

    return summary


def build_coverage_category_counts(department_summary):
    """
    Δημιουργεί πίνακα πλήθους προγραμμάτων ανά κατηγορία κάλυψης.

    Περιλαμβάνει όλες τις βασικές κατηγορίες, ακόμη και αν κάποια έχει μηδενικό πλήθος.
    """

    category_order = [
        "Πλήρης συνολική κάλυψη",
        "Πλήρης ΓΕΛ Ημ. με μικρά κενά*",
        "Πλήρης ΓΕΛ Ημ. με σημαντικά κενά*",
        "Μη πλήρης ΓΕΛ Ημ.",
        "Χωρίς στοιχεία ΓΕΛ Ημ.",
    ]

    counts = (
        department_summary["coverage_category"]
        .value_counts()
        .reindex(category_order, fill_value=0)
        .reset_index()
    )

    counts.columns = [
        "Κατηγορία Κάλυψης",
        "Πλήθος Προγραμμάτων",
    ]

    return counts


def format_base_table(df):
    """
    Πίνακας υψηλότερων βάσεων.
    """

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

    display["Βάση ΓΕΛ Ημ."] = (
        display["Βάση ΓΕΛ Ημ."]
        .fillna(0)
        .round(0)
        .astype(int)
    )

    return display


def format_admitted_table(df):
    """
    Πίνακας περισσότερων επιτυχόντων.
    """

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

    display["Επιτυχόντες"] = (
        display["Επιτυχόντες"]
        .fillna(0)
        .round(0)
        .astype(int)
    )

    return display


def format_empty_table(df):
    """
    Πίνακας περισσότερων κενών θέσεων.
    """

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

    display["Κενές Θέσεις"] = (
        display["Κενές Θέσεις"]
        .fillna(0)
        .round(0)
        .astype(int)
    )

    return display


def format_low_coverage_table(df):
    """
    Πίνακας χαμηλότερης κάλυψης.
    """

    display = df[
        [
            "department_name_clean",
            "coverage",
        ]
    ].copy()

    display = display.rename(
        columns={
            "department_name_clean": "Προπτυχιακό Πρόγραμμα",
            "coverage": "Κάλυψη %",
        }
    )

    display["Κάλυψη %"] = display["Κάλυψη %"].round(2)

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


def style_small_table(df):
    """
    Styling μικρών διοικητικών πινάκων.

    Τα ποσοστά κάλυψης εμφανίζονται υποχρεωτικά με 2 δεκαδικά
    και με το σύμβολο %, ακόμη και όταν το Streamlit χρησιμοποιεί Styler.
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


def create_single_institution_chart(total_positions, total_admitted):
    """
    Δημιουργεί γράφημα με δύο στήλες για το σύνολο του Ιδρύματος.
    """

    chart_df = pd.DataFrame(
        {
            "Δείκτης": [
                "Συνολικές Θέσεις",
                "Επιτυχόντες",
            ],
            "Πλήθος": [
                total_positions,
                total_admitted,
            ],
        }
    )

    fig = px.bar(
        chart_df,
        x="Δείκτης",
        y="Πλήθος",
        text="Πλήθος",
        title="Συνολικές θέσεις και επιτυχόντες Ιδρύματος"
    )

    fig.update_traces(
        textposition="outside"
    )

    fig.update_layout(
        xaxis_title="",
        yaxis_title="Πλήθος"
    )

    return fig


def create_coverage_category_chart(coverage_counts):
    """
    Δημιουργεί γράφημα κατηγοριών κάλυψης προγραμμάτων.
    """

    fig = px.bar(
        coverage_counts,
        x="Κατηγορία Κάλυψης",
        y="Πλήθος Προγραμμάτων",
        text="Πλήθος Προγραμμάτων",
        title="Κατηγορίες κάλυψης προγραμμάτων"
    )

    fig.update_traces(
        textposition="outside"
    )

    fig.update_layout(
        xaxis_title="",
        yaxis_title="Πλήθος Προγραμμάτων",
        yaxis=dict(dtick=1)
    )

    return fig


def create_small_bar_chart(
    display_df,
    value_col,
    title,
    is_score=False,
    is_percent=False,
    integer_axis=False
):
    """
    Δημιουργεί μικρό γράφημα Top-5 για τις διοικητικές ενότητες.
    """

    fig = px.bar(
        display_df,
        x="Προπτυχιακό Πρόγραμμα",
        y=value_col,
        text=value_col,
        title=title
    )

    if is_score:
        fig.update_traces(
            texttemplate="%{text:.0f}",
            textposition="outside"
        )
    elif is_percent:
        fig.update_traces(
            texttemplate="%{text:.2f}%",
            textposition="outside"
        )
    else:
        fig.update_traces(
            textposition="outside"
        )

    fig.update_layout(
        xaxis_title="",
        yaxis_title=value_col,
        uniformtext_minsize=8,
        uniformtext_mode="hide"
    )

    if is_score:
        fig.update_layout(
            yaxis_range=[0, 20000]
        )

    if is_percent:
        fig.update_layout(
            yaxis_range=[0, 100]
        )

    if integer_axis:
        fig.update_layout(
            yaxis=dict(dtick=1)
        )

    return fig


def show_management_section(
    title,
    source_df,
    table_formatter,
    value_col,
    chart_title,
    is_score=False,
    is_percent=False,
    integer_axis=False
):
    """
    Εμφανίζει διοικητική ενότητα με πίνακα και γράφημα Top-5.
    """

    st.markdown(f"### {title}")

    display_df = table_formatter(source_df)

    col_table, col_chart = st.columns([1, 1.4])

    with col_table:
        st.dataframe(
            style_small_table(display_df),
            use_container_width=True,
            hide_index=True
        )

    with col_chart:
        fig = create_small_bar_chart(
            display_df=display_df,
            value_col=value_col,
            title=chart_title,
            is_score=is_score,
            is_percent=is_percent,
            integer_axis=integer_axis
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


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

    if department_summary.empty:
        st.warning("Δεν δημιουργήθηκε σύνοψη προγραμμάτων.")
        st.stop()

    coverage_counts = build_coverage_category_counts(department_summary)

    total_programs = int(department_summary["department_code"].nunique())
    total_positions = int(department_summary["total_positions"].sum())
    total_admitted = int(department_summary["total_admitted"].sum())
    total_empty_positions = int(department_summary["empty_positions"].sum())

    total_coverage = (
        total_admitted / total_positions * 100
        if total_positions > 0
        else 0
    )

    full_total_count = int(
        department_summary[
            department_summary["coverage_category"] == "Πλήρης συνολική κάλυψη"
        ]["department_code"].nunique()
    )

    full_gel_small_gaps_count = int(
        department_summary[
            department_summary["coverage_category"] == "Πλήρης ΓΕΛ Ημ. με μικρά κενά*"
        ]["department_code"].nunique()
    )

    full_gel_significant_gaps_count = int(
        department_summary[
            department_summary["coverage_category"] == "Πλήρης ΓΕΛ Ημ. με σημαντικά κενά*"
        ]["department_code"].nunique()
    )

    not_full_gel_count = int(
        department_summary[
            department_summary["coverage_category"] == "Μη πλήρης ΓΕΛ Ημ."
        ]["department_code"].nunique()
    )

    st.subheader(f"Συνολική εικόνα Ιδρύματος {selected_year}")

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
            total_empty_positions
        )

    with kpi4:
        st.metric(
            "Ποσοστό Κάλυψης",
            f"{total_coverage:.2f}%"
        )

    st.caption(
        f"Η εικόνα αφορά {total_programs} ενεργά προπτυχιακά προγράμματα σπουδών "
        "και όλες τις κατηγορίες εισαγωγής."
    )

    st.divider()

    st.subheader("Κεντρικά γραφήματα Ιδρύματος")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        institution_fig = create_single_institution_chart(
            total_positions=total_positions,
            total_admitted=total_admitted
        )

        st.plotly_chart(
            institution_fig,
            use_container_width=True
        )

    with chart_col2:
        coverage_category_fig = create_coverage_category_chart(
            coverage_counts=coverage_counts
        )

        st.plotly_chart(
            coverage_category_fig,
            use_container_width=True
        )

    st.caption(
        "* Πλήρης κάλυψη ΓΕΛ Ημερήσια σημαίνει ότι το πρόγραμμα κάλυψε το 100% "
        "των θέσεων στη βασική κατηγορία εισαγωγής. "
        "Ως μικρά κενά θεωρείται συνολική κάλυψη τουλάχιστον 95% αλλά μικρότερη από 100%."
    )

    status_col1, status_col2, status_col3, status_col4 = st.columns(4)

    with status_col1:
        st.metric(
            "Πλήρης συνολική κάλυψη",
            full_total_count
        )

    with status_col2:
        st.metric(
            "Πλήρης ΓΕΛ Ημ. με μικρά κενά*",
            full_gel_small_gaps_count
        )

    with status_col3:
        st.metric(
            "Πλήρης ΓΕΛ Ημ. με σημαντικά κενά*",
            full_gel_significant_gaps_count
        )

    with status_col4:
        st.metric(
            "Μη πλήρης ΓΕΛ Ημ.",
            not_full_gel_count
        )

    st.divider()

    st.subheader("Διοικητικές επισημάνσεις Top-5")

    top_base = (
        department_summary
        .dropna(subset=["gel_day_base_score"])
        .sort_values("gel_day_base_score", ascending=False)
        .head(5)
    )

    top_admitted = (
        department_summary
        .sort_values("total_admitted", ascending=False)
        .head(5)
    )

    top_empty = (
        department_summary
        .sort_values("empty_positions", ascending=False)
        .head(5)
    )

    low_coverage = (
        department_summary
        .sort_values("coverage", ascending=True)
        .head(5)
    )

    show_management_section(
        title="Υψηλότερες βάσεις ΓΕΛ Ημερήσια",
        source_df=top_base,
        table_formatter=format_base_table,
        value_col="Βάση ΓΕΛ Ημ.",
        chart_title="Top-5 υψηλότερες βάσεις ΓΕΛ Ημερήσια",
        is_score=True
    )

    st.divider()

    show_management_section(
        title="Περισσότεροι επιτυχόντες",
        source_df=top_admitted,
        table_formatter=format_admitted_table,
        value_col="Επιτυχόντες",
        chart_title="Top-5 περισσότερων επιτυχόντων"
    )

    st.divider()

    show_management_section(
        title="Περισσότερες κενές θέσεις",
        source_df=top_empty,
        table_formatter=format_empty_table,
        value_col="Κενές Θέσεις",
        chart_title="Top-5 περισσότερων κενών θέσεων",
        integer_axis=True
    )

    st.divider()

    show_management_section(
        title="Χαμηλότερο ποσοστό κάλυψης",
        source_df=low_coverage,
        table_formatter=format_low_coverage_table,
        value_col="Κάλυψη %",
        chart_title="Top-5 χαμηλότερης κάλυψης",
        is_percent=True
    )

except Exception as e:
    st.error("Υπήρξε πρόβλημα κατά την παραγωγή του Dashboard Διοίκησης.")
    st.exception(e)