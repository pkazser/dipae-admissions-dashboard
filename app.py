import streamlit as st
from modules.database_manager import load_departments


st.set_page_config(
    page_title="Πλατφόρμα Ανάλυσης Εισακτέων ΔΙΠΑΕ",
    page_icon="🎓",
    layout="wide"
)


st.title("🎓 Πλατφόρμα Ανάλυσης Εισακτέων ΔΙ.ΠΑ.Ε.")

st.markdown("""
Η εφαρμογή θα χρησιμοποιείται για την ανάλυση των αποτελεσμάτων εισαγωγής
του Διεθνούς Πανεπιστημίου της Ελλάδος.
""")

st.divider()

st.subheader("Μητρώο Τμημάτων ΔΙ.ΠΑ.Ε.")

try:
    departments_df = load_departments()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Τμήματα", len(departments_df))

    with col2:
        st.metric("Σχολές", departments_df["school"].nunique())

    with col3:
        st.metric("Πόλεις", departments_df["city"].nunique())

    st.dataframe(
        departments_df,
        use_container_width=True,
        hide_index=True
    )

except Exception as e:
    st.error("Δεν ήταν δυνατή η ανάγνωση της βάσης δεδομένων.")
    st.exception(e)