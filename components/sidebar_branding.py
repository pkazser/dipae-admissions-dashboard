from pathlib import Path
import base64
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"


def image_to_base64(image_path):
    """
    Μετατρέπει εικόνα σε base64 ώστε να μπορεί να εμφανιστεί με HTML/CSS.
    """

    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except Exception:
        return None


def show_sidebar_branding():
    """
    Εμφανίζει τα λογότυπα ΔΙ.ΠΑ.Ε. και ΜΟ.ΔΙ.Π. κάτω αριστερά στο sidebar.
    """

    dipae_logo_path = ASSETS_DIR / "dipae_logo.png"
    modip_logo_path = ASSETS_DIR / "modip_logo.png"

    dipae_logo = image_to_base64(dipae_logo_path)
    modip_logo = image_to_base64(modip_logo_path)

    if not dipae_logo and not modip_logo:
        return

    html = """
    <style>
        .sidebar-branding {
            position: fixed;
            left: 1.1rem;
            bottom: 1.2rem;
            width: 210px;
            z-index: 999;
            background: rgba(255, 255, 255, 0.92);
            padding: 0.6rem 0.4rem;
            border-radius: 8px;
        }

        .sidebar-branding img {
            display: block;
            margin-bottom: 0.65rem;
            max-width: 190px;
            height: auto;
        }

        .sidebar-branding .dipae-logo {
            max-width: 155px;
        }

        .sidebar-branding .modip-logo {
            max-width: 190px;
        }

        @media (max-height: 720px) {
            .sidebar-branding {
                position: relative;
                left: auto;
                bottom: auto;
                margin-top: 2rem;
            }
        }
    </style>
    <div class="sidebar-branding">
    """

    if dipae_logo:
        html += f"""
        <img class="dipae-logo" src="data:image/png;base64,{dipae_logo}">
        """

    if modip_logo:
        html += f"""
        <img class="modip-logo" src="data:image/png;base64,{modip_logo}">
        """

    html += """
    </div>
    """

    st.sidebar.markdown(html, unsafe_allow_html=True)