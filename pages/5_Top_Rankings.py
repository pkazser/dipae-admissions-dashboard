import streamlit as st
import plotly.express as px
from modules.database_manager import load_admissions_with_departments


st.set_page_config(
    page_title="Top Rankings | ΔΙΠΑΕ",
    page_icon="🏆",
    layout="wide"
)


st.title("🏆 Top Rankings Τμημάτων ΔΙ.ΠΑ.Ε.")

st.markdown("""
Σε αυτή τη σελίδα εμφανίζονται κατατάξεις Τμημάτων του ΔΙ.ΠΑ.Ε. με βάση θέσεις,
επιτυχόντες, κάλυψη, κενές θέσεις και βάση εισαγωγής.

**Μεθοδολογικοί κανόνες της εφαρμογής:**

- Η ανάλυση γίνεται πάντα για **όλες τις κατηγορίες εισαγωγής**.
- Οι **Συνολικές Θέσεις** υπολογίζονται από τις **Αρχικές Θέσεις**.
- Η **Κάλυψη** υπολογίζεται ως: Επιτυχόντες / Συνολικές Θέσεις.
- Η **Βάση Τμήματος** είναι η **Βάση ΓΕΛ Ημερήσια**.
- Ο **Πρώτος Τμήματος** είναι ο **Πρώτος ΓΕΛ Ημερήσια**.
- Δεν εμφανίζονται τελικές θέσεις ή φαινόμενη μεταβολή θέσεων.
""")

st.divider()


def get_gel_day_scores(df_year):
    """
    Επιστρέφει Βάση Τελευταίου και Βαθμό Πρώτου από τη ΓΕΛ Ημερήσια ανά Τμήμα.
    Αυτές οι τιμές χρησιμοποιούνται στα rankings βάσεων.
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
    Δημιουργεί σύνοψη ανά Τμήμα για όλες τις κατηγορίες.

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


def format_display_table(df):
    """
    Ετοιμάζει πίνακα για εμφάνιση.
    """

    display = df[
        [
            "department_name_clean",
            "school",
            "city",
            "total_positions",
            "total_admitted",
            "empty_positions",
            "coverage",
            "gel_day_first_score",
            "gel_day_base_score",
        ]
    ].copy()

    display = display.rename(
        columns={
            "department_name_clean": "Τμήμα",
            "school": "Σχολή",
            "city": "Πόλη",
            "total_positions": "Συνολικές Θέσεις",
            "total_admitted": "Επιτυχόντες",
            "empty_positions": "Κενές Θέσεις",
            "coverage": "Κάλυψη %",
            "gel_day_first_score": "Πρώτος ΓΕΛ Ημ.",
            "gel_day_base_score": "Βάση ΓΕΛ Ημ.",
        }
    )

    for col in [
        "Κάλυψη %",
        "Πρώτος ΓΕΛ Ημ.",
        "Βάση ΓΕΛ Ημ.",
    ]:
        display[col] = display[col].round(2)

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


def style_rank_table(df):
    """
    Styling πίνακα rankings.
    """

    style_obj = df.style

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


def show_ranking_table_and_chart(
    df,
    sort_column,
    ascending,
    top_n,
    title,
    chart_y_title
):
    """
    Εμφανίζει πίνακα και γράφημα ranking.
    """

    ranking_df = (
        df
        .dropna(subset=[sort_column])
        .sort_values(sort_column, ascending=ascending)
        .head(top_n)
        .copy()
    )

    if ranking_df.empty:
        st.warning("Δεν υπάρχουν διαθέσιμα δεδομένα για αυτό το ranking.")
        return

    display_df = format_display_table(ranking_df)

    st.dataframe(
        style_rank_table(display_df),
        use_container_width=True,
        hide_index=True
    )

    fig = px.bar(
        display_df,
        x="Τμήμα",
        y=chart_y_title,
        text=chart_y_title,
        hover_data=["Σχολή", "Πόλη"],
        title=title
    )

    if chart_y_title == "Κάλυψη %":
        fig.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside"
        )
    elif chart_y_title in ["Βάση ΓΕΛ Ημ.", "Πρώτος ΓΕΛ Ημ."]:
        fig.update_traces(
            texttemplate="%{text:.0f}",
            textposition="outside"
        )
    else:
        fig.update_traces(
            textposition="outside"
        )

    fig.update_layout(
        xaxis_title="Τμήμα",
        yaxis_title=chart_y_title,
        uniformtext_minsize=8,
        uniformtext_mode="hide"
    )

    if chart_y_title == "Κάλυψη %":
        fig.update_layout(
            yaxis_range=[0, 110]
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

    # ---------------------------------------------------------
    # Φίλτρο έτους
    # ---------------------------------------------------------

    years = sorted(df["year"].dropna().unique().tolist())

    col_year, col_topn = st.columns(2)

    with col_year:
        selected_year = st.selectbox(
            "Έτος",
            years,
            index=len(years) - 1
        )

    with col_topn:
        top_n = st.slider(
            "Πλήθος Τμημάτων στο ranking",
            min_value=3,
            max_value=23,
            value=10,
            step=1
        )

    df_year = df[df["year"] == selected_year].copy()

    if df_year.empty:
        st.warning("Δεν υπάρχουν δεδομένα για το επιλεγμένο έτος.")
        st.stop()

    department_summary = build_department_summary(df_year)

    if department_summary.empty:
        st.warning("Δεν δημιουργήθηκε σύνοψη Τμημάτων.")
        st.stop()

    # ---------------------------------------------------------
    # KPIs
    # ---------------------------------------------------------

    total_departments = department_summary["department_code"].nunique()
    total_positions = int(department_summary["total_positions"].sum())
    total_admitted = int(department_summary["total_admitted"].sum())
    total_empty = int(department_summary["empty_positions"].sum())

    total_coverage = (
        total_admitted / total_positions * 100
        if total_positions > 0
        else 0
    )

    gel_day_available = department_summary["gel_day_base_score"].notna().sum()

    st.subheader(f"Rankings Τμημάτων για το έτος {selected_year}")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.metric(
            "Τμήματα",
            total_departments
        )

    with kpi2:
        st.metric(
            "Συνολικές Θέσεις",
            total_positions
        )

    with kpi3:
        st.metric(
            "Επιτυχόντες",
            total_admitted
        )

    with kpi4:
        st.metric(
            "Συνολική Κάλυψη",
            f"{total_coverage:.1f}%"
        )

    kpi5, kpi6 = st.columns(2)

    with kpi5:
        st.metric(
            "Κενές Θέσεις",
            total_empty
        )

    with kpi6:
        st.metric(
            "Τμήματα με Βάση ΓΕΛ Ημ.",
            gel_day_available
        )

    st.caption(
        "Η ανάλυση γίνεται για όλες τις κατηγορίες εισαγωγής. "
        "Οι Συνολικές Θέσεις είναι οι αρχικές θέσεις. "
        "Τα rankings βάσης χρησιμοποιούν αποκλειστικά τη ΓΕΛ Ημερήσια."
    )

    st.divider()

    # ---------------------------------------------------------
    # Tabs Rankings
    # ---------------------------------------------------------

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Βάσεις ΓΕΛ Ημ.",
            "Επιτυχόντες",
            "Κάλυψη",
            "Κενές Θέσεις",
        ]
    )

    with tab1:
        st.subheader("Rankings βάσης ΓΕΛ Ημερήσια")

        subtab1, subtab2 = st.tabs(
            [
                "Υψηλότερες βάσεις",
                "Χαμηλότερες βάσεις",
            ]
        )

        with subtab1:
            show_ranking_table_and_chart(
                df=department_summary,
                sort_column="gel_day_base_score",
                ascending=False,
                top_n=top_n,
                title="Υψηλότερες βάσεις ΓΕΛ Ημερήσια",
                chart_y_title="Βάση ΓΕΛ Ημ."
            )

        with subtab2:
            show_ranking_table_and_chart(
                df=department_summary,
                sort_column="gel_day_base_score",
                ascending=True,
                top_n=top_n,
                title="Χαμηλότερες βάσεις ΓΕΛ Ημερήσια",
                chart_y_title="Βάση ΓΕΛ Ημ."
            )

    with tab2:
        st.subheader("Rankings επιτυχόντων")

        subtab3, subtab4 = st.tabs(
            [
                "Περισσότεροι επιτυχόντες",
                "Λιγότεροι επιτυχόντες",
            ]
        )

        with subtab3:
            show_ranking_table_and_chart(
                df=department_summary,
                sort_column="total_admitted",
                ascending=False,
                top_n=top_n,
                title="Τμήματα με περισσότερους επιτυχόντες",
                chart_y_title="Επιτυχόντες"
            )

        with subtab4:
            show_ranking_table_and_chart(
                df=department_summary,
                sort_column="total_admitted",
                ascending=True,
                top_n=top_n,
                title="Τμήματα με λιγότερους επιτυχόντες",
                chart_y_title="Επιτυχόντες"
            )

    with tab3:
        st.subheader("Rankings κάλυψης")

        subtab5, subtab6 = st.tabs(
            [
                "Υψηλότερη κάλυψη",
                "Χαμηλότερη κάλυψη",
            ]
        )

        with subtab5:
            show_ranking_table_and_chart(
                df=department_summary,
                sort_column="coverage",
                ascending=False,
                top_n=top_n,
                title="Τμήματα με υψηλότερη συνολική κάλυψη",
                chart_y_title="Κάλυψη %"
            )

        with subtab6:
            show_ranking_table_and_chart(
                df=department_summary,
                sort_column="coverage",
                ascending=True,
                top_n=top_n,
                title="Τμήματα με χαμηλότερη συνολική κάλυψη",
                chart_y_title="Κάλυψη %"
            )

    with tab4:
        st.subheader("Rankings κενών θέσεων")

        subtab7, subtab8 = st.tabs(
            [
                "Περισσότερες κενές θέσεις",
                "Λιγότερες κενές θέσεις",
            ]
        )

        with subtab7:
            show_ranking_table_and_chart(
                df=department_summary,
                sort_column="empty_positions",
                ascending=False,
                top_n=top_n,
                title="Τμήματα με περισσότερες κενές θέσεις",
                chart_y_title="Κενές Θέσεις"
            )

        with subtab8:
            show_ranking_table_and_chart(
                df=department_summary,
                sort_column="empty_positions",
                ascending=True,
                top_n=top_n,
                title="Τμήματα με λιγότερες κενές θέσεις",
                chart_y_title="Κενές Θέσεις"
            )

    st.divider()

    # ---------------------------------------------------------
    # Πλήρης πίνακας
    # ---------------------------------------------------------

    st.subheader("Πλήρης πίνακας rankings")

    full_display = format_display_table(
        department_summary.sort_values(
            "gel_day_base_score",
            ascending=False,
            na_position="last"
        )
    )

    st.dataframe(
        style_rank_table(full_display),
        use_container_width=True,
        hide_index=True
    )

except Exception as e:
    st.error("Υπήρξε πρόβλημα κατά την παραγωγή των rankings.")
    st.exception(e)