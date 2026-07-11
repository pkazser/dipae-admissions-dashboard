from pathlib import Path
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"


def show_sidebar_branding():
    dipae_logo_path = ASSETS_DIR / "dipae_logo.png"
    modip_logo_path = ASSETS_DIR / "modip_logo.png"

    with st.sidebar:
        st.markdown("---")
        st.caption("🔎 Έλεγχος λογοτύπων")

        st.write("BASE_DIR")
        st.code(str(BASE_DIR))

        st.write("ASSETS_DIR")
        st.code(str(ASSETS_DIR))

        st.write("Περιεχόμενα BASE_DIR")
        try:
            st.code("\n".join([p.name for p in BASE_DIR.iterdir()]))
        except Exception as e:
            st.code(str(e))

        st.write("Περιεχόμενα assets")
        try:
            st.code("\n".join([p.name for p in ASSETS_DIR.iterdir()]))
        except Exception as e:
            st.code(str(e))

        st.write("DIPAE exists")
        st.code(str(dipae_logo_path.exists()))

        st.write("MODIP exists")
        st.code(str(modip_logo_path.exists()))

        if dipae_logo_path.exists():
            st.image(str(dipae_logo_path), width=170)
        else:
            st.error("Δεν βρέθηκε το dipae_logo.png")

        if modip_logo_path.exists():
            st.image(str(modip_logo_path), width=220)
        else:
            st.error("Δεν βρέθηκε το modip_logo.png")