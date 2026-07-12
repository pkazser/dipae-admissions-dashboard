from pathlib import Path
import base64
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"


def image_to_base64(image_path):
    """
    Μετατρέπει εικόνα σε base64 για ασφαλή εμφάνιση στο Streamlit Cloud.
    """

    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception:
        return None


def show_sidebar_branding():
    """
    Εμφανίζει τα λογότυπα ΔΙ.ΠΑ.Ε. και ΜΟ.ΔΙ.Π. σταθερά κάτω στο sidebar,
    χωρίς να καταλαμβάνουν χώρο από το μενού πλοήγησης.
    """

    dipae_logo_path = ASSETS_DIR / "dipae_logo.png"
    modip_logo_path = ASSETS_DIR / "modip_logo.png"

    dipae_logo = image_to_base64(dipae_logo_path)
    modip_logo = image_to_base64(modip_logo_path)

    if not dipae_logo and not modip_logo:
        return

    html = f"""
<style>
    .dipae-sidebar-branding {{
        position: fixed;
        left: 18px;
        bottom: 16px;
        width: 210px;
        z-index: 999999;
        background: rgba(240, 242, 246, 0.96);
        padding-top: 10px;
        border-top: 1px solid rgba(120, 120, 120, 0.35);
        pointer-events: none;
    }}

    .dipae-sidebar-branding img {{
        display: block;
        height: auto;
        margin-bottom: 10px;
    }}

    .dipae-sidebar-branding .dipae-logo {{
        width: 115px;
    }}

    .dipae-sidebar-branding .modip-logo {{
        width: 145px;
    }}

    @media (max-height: 680px) {{
        .dipae-sidebar-branding {{
            display: none;
        }}
    }}
</style>

<div class="dipae-sidebar-branding">
"""

    if dipae_logo:
        html += f"""
    <img class="dipae-logo" src="data:image/png;base64,{dipae_logo}" />
"""

    if modip_logo:
        html += f"""
    <img class="modip-logo" src="data:image/png;base64,{modip_logo}" />
"""

    html += """
</div>
"""

    st.sidebar.markdown(
        html,
        unsafe_allow_html=True
    )