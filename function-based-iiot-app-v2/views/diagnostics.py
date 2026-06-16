import streamlit as st
import math

# ============================================================================
# CATEGORY COLORS (applied to name TEXT via CSS :has() selector)
# ============================================================================
COLORS = {
    "db": "#1E293B", "plant": "#0F766E", "area": "#1D4ED8",
    "machine": "#7C3AED", "point": "#BE185D",
}
# Colored circle emoji per category
CIRCLES = {
    "db": "⚫", "plant": "🟢", "area": "🔵",
    "machine": "🟡", "point": "🔴",
}

# ============================================================================
# DATABASE HOOKS — Your DB friend modifies these
# ============================================================================
def db_add_area(plant_id, name):
    """DB HOOK: Insert area. Replace with real DB call."""
    import uuid
    nid = f"area_{uuid.uuid4().hex[:6]}"
    st.session_state.diag_tree[nid] = {"name": name, "type": "area", "expanded": False, "children": []}
    st.session_state.diag_tree[plant_id]["children"].append(nid)

def db_add_machine(area_id, name, speed, vib, op_sig, rotatory):
    """DB HOOK: Insert machine. Replace with real DB call."""
    import uuid
    nid = f"mach_{uuid.uuid4().hex[:6]}"
    st.session_state.diag_tree[nid] = {"name": name, "type": "machine", "expanded": False, "children": []}
    st.session_state.diag_tree[area_id]["children"].append(nid)

def db_add_point(machine_id, name):
    """DB HOOK: Insert point. Replace with real DB call."""
    import uuid
    nid = f"pt_{uuid.uuid4().hex[:6]}"
    st.session_state.diag_tree[nid] = {"name": name, "type": "point", "expanded": False, "children": []}
    st.session_state.diag_tree[machine_id]["children"].append(nid)

# ============================================================================
# STATE
# ============================================================================
def _init():
    if "diag_tree" not in st.session_state:
        st.session_state.diag_tree = {
            "root": {"name": "Empty Data Base", "type": "db", "expanded": True, "children": ["mgdc"]},
            "mgdc": {"name": "MGDC", "type": "plant", "expanded": True, "children": ["comp","cond","cool"]},
            "comp": {"name": "Compressors", "type": "area", "expanded": False, "children": []},
            "cond": {"name": "Condensers", "type": "area", "expanded": True, "children": ["c1","c2","c3","c4"]},
            "c1": {"name": "A-341A De-pr...", "type": "machine", "expanded": False, "children": ["c1p1","c1p2","c1p3","c1p4"]},
            "c1p1": {"name": "MNDE", "type": "point", "expanded": False, "children": []},
            "c1p2": {"name": "MDE", "type": "point", "expanded": False, "children": []},
            "c1p3": {"name": "FNDE", "type": "point", "expanded": False, "children": []},
            "c1p4": {"name": "FDE", "type": "point", "expanded": False, "children": []},
            "c2": {"name": "A-341B De-pr...", "type": "machine", "expanded": False, "children": []},
            "c3": {"name": "A-341C De-pr...", "type": "machine", "expanded": False, "children": []},
            "c4": {"name": "A-341D De-pr...", "type": "machine", "expanded": False, "children": []},
            "cool": {"name": "Coolers", "type": "area", "expanded": True, "children": ["cl1","cl2"]},
            "cl1": {"name": "A-311A Rege...", "type": "machine", "expanded": True, "children": ["p1","p2","p3","p4"]},
            "p1": {"name": "MNDE", "type": "point", "expanded": False, "children": []},
            "p2": {"name": "FNDE", "type": "point", "expanded": False, "children": []},
            "p3": {"name": "MDE", "type": "point", "expanded": False, "children": []},
            "p4": {"name": "FDE", "type": "point", "expanded": False, "children": []},
            "cl2": {"name": "A-311B Regen...", "type": "machine", "expanded": True, "children": ["q1","q2","q3","q4"]},
            "q1": {"name": "MNDE", "type": "point", "expanded": False, "children": []},
            "q2": {"name": "MDE", "type": "point", "expanded": False, "children": []},
            "q3": {"name": "FDE", "type": "point", "expanded": False, "children": []},
            "q4": {"name": "FNDE", "type": "point", "expanded": False, "children": []},
        }
    if "diag_active_node" not in st.session_state:
        st.session_state.diag_active_node = None

# ============================================================================
# SEARCH
# ============================================================================
def _matches(nid, q):
    t = st.session_state.diag_tree
    if q.lower() in t[nid]["name"].lower():
        return True
    return any(_matches(c, q) for c in t[nid]["children"])

# ============================================================================
# ADD DIALOGS — Streamlit popup dialogs
# ============================================================================
@st.dialog("Add Area")
def _dlg_add_area(parent_id):
    st.markdown(f"**Adding area to:** {st.session_state.diag_tree[parent_id]['name']}")
    name = st.text_input("Area Name", placeholder="Enter area name")
    if st.button("✅ Add Area", type="primary", use_container_width=True):
        if name.strip():
            db_add_area(parent_id, name.strip())
            st.rerun()
    if st.button("Cancel", use_container_width=True):
        st.rerun()

@st.dialog("Add Machine")
def _dlg_add_machine(parent_id):
    st.markdown(f"**Adding machine to:** {st.session_state.diag_tree[parent_id]['name']}")
    name = st.text_input("Machine Name", placeholder="Machine name")
    speed = st.number_input("Nominal Speed (HZ)", value=0.0, min_value=0.0)
    vib = st.selectbox("Vibration Category", ["N/A","VERY_SMOOTH","SMOOTH","STANDARD","ROUGH","VERY_ROUGH"])
    op = st.selectbox("Operational Significance", ["N/A","ONE","TWO","THREE","FOUR","FIVE"])
    rot = st.checkbox("Rotatory Machine", value=True)
    if st.button("✅ Add Machine", type="primary", use_container_width=True):
        if name.strip():
            db_add_machine(parent_id, name.strip(), speed, vib, op, rot)
            st.rerun()
    if st.button("Cancel", use_container_width=True):
        st.rerun()

@st.dialog("Add Measurement Point")
def _dlg_add_point(parent_id):
    st.markdown(f"**Adding point to:** {st.session_state.diag_tree[parent_id]['name']}")
    name = st.text_input("Point Name", placeholder="e.g. MNDE, FDE, MDE...")
    if st.button("✅ Add Point", type="primary", use_container_width=True):
        if name.strip():
            db_add_point(parent_id, name.strip())
            st.rerun()
    if st.button("Cancel", use_container_width=True):
        st.rerun()

def _open_add_dialog(nid):
    t = st.session_state.diag_tree
    if t[nid]["type"] == "plant": _dlg_add_area(nid)
    elif t[nid]["type"] == "area": _dlg_add_machine(nid)
    elif t[nid]["type"] == "machine": _dlg_add_point(nid)

# ============================================================================
# TREE NODE RENDERER — uses variable-width spacer column for indentation
# ============================================================================
def _node(nid, level=0, search=""):
    t = st.session_state.diag_tree
    n = t[nid]
    if search and not _matches(nid, search):
        return
    has_kids = len(n["children"]) > 0
    is_exp = n["expanded"]
    is_active = st.session_state.diag_active_node == nid
    tips = {"plant": "Add Area", "area": "Add Machine", "machine": "Add Point"}
    cat = n["type"]
    color = COLORS.get(cat, "#334155")
    show_plus = cat in tips

    # --- INDENTATION via variable spacer column ---
    spacer_w = max(level * 0.06, 0.001)
    chev_w = 0.06
    chk_w = 0.06
    name_w = max(0.68 - spacer_w, 0.15)
    plus_w = 0.07 if show_plus else 0.001
    circle = CIRCLES.get(cat, "⚫")

    cols = st.columns([spacer_w, chev_w, chk_w, name_w, plus_w])

    # Col 0: Spacer
    with cols[0]:
        st.empty()

    # Col 1: Chevron
    with cols[1]:
        if has_kids:
            if st.button("▾" if is_exp else "▸", key=f"e_{nid}"):
                t[nid]["expanded"] = not is_exp
                st.rerun()

    # Col 2: Checkbox
    with cols[2]:
        st.checkbox("x", key=f"k_{nid}", label_visibility="collapsed")

    # Col 3: Name with colored circle prefix
    with cols[3]:
        display_name = f"{circle} {n['name']}"
        if st.button(display_name, key=f"n_{nid}", use_container_width=True,
                     type="primary" if is_active else "secondary"):
            st.session_state.diag_active_node = nid
            st.rerun()

    # Col 4: + button
    with cols[4]:
        if show_plus:
            if st.button("+", key=f"a_{nid}", help=tips[cat]):
                _open_add_dialog(nid)

    # Recurse children
    if has_kids and is_exp:
        for cid in n["children"]:
            _node(cid, level + 1, search)

# ============================================================================
# CSS — Override theme_engine for sidebar, match Rimap reference
# ============================================================================
def _css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    /* ===== FORCE LIGHT MODE on sidebar (Chrome + Edge + Firefox) ===== */
    /* forced-color-adjust: none prevents Edge "Auto dark mode" from overriding */
    html body .stApp [data-testid="stSidebar"],
    html body .stApp [data-testid="stSidebar"] *,
    html body .stApp [data-testid="stSidebar"] *::before,
    html body .stApp [data-testid="stSidebar"] *::after {
        color-scheme: light !important;
        forced-color-adjust: none !important;
        -ms-high-contrast-adjust: none !important;
    }
    /* Edge-specific: force light on ALL interactive elements */
    html body .stApp [data-testid="stSidebar"] input,
    html body .stApp [data-testid="stSidebar"] button,
    html body .stApp [data-testid="stSidebar"] select,
    html body .stApp [data-testid="stSidebar"] textarea,
    html body .stApp [data-testid="stSidebar"] label,
    html body .stApp [data-testid="stSidebar"] [role="checkbox"],
    html body .stApp [data-testid="stSidebar"] [data-baseweb] {
        color-scheme: light !important;
        forced-color-adjust: none !important;
    }
    /* Force sidebar content divs to NOT get dark backgrounds */
    html body .stApp [data-testid="stSidebar"] [data-testid="stSidebarContent"] > div {
        background-color: transparent !important;
        background-image: none !important;
    }

    /* ===== Edge dark mode: explicit overrides via media query ===== */
    @media (prefers-color-scheme: dark) {
        html body .stApp [data-testid="stSidebar"],
        html body .stApp [data-testid="stSidebar"] > div,
        html body .stApp section[data-testid="stSidebar"],
        html body .stApp section[data-testid="stSidebar"] > div,
        html body .stApp [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
            background: #F1F5F9 !important;
            background-color: #F1F5F9 !important;
            background-image: none !important;
        }
        html body .stApp [data-testid="stSidebar"] [data-testid="stSidebarContent"] * {
            color: #334155 !important;
        }
        html body .stApp [data-testid="stSidebar"] .stButton > button {
            background: transparent !important;
            background-color: transparent !important;
            color: #334155 !important;
        }
        html body .stApp [data-testid="stSidebar"] [data-testid="stCheckbox"] input[type="checkbox"] {
            background: #FFFFFF !important;
            background-color: #FFFFFF !important;
            border-color: #94A3B8 !important;
        }
        html body .stApp [data-testid="stSidebar"] [data-testid="stTextInput"] input {
            background: #FFFFFF !important;
            background-color: #FFFFFF !important;
            color: #333333 !important;
            -webkit-text-fill-color: #333333 !important;
        }
    }

    /* ===== SIDEBAR BACKGROUND: light grey ===== */
    html body .stApp [data-testid="stSidebar"],
    html body .stApp [data-testid="stSidebar"] > div,
    html body .stApp section[data-testid="stSidebar"],
    html body .stApp section[data-testid="stSidebar"] > div,
    html body .stApp [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        background: #F1F5F9 !important;
        background-color: #F1F5F9 !important;
        background-image: none !important;
    }

    /* ===== ALL SIDEBAR TEXT: dark (but NOT collapse button icon) ===== */
    html body .stApp [data-testid="stSidebar"] [data-testid="stSidebarContent"] * {
        color: #334155 !important;
        font-family: 'Inter', 'Segoe UI', system-ui, sans-serif !important;
    }

    /* ===== HIDE the collapse button "keyboard_double" icon text ===== */
    html body .stApp [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"],
    html body .stApp [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] * {
        font-size: 0px !important;
        overflow: hidden !important;
    }
    html body .stApp [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button {
        font-size: 0px !important;
        width: 32px !important;
        height: 32px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: transparent !important;
        border: none !important;
    }
    html body .stApp [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] svg {
        width: 20px !important;
        height: 20px !important;
        fill: #64748B !important;
        color: #64748B !important;
    }
    /* Also hide any stray icon text in the sidebar header area */
    html body .stApp [data-testid="stSidebar"] [data-testid="stSidebarHeader"] * {
        font-size: 0px !important;
        line-height: 0 !important;
    }
    html body .stApp [data-testid="stSidebar"] [data-testid="stSidebarHeader"] svg {
        font-size: initial !important;
    }

    /* ===== SIDEBAR WIDTH ===== */
    html body .stApp [data-testid="stSidebar"][aria-expanded="true"] {
        width: 300px !important;
    }
    html body .stApp [data-testid="stSidebar"][aria-expanded="false"] {
        width: 0px !important; min-width: 0px !important;
    }

    /* ===== KILL ALL SPACING between rows ===== */
    html body .stApp [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0px !important;
    }
    html body .stApp [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
        padding-top: 0px !important;
        padding-bottom: 0px !important;
        margin-top: 0px !important;
        margin-bottom: 0px !important;
    }
    html body .stApp [data-testid="stSidebar"] [data-testid="stElementContainer"] {
        padding: 0px !important;
        margin: 0px !important;
    }

    /* ===== ROW LAYOUT: spaced horizontal alignment ===== */
    html body .stApp [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
        gap: 4px !important;
        align-items: center !important;
        margin: 0px !important;
        padding: 0px !important;
        flex-wrap: nowrap !important;
    }
    html body .stApp [data-testid="stSidebar"] [data-testid="column"] {
        padding: 0 2px !important;
        min-width: 0px !important;
        overflow: hidden !important;
    }

    /* ===== KILL MARKDOWN SPACING (from hidden divs) ===== */
    html body .stApp [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        margin: 0px !important; padding: 0px !important;
    }
    html body .stApp [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        margin: 0px !important; padding: 0px !important;
        line-height: 1.2 !important; font-size: 13px !important;
    }

    /* ===== ALL TREE BUTTONS: compact, transparent, LEFT-ALIGNED ===== */
    html body .stApp [data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #334155 !important;
        padding: 2px 4px !important;
        height: 26px !important;
        min-height: 20px !important;
        max-height: 28px !important;
        font-size: 13px !important;
        font-family: 'Inter', 'Segoe UI', sans-serif !important;
        transform: none !important;
        border-radius: 3px !important;
        line-height: 1.2 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        /* FORCE LEFT ALIGNMENT */
        display: flex !important;
        justify-content: flex-start !important;
        align-items: center !important;
        text-align: left !important;
    }
    /* Force inner div and p left-aligned too */
    html body .stApp [data-testid="stSidebar"] .stButton > button > div {
        display: flex !important;
        justify-content: flex-start !important;
        align-items: center !important;
        text-align: left !important;
        width: 100% !important;
    }
    html body .stApp [data-testid="stSidebar"] .stButton > button p,
    html body .stApp [data-testid="stSidebar"] .stButton > button span {
        color: #334155 !important;
        font-size: 13px !important;
        text-align: left !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    html body .stApp [data-testid="stSidebar"] .stButton > button:hover {
        background: #E2E8F0 !important;
        transform: none !important;
        box-shadow: none !important;
    }

    /* ===== ACTIVE ROW (primary button) ===== */
    html body .stApp [data-testid="stSidebar"] .stButton > button[kind="primary"],
    html body .stApp [data-testid="stSidebar"] .stButton > button[data-testid="baseButton-primary"] {
        background: #BFDBFE !important;
    }
    html body .stApp [data-testid="stSidebar"] .stButton > button[kind="primary"] p,
    html body .stApp [data-testid="stSidebar"] .stButton > button[data-testid="baseButton-primary"] p {
        color: #1E293B !important;
    }

    /* ===== + BUTTON: plain text, NO border, NO box (match reference) ===== */
    html body .stApp [data-testid="stSidebar"] [data-testid="column"]:last-child .stButton > button {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        justify-content: center !important;
        text-align: center !important;
        font-size: 15px !important;
        font-weight: 400 !important;
        width: auto !important;
        height: auto !important;
        min-height: 0 !important;
        max-height: none !important;
        padding: 0 2px !important;
        color: #64748B !important;
        line-height: 1.2 !important;
    }
    html body .stApp [data-testid="stSidebar"] [data-testid="column"]:last-child .stButton > button > div {
        justify-content: center !important;
    }
    html body .stApp [data-testid="stSidebar"] [data-testid="column"]:last-child .stButton > button:hover {
        background: transparent !important;
        color: #3B82F6 !important;
    }
    html body .stApp [data-testid="stSidebar"] [data-testid="column"]:last-child .stButton > button p {
        text-align: center !important;
        color: #64748B !important;
        font-size: 15px !important;
        line-height: 1.2 !important;
    }
    html body .stApp [data-testid="stSidebar"] [data-testid="column"]:last-child .stButton > button:hover p {
        color: #3B82F6 !important;
    }

    /* ===== CHECKBOX: compact, ALWAYS light mode ===== */
    html body .stApp [data-testid="stSidebar"] [data-testid="stCheckbox"] {
        min-height: 0px !important;
        height: 22px !important;
        padding: 0px !important;
    }
    html body .stApp [data-testid="stSidebar"] [data-testid="stCheckbox"] label {
        min-height: 0px !important;
        padding: 0px !important;
        gap: 0px !important;
    }
    html body .stApp [data-testid="stSidebar"] [data-testid="stCheckbox"] [data-testid="stWidgetLabel"] {
        display: none !important;
    }
    /* Force checkbox input to always look light (Edge + Chrome) */
    html body .stApp [data-testid="stSidebar"] [data-testid="stCheckbox"] input[type="checkbox"] {
        appearance: auto !important;
        -webkit-appearance: checkbox !important;
        -moz-appearance: checkbox !important;
        width: 14px !important;
        height: 14px !important;
        background: #FFFFFF !important;
        background-color: #FFFFFF !important;
        border: 1.5px solid #94A3B8 !important;
        border-radius: 2px !important;
        color-scheme: light !important;
        accent-color: #3B82F6 !important;
        filter: none !important;
    }
    /* Force Edge checkbox SVG/container to NOT invert */
    html body .stApp [data-testid="stSidebar"] [data-testid="stCheckbox"] svg {
        filter: none !important;
        color: #94A3B8 !important;
    }
    html body .stApp [data-testid="stSidebar"] [data-testid="stCheckbox"] [data-testid="stMarkdownContainer"],
    html body .stApp [data-testid="stSidebar"] [data-testid="stCheckbox"] > div {
        background: transparent !important;
        filter: none !important;
    }

    /* ===== CONTAINER BORDERS: kill ===== */
    html body .stApp [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"],
    html body .stApp [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] > div {
        border: none !important;
        border-width: 0px !important;
        box-shadow: none !important;
        background: transparent !important;
    }

    /* ===== HR ===== */
    html body .stApp [data-testid="stSidebar"] hr {
        margin: 6px 0px !important;
        border-color: #CBD5E1 !important;
    }

    /* ===== SEARCH INPUT ===== */
    html body .stApp [data-testid="stSidebar"] [data-testid="stTextInput"] input {
        border: 1.5px solid #34D399 !important;
        border-radius: 6px !important;
        background: white !important;
        color: #333 !important;
        -webkit-text-fill-color: #333 !important;
        height: 36px !important;
        font-size: 13px !important;
    }
    html body .stApp [data-testid="stSidebar"] [data-testid="stTextInput"] > div > div > div {
        background: white !important;
    }

    /* ===== NAV BUTTONS via :has() sibling selector =====
       Streamlit renders <div class='nav-btn'> and the button in SEPARATE
       stElementContainer siblings. So we target the button's container
       that is the next sibling of the marker container. */
    html body .stApp [data-testid="stSidebar"] [data-testid="stElementContainer"]:has(.nav-btn) + [data-testid="stElementContainer"] .stButton > button {
        background: #4B5563 !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        height: 38px !important;
        min-height: 38px !important;
        max-height: 38px !important;
        border-radius: 6px !important;
        justify-content: center !important;
        text-align: center !important;
        padding: 6px 16px !important;
        border: none !important;
        width: 100% !important;
    }
    html body .stApp [data-testid="stSidebar"] [data-testid="stElementContainer"]:has(.nav-btn) + [data-testid="stElementContainer"] .stButton > button > div {
        justify-content: center !important;
    }
    html body .stApp [data-testid="stSidebar"] [data-testid="stElementContainer"]:has(.nav-btn) + [data-testid="stElementContainer"] .stButton > button p,
    html body .stApp [data-testid="stSidebar"] [data-testid="stElementContainer"]:has(.nav-btn) + [data-testid="stElementContainer"] .stButton > button span {
        color: white !important;
        font-size: 13px !important;
        text-align: center !important;
    }
    html body .stApp [data-testid="stSidebar"] [data-testid="stElementContainer"]:has(.nav-btn) + [data-testid="stElementContainer"] .stButton > button:hover {
        background: #374151 !important;
    }
    /* Open Selected = green */
    html body .stApp [data-testid="stSidebar"] [data-testid="stElementContainer"]:has(.open-btn) + [data-testid="stElementContainer"] .stButton > button {
        background: #10B981 !important;
    }
    html body .stApp [data-testid="stSidebar"] [data-testid="stElementContainer"]:has(.open-btn) + [data-testid="stElementContainer"] .stButton > button:hover {
        background: #059669 !important;
    }
    /* Refresh = slightly lighter */
    html body .stApp [data-testid="stSidebar"] [data-testid="stElementContainer"]:has(.refresh-btn) + [data-testid="stElementContainer"] .stButton > button {
        background: #6B7280 !important;
        height: 32px !important;
        min-height: 32px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# SIDEBAR
# ============================================================================
def _sidebar():
    _css()

    # Back button
    st.sidebar.markdown("<div class='nav-btn'>", unsafe_allow_html=True)
    if st.sidebar.button("← Back to Main Menu", use_container_width=True, key="back_nav"):
        st.session_state.current_view = "Dashboard 📊"
        st.rerun()
    st.sidebar.markdown("</div>", unsafe_allow_html=True)

    # Search
    search = st.sidebar.text_input("S", placeholder="🔍 Search for assets",
                                   label_visibility="collapsed", key="diag_search")

    # Refresh
    st.sidebar.markdown("<div class='nav-btn refresh-btn'>", unsafe_allow_html=True)
    st.sidebar.button("🔄 Refresh", use_container_width=True, key="refresh_tree")
    st.sidebar.markdown("</div>", unsafe_allow_html=True)

    st.sidebar.markdown("<hr>", unsafe_allow_html=True)

    # Tree
    with st.sidebar.container(height=450, border=False):
        _node("root", search=search)

    st.sidebar.markdown("<hr>", unsafe_allow_html=True)

    # Open Selected
    st.sidebar.markdown("<div class='nav-btn open-btn'>", unsafe_allow_html=True)
    st.sidebar.button("Open Selected", use_container_width=True, key="open_sel")
    st.sidebar.markdown("</div>", unsafe_allow_html=True)

# ============================================================================
# CONTENT PAGES
# ============================================================================
def _machine_page(nid):
    t = st.session_state.diag_tree
    n = t[nid]
    st.markdown(f"### Machine: {n['name']}")
    tabs = st.tabs(["Dashboards","Reports","Overall Table","Attached Sensors","Media"])
    with tabs[0]:
        st.markdown("## Machine Health")
        parent = next((t[p]["name"] for p in t if nid in t[p].get("children",[])), "Unknown")
        st.markdown(f"**Location:** {parent}")
        st.markdown("**Nominal Speed:** 25.000 HZ / 1500.00 RPM")
        st.markdown("""<div style="text-align:center;padding:20px;">
            <div style="width:200px;height:12px;background:linear-gradient(to right,#EF4444,#F59E0B,#EAB308,#22C55E);border-radius:6px;margin:10px auto;"></div>
            <div style="font-weight:bold;color:#64748B;">Health Rating</div>
            <div style="font-size:48px;font-weight:bold;color:#EF4444;">0%</div></div>""", unsafe_allow_html=True)
        st.line_chart([0]*10)
    for i in range(1,5):
        with tabs[i]:
            st.info("Content placeholder")

def _point_page(nid):
    t = st.session_state.diag_tree
    n = t[nid]
    parent = next((t[p]["name"] for p in t if nid in t[p].get("children",[])), "Unknown")
    st.markdown(f"### Point: {n['name']} — {parent}")
    tabs = st.tabs(["Trend","Time Waveform","Spectrum","Average Spectrum","Demod Spectrum"])
    with tabs[0]:
        st.line_chart([10,15,13,20,18,25,22,30,28,35])
    with tabs[1]:
        st.line_chart([math.sin(i*0.3)*5+10 for i in range(100)])
    for i in range(2,5):
        with tabs[i]:
            st.info("Analysis placeholder")

# ============================================================================
# MAIN
# ============================================================================
def diagnostics_view():
    _init()
    _sidebar()

    active = st.session_state.diag_active_node
    if active is None:
        st.markdown("""<div style="display:flex;justify-content:center;align-items:center;
            height:60vh;color:#94A3B8;font-size:20px;">
            Please select measurement from tree</div>""", unsafe_allow_html=True)
    else:
        n = st.session_state.diag_tree[active]
        if n["type"] == "machine":
            _machine_page(active)
        elif n["type"] == "point":
            _point_page(active)
        else:
            st.markdown("""<div style="display:flex;justify-content:center;align-items:center;
                height:60vh;color:#94A3B8;font-size:20px;">
                Select a machine or measurement point</div>""", unsafe_allow_html=True)
