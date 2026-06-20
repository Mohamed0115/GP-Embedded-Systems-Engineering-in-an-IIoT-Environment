import streamlit as st
import streamlit.components.v1 as components
import os
import uuid


def new_diagnosis_view():
    """New Diagnosis page — fully custom Streamlit component.
    
    All UI (cards, modals, pin placement, charts) is rendered inside
    the custom HTML/JS component. Python only handles data persistence
    and event processing.
    """
    # ===== Initialize data model =====
    if 'diag_data' not in st.session_state:
        st.session_state.diag_data = {
            "nodes": {},
            "root_companies": []
        }
    if 'diag_view_mode' not in st.session_state:
        st.session_state.diag_view_mode = "main"
    if 'diag_view_point_id' not in st.session_state:
        st.session_state.diag_view_point_id = None

    prev_key = "_prev_diag_event"

    # ===== Declare the custom component =====
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    comp_path = os.path.join(parent_dir, "new_diagnosis_component")
    diag_comp = components.declare_component("new_diagnosis_component", path=comp_path)

    # ===== Build point data + breadcrumb for point detail mode =====
    mode = st.session_state.diag_view_mode
    point_data = None
    breadcrumb = []

    if mode == "point_detail" and st.session_state.diag_view_point_id:
        pid = st.session_state.diag_view_point_id
        nodes = st.session_state.diag_data["nodes"]
        if pid in nodes:
            point_data = nodes[pid]
            # Build breadcrumb: point → machine → zone → plant → company
            breadcrumb = _build_breadcrumb(pid, nodes)
            # Also attach parent machine data for the photo
            parent_id = nodes[pid].get("parent_id")
            if parent_id and parent_id in nodes:
                point_data = dict(point_data)  # shallow copy
                point_data["_machine_photo_b64"] = nodes[parent_id].get("photo_b64", "")
                point_data["_machine_pins"] = nodes[parent_id].get("pins", [])
                point_data["_machine_name"] = nodes[parent_id].get("name", "")

    # ===== Render the component =====
    res = diag_comp(
        diag_data=st.session_state.diag_data,
        mode=mode,
        point_data=point_data,
        breadcrumb=breadcrumb,
        user_role=st.session_state.get("user_role", "Maintenance Engineer"),
        key="new_diag_comp"
    )

    # ===== Handle events from the JS component =====
    if res and res != st.session_state.get(prev_key):
        st.session_state[prev_key] = res
        _handle_event(res)
        st.rerun()


# ============================================================================
# HELPERS
# ============================================================================

def _build_breadcrumb(point_id, nodes):
    """Walk up from point to company, return list of {id, name, type}."""
    chain = []
    current = point_id
    while current:
        node = nodes.get(current)
        if not node:
            break
        chain.append({"id": current, "name": node["name"], "type": node["type"]})
        current = node.get("parent_id")
    chain.reverse()
    return chain


def _handle_event(event):
    """Process a CRUD event sent by the JS component."""
    if not isinstance(event, dict):
        return

    action = event.get("action")
    nodes = st.session_state.diag_data["nodes"]

    # ----- ADD PLANT (+ optionally create Company) -----
    if action == "add_plant":
        data = event.get("data", {})
        company_id = data.get("company_id")

        # Create new company if needed
        if not company_id or company_id not in nodes:
            company_id = f"comp_{uuid.uuid4().hex[:8]}"
            nodes[company_id] = {
                "id": company_id, "type": "company",
                "name": data.get("company_name", "New Company"),
                "parent_id": None, "children": [],
                "status_color": "gray"
            }
            st.session_state.diag_data["root_companies"].append(company_id)

        # Create plant under company
        plant_id = f"plt_{uuid.uuid4().hex[:8]}"
        nodes[plant_id] = {
            "id": plant_id, "type": "plant",
            "name": data.get("name", "New Plant"),
            "parent_id": company_id, "children": [],
            "status_color": "gray",
            "location": data.get("location", "")
        }
        nodes[company_id]["children"].append(plant_id)

    # ----- ADD ZONE -----
    elif action == "add_zone":
        parent_id = event.get("parent_id")
        data = event.get("data", {})
        zone_id = f"zone_{uuid.uuid4().hex[:8]}"
        nodes[zone_id] = {
            "id": zone_id, "type": "zone",
            "name": data.get("name", "New Zone"),
            "parent_id": parent_id, "children": [],
            "status_color": "gray"
        }
        if parent_id in nodes:
            nodes[parent_id]["children"].append(zone_id)

    # ----- ADD MACHINE -----
    elif action == "add_machine":
        parent_id = event.get("parent_id")
        data = event.get("data", {})
        mach_id = f"mach_{uuid.uuid4().hex[:8]}"
        nodes[mach_id] = {
            "id": mach_id, "type": "machine",
            "name": data.get("name", "New Machine"),
            "parent_id": parent_id, "children": [],
            "status_color": "gray",
            "photo_b64": data.get("photo_b64", ""),
            "pins": data.get("pins", []),
            "nominal_speed": data.get("nominal_speed", 0),
            "vib_category": data.get("vib_category", "N/A"),
            "op_significance": data.get("op_significance", "N/A")
        }
        if parent_id in nodes:
            nodes[parent_id]["children"].append(mach_id)

    # ----- ADD POINT -----
    elif action == "add_point":
        parent_id = event.get("parent_id")
        data = event.get("data", {})
        point_id = f"pt_{uuid.uuid4().hex[:8]}"
        nodes[point_id] = {
            "id": point_id, "type": "point",
            "name": data.get("name", "New Point"),
            "parent_id": parent_id, "children": [],
            "status_color": "gray",
            "pin_index": data.get("pin_index", -1),
            "sensor_photo_b64": data.get("sensor_photo_b64", ""),
            "sensor_name": data.get("sensor_name", ""),
            "readings": {}
        }
        if parent_id in nodes:
            nodes[parent_id]["children"].append(point_id)
            # Link point_id into the machine's pin record
            pins = nodes[parent_id].get("pins", [])
            pin_idx = data.get("pin_index", -1)
            if 0 <= pin_idx < len(pins):
                pins[pin_idx]["point_id"] = point_id

    # ----- EDIT -----
    elif action == "edit":
        node_id = event.get("node_id")
        data = event.get("data", {})
        if node_id in nodes:
            for k, v in data.items():
                if k not in ("id", "type", "parent_id", "children", "readings"):
                    nodes[node_id][k] = v

    # ----- DELETE (recursive) -----
    elif action == "delete":
        node_id = event.get("node_id")
        _delete_node(node_id, nodes)

    # ----- CHANGE STATUS COLOR -----
    elif action == "change_status":
        node_id = event.get("node_id")
        color = event.get("color", "gray")
        if node_id in nodes:
            nodes[node_id]["status_color"] = color

    # ----- OPEN POINT PAGE -----
    elif action == "open_page":
        node_id = event.get("node_id")
        if node_id in nodes:
            st.session_state.diag_view_mode = "point_detail"
            st.session_state.diag_view_point_id = node_id

    # ----- RETURN TO MAIN VIEW -----
    elif action == "go_main":
        st.session_state.diag_view_mode = "main"
        st.session_state.diag_view_point_id = None


def _delete_node(node_id, nodes):
    """Recursively delete a node and all its descendants."""
    if node_id not in nodes:
        return
    node = nodes[node_id]
    # Delete children first
    for child_id in list(node.get("children", [])):
        _delete_node(child_id, nodes)
    # Remove from parent's children list
    parent_id = node.get("parent_id")
    if parent_id and parent_id in nodes:
        nodes[parent_id]["children"] = [
            c for c in nodes[parent_id]["children"] if c != node_id
        ]
    # Remove from root_companies if it's a company
    if node["type"] == "company":
        st.session_state.diag_data["root_companies"] = [
            c for c in st.session_state.diag_data["root_companies"] if c != node_id
        ]
    del nodes[node_id]


# ============================================================================
# PUBLIC HELPER: used by gateways.py to list all points for Location selector
# ============================================================================
def get_all_points_for_selector():
    """Return a list of (point_id, display_path) for all configured points.
    
    Each entry is like: ("pt_abc123", "RITEC > Cairo Plant > Compressors > A-341A > MNDE")
    Used by gateways.py to populate the Location (Machine - Point) selector.
    """
    if 'diag_data' not in st.session_state:
        return []
    nodes = st.session_state.diag_data["nodes"]
    points = []
    for nid, node in nodes.items():
        if node["type"] == "point":
            breadcrumb = _build_breadcrumb(nid, nodes)
            path = " > ".join([b["name"] for b in breadcrumb])
            points.append((nid, path))
    return points
