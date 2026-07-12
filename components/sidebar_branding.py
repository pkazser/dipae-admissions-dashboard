from pathlib import Path
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"


def show_sidebar_branding():
    """
    Εμφανίζει τα λογότυπα ΔΙ.ΠΑ.Ε. και ΜΟ.ΔΙ.Π. στο sidebar
    με ασφαλή τρόπο για Streamlit Cloud.
    """

    dipae_logo_path = ASSETS_DIR / "dipae_logo.png"
    modip_logo_path = ASSETS_DIR / "modip_logo.png"

    with st.sidebar:
        st.markdown("---")

        if dipae_logo_path.exists():
            st.image(
                str(dipae_logo_path),
                width=120
            )

        if modip_logo_path.exists():
            st.image(
                str(modip_logo_path),
                width=145
            )