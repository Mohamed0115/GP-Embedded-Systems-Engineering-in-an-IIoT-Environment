import streamlit as st

def apply_theme():
    th = st.session_state.get('theme', 'Dark')
    if th == "Dark":
        bg_color, text_color = "#060D13", "#E2E8F0"
        bg_img = "radial-gradient(ellipse at 50% top, rgba(35, 140, 160, 0.25) 0%, transparent 50%), radial-gradient(ellipse at 100% bottom, rgba(20, 90, 130, 0.15) 0%, transparent 60%), linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px)"
        sidebar_bg = "rgba(6, 13, 19, 0.95)"
        card_bg = "rgba(15, 30, 45, 0.4)"
        border_clr = "rgba(255, 255, 255, 0.05)"
        accent_color = "#4A90E2"
        mutated_text = "rgba(255, 255, 255, 0.6)"
        gold_color = "#FFD700"
    else:
        bg_color, text_color = "#EAE9E4", "#1A1A1A"
        bg_img = "none" 
        sidebar_bg = "rgba(225, 224, 219, 0.95)"
        card_bg = "rgba(255, 255, 255, 0.6)"
        border_clr = "rgba(0, 0, 0, 0.25)" 
        accent_color = "#3A7CA5" 
        mutated_text = "rgba(0, 0, 0, 0.6)"
        gold_color = "#A67B27" 
        
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
        .stApp {{
            background-color: {bg_color};
            background-image: {bg_img};
            background-size: 100% 100%, 100% 100%, 40px 40px, 40px 40px;
            background-attachment: fixed;
            color: {text_color};
        }}
        div[data-testid="stAppViewContainer"], div[data-testid="stHeader"] {{ background-color: transparent !important; }}
        [data-testid="stSidebar"] {{
            background-color: {sidebar_bg} !important;
            border-right: 1px solid {border_clr} !important;
            backdrop-filter: blur(10px);
        }}
        
        h1, h2, h3, h4, h5, h6, p, label, div[data-testid="stMetricValue"], [data-testid="stMetricLabel"] label {{
            color: {text_color} !important; 
        }}
        
        .gold-user {{ color: {gold_color} !important; }}
        
        .stButton > button {{
            background-color: {accent_color} !important; color: #FFFFFF !important;
            border: none !important; border-radius: 8px !important;
            padding: 0.5rem 1rem !important; font-weight: 500 !important;
            transition: all 0.2s ease;
        }}
        .stButton > button p, .stButton > button span {{ color: #FFFFFF !important; }}
        .stButton > button:hover {{ transform: translateY(-1px); box-shadow: 0 4px 12px {accent_color}66 !important; }}
        
        div[data-testid="stMetric"], .plot-container {{
            background-color: {card_bg} !important;
            backdrop-filter: blur(6px); border: 1px solid {border_clr} !important;
            padding: 1rem; border-radius: 12px; height: 100%;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
            color: {text_color} !important;
        }}
        
        .adaptive-card {{
            background-color: {card_bg} !important; 
            padding: 20px; border-radius: 10px; height: 100%;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
        }}
        
        .stTabs [data-baseweb="tab-list"] {{ border-bottom: 2px solid {border_clr} !important; }}
        .stTabs [data-baseweb="tab"] {{ background-color: transparent !important; border-bottom: 2px solid transparent !important; margin-bottom: -2px; }}
        .stTabs [data-baseweb="tab"] p, .stTabs [data-baseweb="tab"] span {{ color: {mutated_text} !important; font-weight: 500 !important; }}
        .stTabs [aria-selected="true"] p, .stTabs [aria-selected="true"] span {{ color: {accent_color} !important; }}
        .stTabs [aria-selected="true"] {{ border-bottom: 2px solid {accent_color} !important; }}
        .stTabs [data-baseweb="tab-highlight"] {{ background-color: transparent !important; }}
        
        hr, div[data-testid="stMarkdownContainer"] hr {{
            border-top: 2px solid {border_clr} !important;
            margin: 1.5rem 0 !important;
            border-bottom: none !important;
        }}
        
        div[data-testid="stVerticalBlockBorderWrapper"], div[data-testid="stVerticalBlockBorderWrapper"] > div, div[data-testid="stForm"] {{
            border-color: {border_clr} !important;
            border-style: solid !important;
            border-width: 1px !important;
            border-radius: 12px !important;
            box-shadow: none !important;
        }}
        
        .adaptive-history {{
            background-color: {card_bg} !important;
            padding: 10px; border-radius: 5px; margin-bottom: 8px; font-size: 0.9em; 
            border: 1px solid {border_clr} !important;
        }}
        .adaptive-card p, .adaptive-card h3, .adaptive-history span, .adaptive-history b {{ color: {text_color} !important; }}
    </style>
    """, unsafe_allow_html=True)
