import streamlit as st

st.set_page_config(page_title="40px Table Test", layout="wide")

st.markdown("""
<style>
/* Reset Streamlit Margins */
.stMarkdown p {
    margin-bottom: 0px !important;
    padding-bottom: 0px !important;
}

/* Force the inner markdown container to remove padding so our 100px pole works perfectly */
div[data-testid="stMarkdownContainer"] {
    line-height: 1;
}

/* Eliminate the hidden Streamlit vertical gap between rows */
[data-testid="stVerticalBlock"] > div {
    gap: 0rem !important;
}

/* Clean horizontal rules */
hr {
    margin-top: 0px !important;
    margin-bottom: 0px !important;
    border-color: rgba(128,128,128,0.2);
}
</style>
""", unsafe_allow_html=True)

st.title("100px Row Height Test Table")
st.markdown("<hr>", unsafe_allow_html=True)

# Header Row
h1, h2, h3, h4 = st.columns([1, 2, 2, 2], gap="small", vertical_alignment="center")
h1.markdown("<div style='height: 40px; display: flex; align-items: center;'>**ID**</div>", unsafe_allow_html=True) # Let's make headers 40px
h2.markdown("**Name**")
h3.markdown("**Role**")
h4.markdown("**Status**")
st.markdown("<hr>", unsafe_allow_html=True)

# Data Rows
mock_data = [
    {"id": "EMP-001", "name": "System Administrator", "role": "Admin", "status": "Active"},
    {"id": "EMP-002", "name": "Ahmed Engineer", "role": "Engineer", "status": "Active"},
    {"id": "EMP-003", "name": "Guest Operator", "role": "Viewer", "status": "Inactive"},
]

for row in mock_data:
    c1, c2, c3, c4 = st.columns([1, 2, 2, 2], gap="small", vertical_alignment="center")
    
    # We place a single invisible 40px tall flex container here. 
    # Because the row is vertical_alignment="center", this automatically forces the whole row to be 40px tall exactly.
    c1.markdown(f"<div style='height: 40px; display: flex; align-items: center;'><span style='background-color:#f0fdf4; color:#166534; padding:2px 6px; border-radius:4px; font-family: monospace;'>{row['id']}</span></div>", unsafe_allow_html=True)
    
    c2.markdown(row['name'])
    c3.markdown(row['role'])
    c4.markdown(row['status'])
    st.markdown("<hr>", unsafe_allow_html=True)
