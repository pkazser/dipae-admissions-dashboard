from pathlib import Path
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"


def show_sidebar_branding():
    """
    Εμφανίζει τα λογότυπα ΔΙ.ΠΑ.Ε. και ΜΟ.ΔΙ.Π. στο sidebar.
    Απλή και αξιόπιστη έκδοση χωρίς HTML.
    """

    dipae_logo_path = ASSETS_DIR / "dipae_logo.png"
    modip_logo_path = ASSETS_DIR / "modip_logo.png"

    with st.sidebar:
        st.markdown("---")
        st.caption("")

        if dipae_logo_path.exists():
            st.image(
                str(dipae_logo_path),
                width=170
            )
        else:
            st.warning("Δεν βρέθηκε το λογότυπο ΔΙ.ΠΑ.Ε.")
            st.code(str(dipae_logo_path))

        st.markdown("")

        if modip_logo_path.exists():
            st.image(
                str(modip_logo_path),
                width=220
            )
        else:
            st.warning("Δεν βρέθηκε το λογότυπο ΜΟ.ΔΙ.Π.")
            st.code(str(modip_logo_path))