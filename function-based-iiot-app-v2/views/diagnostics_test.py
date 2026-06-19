import streamlit as st

st.set_page_config(layout="wide", page_title="Diagnostics Test")

def init_diagnostics_state():
    if "diag_tree" not in st.session_state:
        st.session_state.diag_tree = {
            "root": {"id": "root", "name": "Empty Data Base", "type": "db", "expanded": True, "selected": False, "children": ["mgdc"]},
            "mgdc": {"id": "mgdc", "name": "MGDC", "type": "plant", "expanded": True, "selected": False, "children": ["comp", "cond", "cool"]},
            "comp": {"id": "comp", "name": "Compressors", "type": "area", "expanded": False, "selected": False, "children": []},
            "cond": {"id": "cond", "name": "Condensers", "type": "area", "expanded": True, "selected": True, "children": ["c1", "c2", "c3", "c4"]},
            "c1": {"id": "c1", "name": "A-341A De-propanizer reflux condenser", "type": "machine", "expanded": False, "selected": False, "children": []},
            "c2": {"id": "c2", "name": "A-341B De-propanizer reflux condenser", "type": "machine", "expanded": False, "selected": False, "children": []},
            "c3": {"id": "c3", "name": "A-341C De-propanizer reflux condenser", "type": "machine", "expanded": False, "selected": False, "children": []},
            "c4": {"id": "c4", "name": "A-341D De-propanizer reflux condenser", "type": "machine", "expanded": False, "selected": False, "children": []},
            "cool": {"id": "cool", "name": "Coolers", "type": "area", "expanded": True, "selected": False, "children": ["cool1", "cool2"]},
            "cool1": {"id": "cool1", "name": "A-311A Regeneration Gas Cooler", "type": "machine", "expanded": True, "selected": False, "children": ["p1", "p2", "p3", "p4"]},
            "p1": {"id": "p1", "name": "MNDE", "type": "point", "expanded": False, "selected": False, "children": []},
            "p2": {"id": "p2", "name": "FNDE", "type": "point", "expanded": False, "selected": False, "children": []},
            "p3": {"id": "p3", "name": "MDE", "type": "point", "expanded": False, "selected": False, "children": []},
            "p4": {"id": "p4", "name": "FDE", "type": "point", "expanded": False, "selected": False, "children": []},
            "cool2": {"id": "cool2", "name": "A-311B Regeneration Gas Cooler", "type": "machine", "expanded": False, "selected": False, "children": []},
        }
    if "diag_active_node" not in st.session_state:
        st.session_state.diag_active_node = None
        
    # State to track if the secondary Tree slider is open
    if "show_tree_slider" not in st.session_state:
        st.session_state.show_tree_slider = True
        
    # State for the active main icon (e.g. Diagnostics vs Home)
    if "active_main_icon" not in st.session_state:
        st.session_state.active_main_icon = "diagnostics"

def toggle_node(node_id):
    st.session_state.diag_tree[node_id]["expanded"] = not st.session_state.diag_tree[node_id]["expanded"]

def select_node(node_id):
    # Select the node and automatically collapse the tree slider!
    st.session_state.diag_active_node = node_id
    st.session_state.show_tree_slider = False

def render_node(node_id, level=0):
    node = st.session_state.diag_tree[node_id]
    
    if node["type"] == "db": icon = ""
    elif node["type"] == "plant": icon = "≡" 
    else: icon = "≑"
    
    has_children = len(node["children"]) > 0
    is_expanded = node["expanded"]
    is_selected = node["selected"]
    
    c_chevr, c_chk, c_icon, c_name, c_add = st.columns([0.5, 0.5, 0.5, 6, 0.5], vertical_alignment="center")
    
    with c_chevr:
        if has_children:
            chevron = "v" if is_expanded else ">"
            if st.button(chevron, key=f"exp_{node_id}"):
                toggle_node(node_id)
                st.rerun()
        else:
            st.markdown("<div style='width: 15px;'></div>", unsafe_allow_html=True)
            
    with c_chk:
        checked = st.checkbox("", key=f"chk_{node_id}", value=is_selected, label_visibility="collapsed")
        if checked != is_selected:
            st.session_state.diag_tree[node_id]["selected"] = checked
            st.rerun()
            
    with c_icon:
        st.markdown(f"<div class='node-icon'>{icon}</div>", unsafe_allow_html=True)
        
    with c_name:
        bg_class = "node-highlight" if is_selected else ""
        st.markdown(f"<div class='{bg_class}'></div>", unsafe_allow_html=True)
        
        # When you click the name, it selects the node and collapses the slider
        if st.button(node['name'], key=f"name_{node_id}"):
            select_node(node_id)
            st.rerun()
            
    with c_add:
        if node["type"] in ["plant", "area", "machine"]:
            st.button("+", key=f"add_{node_id}")

    if has_children and is_expanded:
        with st.container():
            st.markdown(f"<div class='tree-indent'>", unsafe_allow_html=True)
            for child_id in node["children"]:
                render_node(child_id, level + 1)
            st.markdown("</div>", unsafe_allow_html=True)

def main():
    init_diagnostics_state()
    
    # EXACT CSS to build the 2-tier SPA layout
    st.markdown("""
    <style>
    /* Completely hide Streamlit's default header and padding */
    header { visibility: hidden; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    
    /* Create a fixed full-screen layout container */
    .app-layout {
        display: flex;
        width: 100vw;
        height: 100vh;
        overflow: hidden;
        background-color: #E2E8F0; /* Grey background of main page */
    }
    
    /* 1. Main Thin Sidebar (Leftmost) */
    .thin-sidebar {
        width: 60px;
        min-width: 60px;
        height: 100vh;
        background-color: #1E293B; /* Dark navy */
        display: flex;
        flex-direction: column;
        align-items: center;
        padding-top: 20px;
        z-index: 100;
        box-shadow: 2px 0 5px rgba(0,0,0,0.2);
    }
    .thin-sidebar button {
        background: transparent !important;
        border: none !important;
        color: white !important;
        font-size: 24px !important;
        padding: 10px !important;
        margin-bottom: 10px !important;
        transition: all 0.2s;
        border-radius: 8px !important;
    }
    .thin-sidebar button:hover {
        background-color: rgba(255,255,255,0.1) !important;
    }
    .icon-active button {
        background-color: #10B981 !important; /* Green active */
    }
    
    /* 2. Tree Slider (Middle) */
    .tree-slider {
        width: 350px;
        min-width: 350px;
        height: 100vh;
        background-color: #F8FAFC;
        border-right: 1px solid #CBD5E1;
        overflow-y: auto;
        padding: 15px;
        transition: margin-left 0.3s ease-in-out;
        z-index: 90;
    }
    .slider-hidden {
        margin-left: -350px; /* Slide it completely behind the thin sidebar */
    }
    
    /* 3. Main Content Area (Right) */
    .main-content {
        flex-grow: 1;
        height: 100vh;
        overflow-y: auto;
        padding: 30px;
        position: relative;
    }
    
    /* Tree Component Styling */
    .tree-slider [data-testid="column"] { min-width: 0 !important; padding: 0 !important; gap: 0 !important; }
    .tree-slider .stButton > button {
        background: transparent !important; border: none !important; color: #333 !important;
        padding: 0px 2px !important; height: 22px !important; min-height: 22px !important;
        display: flex; justify-content: flex-start; font-size: 13px !important; box-shadow: none !important;
    }
    .tree-slider .stButton > button:hover { background: rgba(0,0,0,0.05) !important; color: #000 !important; }
    .node-highlight {
        position: absolute; top: -2px; left: -100px; right: -50px; bottom: -2px;
        background-color: #DBEAFE !important; z-index: -1; pointer-events: none;
    }
    .node-icon { color: #64748B; font-size: 14px; margin-top: -2px; }
    .tree-indent { padding-left: 18px; }
    .rimap-search input { border-radius: 4px !important; border: 1px solid #10B981 !important; background: white !important; }
    .open-btn button { background-color: #10B981 !important; color: white !important; font-weight: bold !important; border-radius: 4px !important; width: 100% !important; }
    
    /* Main Content Background text */
    .empty-state {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100%;
        color: #94A3B8;
        font-size: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # ==========================================
    # DOM STRUCTURE
    # Because Streamlit uses containers, we use st.columns with exact widths to mimic flexbox
    # ==========================================
    
    slider_width = 350 if st.session_state.show_tree_slider else 0.01
    
    # 3 Columns: Thin Sidebar (Fixed width), Tree Slider (Variable width), Main Content (Flexible width)
    # Streamlit column ratios must add up
    c_thin, c_tree, c_main = st.columns([0.05, slider_width/1000 + 0.001, 1])
    
    # --- 1. THIN MAIN SIDEBAR ---
    with c_thin:
        st.markdown("<div class='thin-sidebar'>", unsafe_allow_html=True)
        
        # Home Icon
        st.button("🏠", key="nav_home")
        
        # Diagnostics Icon
        active_cls = "icon-active" if st.session_state.active_main_icon == "diagnostics" else ""
        st.markdown(f"<div class='{active_cls}'>", unsafe_allow_html=True)
        if st.button("📈", key="nav_diag"):
            st.session_state.active_main_icon = "diagnostics"
            # Toggle the tree slider when clicking the diagnostics icon!
            st.session_state.show_tree_slider = not st.session_state.show_tree_slider
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Settings Icon
        st.button("⚙️", key="nav_settings")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        
    # --- 2. TREE SLIDER ---
    with c_tree:
        if st.session_state.show_tree_slider:
            st.markdown("<div class='tree-slider'>", unsafe_allow_html=True)
            
            sc1, sc2 = st.columns([5, 1], vertical_alignment="center")
            with sc1:
                st.markdown("<div class='rimap-search'>", unsafe_allow_html=True)
                st.text_input("Search", placeholder="🔍 Search for assets", label_visibility="collapsed")
                st.markdown("</div>", unsafe_allow_html=True)
            with sc2:
                st.button("🔄")
                
            st.markdown("<hr style='margin: 10px 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)
            
            with st.container(height=600, border=False):
                render_node("root")
                
            st.markdown("<hr style='margin: 10px 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)
            
            st.markdown("<div class='open-btn'>", unsafe_allow_html=True)
            st.button("Open Selected")
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

            
    # --- 3. MAIN CONTENT ---
    with c_main:
        st.markdown("<div class='main-content'>", unsafe_allow_html=True)
        
        if not st.session_state.show_tree_slider:
            if st.button("› Reopen Diagnostics Tree"):
                st.session_state.show_tree_slider = True
                st.rerun()
                
        active_node_id = st.session_state.diag_active_node
        if active_node_id is None:
            st.markdown("<div class='empty-state'>Please select measurement from tree</div>", unsafe_allow_html=True)
        else:
            node = st.session_state.diag_tree[active_node_id]
            st.markdown(f"<h2>Analysis for: {node['name']}</h2>", unsafe_allow_html=True)
            st.markdown("<hr>", unsafe_allow_html=True)
            
            if node["type"] in ["machine", "point"]:
                tabs = st.tabs(["Trend", "Time Waveform", "Spectrum", "Average Spectrum", "Demod Spectrum"])
                with tabs[0]:
                    st.info("Interactive trend analysis goes here...")
                    st.line_chart([10, 15, 13, 20, 18, 25, 22, 30])
            else:
                st.markdown("<div class='empty-state'>Please select a specific measurement point</div>", unsafe_allow_html=True)
                
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
