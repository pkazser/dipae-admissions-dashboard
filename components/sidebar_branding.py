from pathlib import Path
import base64
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"


def image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception:
        return None


def show_sidebar_branding():
    """
    Εμφανίζει διακριτικά τα λογότυπα κάτω στο sidebar,
    χωρίς να καταλαμβάνουν χώρο από το μενού.
    """

    dipae_logo_path = ASSETS_DIR / "dipae_logo.png"
    modip_logo_path = ASSETS_DIR / "modip_logo.png"

    dipae_logo = image_to_base64(dipae_logo_path)
    modip_logo = image_to_base64(modip_logo_path)

    if not dipae_logo or not modip_logo:
        return

    css = f"""
    <style>
        section[data-testid="stSidebar"]::after {{
            content: "";
            position: fixed;
            left: 18px;
            bottom: 18px;
            width: 190px;
            height: 120px;
            background-image:
                url("data:image/png;base64,{dipae_logo}"),
                url("data:image/png;base64,{modip_logo}");
            background-repeat: no-repeat, no-repeat;
            background-size: 120px auto, 155px auto;
            background-position: left top, left 55px;
            border-top: 1px solid rgba(120, 120, 120, 0.35);
            padding-top: 12px;
            z-index: 999999;
            pointer-events: none;
        }}

        @media (max-height: 680px) {{
            section[data-testid="stSidebar"]::after {{
                display: none;
            }}
        }}
    </style>
    """

    st.markdown(css, unsafe_allow_html=True)