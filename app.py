import streamlit as st

# =============================================================================
# Unified Navigation Entry Point
# =============================================================================

# Define pages using existing files
# Note: st.Page requires Streamlit >= 1.31
support_page = st.Page("app_ui.py", title="Support Team", icon="🛡️")
narrative_page = st.Page("app_narrative.py", title="Narrative Archive", icon="📖")

st.set_page_config(
    page_title="Post-Parent Support System",
    layout="wide",
    page_icon="🛡️"
)

# Navigation Setup
pg = st.navigation([support_page, narrative_page])

# Run the selected page
pg.run()
