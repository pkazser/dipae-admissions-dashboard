import streamlit as st
import plotly.express as px
from modules.database_manager import load_admissions_with_departments


st.set_page_config(
    page_title="Top Rankings | ΔΙΠΑΕ",
    page_icon="🏆",
    layout="wide"
)


st.title("🏆 Top Rankings Προπτυχιακών Προγραμμάτων ΔΙ.ΠΑ.Ε.")

st.markdown("""
Σε αυτή τη σελίδα εμφανίζονται κατατάξεις των ενεργών προπτυχιακών προγραμμάτων
του ΔΙ.ΠΑ.Ε. με βάση θέσεις, επιτυχόντες, κάλυψη, κενές θέσεις και βάση εισαγωγής.

**Μεθοδολογικοί κανόνες της εφαρμογής:**

- Η ανάλυση γίνεται πάντα για **όλες τις κατηγορίες εισαγωγής**.
- Οι **Συνολικές Θέσεις** υπολογίζονται από τις **Αρχικές Θέσεις**.
- Η **Κάλυψη** υπολογίζεται ως: Επιτυχόντες / Συνολικές Θέσεις.
- Η **Βάση Προγράμματος** είναι η **Βάση ΓΕΛ Ημερήσια**.
- Ο **Πρώτος Προγράμματος** είναι ο **Πρώτος ΓΕΛ Ημερήσια**.
- Δεν εμφανίζονται τελικές θέσεις ή φαινόμενη μεταβολή θέσεων.
""")

st.divider()


def get_gel_day_scores(df_year):
    """
    Επιστρέφει Βάση Τελευταίου και Βαθμό Πρώτου από τη ΓΕΛ Ημερήσια ανά πρόγραμμα.
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


def format_base_ranking_table(df):
    """
    Πίνακας ranking βάσεων.
    Κρατάμε μόνο τις στήλες που χρειάζονται για να βρει ο χρήστης γρήγορα τις βάσεις.
    """

    display = df[
        [
            "department_name_clean",
            "school",
            "city",
            "gel_day_base_score",
        ]
    ].copy()

    display = display.rename(
        columns={
            "department_name_clean": "Προπτυχιακό Πρόγραμμα",
            "school": "Σχολή",
            "city": "Πόλη",
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


def format_first_score_ranking_table(df):
    """
    Πίνακας ranking πρώτου ΓΕΛ Ημερήσια.
    """

    display = df[
        [
            "department_name_clean",
            "school",
            "city",
            "gel_day_first_score",
        ]
    ].copy()

    display = display.rename(
        columns={
            "department_name_clean": "Προπτυχιακό Πρόγραμμα",
            "school": "Σχολή",
            "city": "Πόλη",
            "gel_day_first_score": "Πρώτος ΓΕΛ Ημ.",
        }
    )

    display["Πρώτος ΓΕΛ Ημ."] = (
        display["Πρώτος ΓΕΛ Ημ."]
        .fillna(0)
        .round(0)
        .astype(int)
    )

    return display


def format_admitted_ranking_table(df):
    """
    Πίνακας ranking επιτυχόντων.
    """

    display = df[
        [
            "department_name_clean",
            "school",
            "city",
            "total_admitted",
        ]
    ].copy()

    display = display.rename(
        columns={
            "department_name_clean": "Προπτυχιακό Πρόγραμμα",
            "school": "Σχολή",
            "city": "Πόλη",
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


def format_coverage_ranking_table(df):
    """
    Πίνακας ranking κάλυψης.
    """

    display = df[
        [
            "department_name_clean",
            "school",
            "city",
            "coverage",
        ]
    ].copy()

    display = display.rename(
        columns={
            "department_name_clean": "Προπτυχιακό Πρόγραμμα",
            "school": "Σχολή",
            "city": "Πόλη",
            "coverage": "Κάλυψη %",
        }
    )

    display["Κάλυψη %"] = display["Κάλυψη %"].round(2)

    return display


def format_empty_ranking_table(df):
    """
    Πίνακας ranking κενών θέσεων.
    """

    display = df[
        [
            "department_name_clean",
            "school",
            "city",
            "empty_positions",
        ]
    ].copy()

    display = display.rename(
        columns={
            "department_name_clean": "Προπτυχιακό Πρόγραμμα",
            "school": "Σχολή",
            "city": "Πόλη",
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


def format_positions_ranking_table(df):
    """
    Πίνακας ranking συνολικών θέσεων.
    """

    display = df[
        [
            "department_name_clean",
            "school",
            "city",
            "total_positions",
        ]
    ].copy()

    display = display.rename(
        columns={
            "department_name_clean": "Προπτυχιακό Πρόγραμμα",
            "school": "Σχολή",
            "city": "Πόλη",
            "total_positions": "Συνολικές Θέσεις",
        }
    )

    display["Συνολικές Θέσεις"] = (
        display["Συνολικές Θέσεις"]
        .fillna(0)
        .round(0)
        .astype(int)
    )

    return display


def format_full_table(df):
    """
    Πλήρης, αλλά όχι υπερφορτωμένος, πίνακας όλων των προγραμμάτων.
    Δεν περιλαμβάνει Πρώτο ΓΕΛ Ημ. και Κενές Θέσεις, ώστε ο χρήστης να βρίσκει εύκολα τις βάσεις.
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

    display["Κάλυψη %"] = display["Κάλυψη %"].round(2)

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


def style_table(df):
    """
    Styling πίνακα.

    Τα ποσοστά κάλυψης εμφανίζονται πάντα με 2 δεκαδικά και σύμβολο %.
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


def build_chart(
    display_df,
    x_col,
    y_col,
    title,
    yaxis_title,
    is_percent=False,
    is_score=False,
    integer_axis=False
):
    """
    Δημιουργεί κοινό γράφημα ranking.
    """

    fig = px.bar(
        display_df,
        x=x_col,
        y=y_col,
        text=y_col,
        hover_data=[
            col for col in ["Σχολή", "Πόλη"]
            if col in display_df.columns
        ],
        title=title
    )

    if is_percent:
        fig.update_traces(
            texttemplate="%{text:.2f}%",
            textposition="outside"
        )
    elif is_score:
        fig.update_traces(
            texttemplate="%{text:.0f}",
            textposition="outside"
        )
    else:
        fig.update_traces(
            textposition="outside"
        )

    fig.update_layout(
        xaxis_title="Προπτυχιακό Πρόγραμμα",
        yaxis_title=yaxis_title,
        uniformtext_minsize=8,
        uniformtext_mode="hide"
    )

    if is_percent:
        fig.update_layout(
            yaxis_range=[0, 100]
        )

    if is_score:
        fig.update_layout(
            yaxis_range=[0, 20000]
        )

    if integer_axis:
        fig.update_layout(
            yaxis=dict(dtick=1)
        )

    return fig


def show_ranking(
    source_df,
    sort_column,
    ascending,
    top_n,
    table_formatter,
    chart_y_col,
    title,
    is_percent=False,
    is_score=False,
    integer_axis=False
):
    """
    Εμφανίζει ranking με πίνακα και γράφημα.
    """

    ranking_df = (
        source_df
        .dropna(subset=[sort_column])
        .sort_values(sort_column, ascending=ascending)
        .head(top_n)
        .copy()
    )

    if ranking_df.empty:
        st.warning("Δεν υπάρχουν διαθέσιμα δεδομένα για αυτό το ranking.")
        return

    display_df = table_formatter(ranking_df)

    col_table, col_chart = st.columns([1, 1.4])

    with col_table:
        st.dataframe(
            style_table(display_df),
            use_container_width=True,
            hide_index=True
        )

    with col_chart:
        fig = build_chart(
            display_df=display_df,
            x_col="Προπτυχιακό Πρόγραμμα",
            y_col=chart_y_col,
            title=title,
            yaxis_title=chart_y_col,
            is_percent=is_percent,
            is_score=is_score,
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

    col_year, col_topn = st.columns(2)

    with col_year:
        selected_year = st.selectbox(
            "Έτος",
            years,
            index=len(years) - 1
        )

    with col_topn:
        top_n = st.slider(
            "Πλήθος προγραμμάτων στο ranking",
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
        st.warning("Δεν δημιουργήθηκε σύνοψη προγραμμάτων.")
        st.stop()

    total_programs = int(department_summary["department_code"].nunique())
    total_positions = int(department_summary["total_positions"].sum())
    total_admitted = int(department_summary["total_admitted"].sum())
    total_empty = int(department_summary["empty_positions"].sum())

    total_coverage = (
        total_admitted / total_positions * 100
        if total_positions > 0
        else 0
    )

    gel_day_available = int(
        department_summary["gel_day_base_score"].notna().sum()
    )

    st.subheader(f"Rankings για το έτος {selected_year}")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.metric(
            "Ενεργά Προπτυχιακά Προγράμματα",
            total_programs
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
            f"{total_coverage:.2f}%"
        )

    kpi5, kpi6 = st.columns(2)

    with kpi5:
        st.metric(
            "Κενές Θέσεις",
            total_empty
        )

    with kpi6:
        st.metric(
            "Προγράμματα με Βάση ΓΕΛ Ημ.",
            gel_day_available
        )

    st.caption(
        "Η ανάλυση γίνεται για όλες τις κατηγορίες εισαγωγής. "
        "Οι Συνολικές Θέσεις είναι οι αρχικές θέσεις. "
        "Τα rankings βάσης χρησιμοποιούν αποκλειστικά τη ΓΕΛ Ημερήσια."
    )

    st.divider()

    tab_base, tab_admitted, tab_coverage, tab_empty, tab_positions = st.tabs(
        [
            "Βάσεις ΓΕΛ Ημ.",
            "Επιτυχόντες",
            "Κάλυψη",
            "Κενές Θέσεις",
            "Θέσεις",
        ]
    )

    with tab_base:
        st.subheader("Rankings βάσης ΓΕΛ Ημερήσια")

        subtab_base_high, subtab_base_low, subtab_first_high = st.tabs(
            [
                "Υψηλότερες βάσεις",
                "Χαμηλότερες βάσεις",
                "Υψηλότερος πρώτος",
            ]
        )

        with subtab_base_high:
            show_ranking(
                source_df=department_summary,
                sort_column="gel_day_base_score",
                ascending=False,
                top_n=top_n,
                table_formatter=format_base_ranking_table,
                chart_y_col="Βάση ΓΕΛ Ημ.",
                title="Υψηλότερες βάσεις ΓΕΛ Ημερήσια",
                is_score=True
            )

        with subtab_base_low:
            show_ranking(
                source_df=department_summary,
                sort_column="gel_day_base_score",
                ascending=True,
                top_n=top_n,
                table_formatter=format_base_ranking_table,
                chart_y_col="Βάση ΓΕΛ Ημ.",
                title="Χαμηλότερες βάσεις ΓΕΛ Ημερήσια",
                is_score=True
            )

        with subtab_first_high:
            show_ranking(
                source_df=department_summary,
                sort_column="gel_day_first_score",
                ascending=False,
                top_n=top_n,
                table_formatter=format_first_score_ranking_table,
                chart_y_col="Πρώτος ΓΕΛ Ημ.",
                title="Υψηλότερα μόρια πρώτου ΓΕΛ Ημερήσια",
                is_score=True
            )

    with tab_admitted:
        st.subheader("Rankings επιτυχόντων")

        subtab_admitted_high, subtab_admitted_low = st.tabs(
            [
                "Περισσότεροι επιτυχόντες",
                "Λιγότεροι επιτυχόντες",
            ]
        )

        with subtab_admitted_high:
            show_ranking(
                source_df=department_summary,
                sort_column="total_admitted",
                ascending=False,
                top_n=top_n,
                table_formatter=format_admitted_ranking_table,
                chart_y_col="Επιτυχόντες",
                title="Προγράμματα με περισσότερους επιτυχόντες"
            )

        with subtab_admitted_low:
            show_ranking(
                source_df=department_summary,
                sort_column="total_admitted",
                ascending=True,
                top_n=top_n,
                table_formatter=format_admitted_ranking_table,
                chart_y_col="Επιτυχόντες",
                title="Προγράμματα με λιγότερους επιτυχόντες"
            )

    with tab_coverage:
        st.subheader("Rankings κάλυψης")

        subtab_coverage_high, subtab_coverage_low = st.tabs(
            [
                "Υψηλότερη κάλυψη",
                "Χαμηλότερη κάλυψη",
            ]
        )

        with subtab_coverage_high:
            show_ranking(
                source_df=department_summary,
                sort_column="coverage",
                ascending=False,
                top_n=top_n,
                table_formatter=format_coverage_ranking_table,
                chart_y_col="Κάλυψη %",
                title="Προγράμματα με υψηλότερη συνολική κάλυψη",
                is_percent=True
            )

        with subtab_coverage_low:
            show_ranking(
                source_df=department_summary,
                sort_column="coverage",
                ascending=True,
                top_n=top_n,
                table_formatter=format_coverage_ranking_table,
                chart_y_col="Κάλυψη %",
                title="Προγράμματα με χαμηλότερη συνολική κάλυψη",
                is_percent=True
            )

    with tab_empty:
        st.subheader("Rankings κενών θέσεων")

        subtab_empty_high, subtab_empty_low = st.tabs(
            [
                "Περισσότερες κενές θέσεις",
                "Λιγότερες κενές θέσεις",
            ]
        )

        with subtab_empty_high:
            show_ranking(
                source_df=department_summary,
                sort_column="empty_positions",
                ascending=False,
                top_n=top_n,
                table_formatter=format_empty_ranking_table,
                chart_y_col="Κενές Θέσεις",
                title="Προγράμματα με περισσότερες κενές θέσεις",
                integer_axis=True
            )

        with subtab_empty_low:
            show_ranking(
                source_df=department_summary,
                sort_column="empty_positions",
                ascending=True,
                top_n=top_n,
                table_formatter=format_empty_ranking_table,
                chart_y_col="Κενές Θέσεις",
                title="Προγράμματα με λιγότερες κενές θέσεις",
                integer_axis=True
            )

    with tab_positions:
        st.subheader("Rankings συνολικών θέσεων")

        subtab_positions_high, subtab_positions_low = st.tabs(
            [
                "Περισσότερες θέσεις",
                "Λιγότερες θέσεις",
            ]
        )

        with subtab_positions_high:
            show_ranking(
                source_df=department_summary,
                sort_column="total_positions",
                ascending=False,
                top_n=top_n,
                table_formatter=format_positions_ranking_table,
                chart_y_col="Συνολικές Θέσεις",
                title="Προγράμματα με περισσότερες συνολικές θέσεις"
            )

        with subtab_positions_low:
            show_ranking(
                source_df=department_summary,
                sort_column="total_positions",
                ascending=True,
                top_n=top_n,
                table_formatter=format_positions_ranking_table,
                chart_y_col="Συνολικές Θέσεις",
                title="Προγράμματα με λιγότερες συνολικές θέσεις"
            )

    st.divider()

    st.subheader("Συνοπτικός πίνακας όλων των προγραμμάτων")

    full_display = format_full_table(
        department_summary.sort_values(
            "gel_day_base_score",
            ascending=False,
            na_position="last"
        )
    )

    st.dataframe(
        style_table(full_display),
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Ο πίνακας κρατά τις βασικές πληροφορίες για γρήγορη αναζήτηση: "
        "θέσεις, επιτυχόντες, κάλυψη και Βάση ΓΕΛ Ημερήσια."
    )

except Exception as e:
    st.error("Υπήρξε πρόβλημα κατά την παραγωγή των rankings.")
    st.exception(e)