import streamlit as st
import time
import base64
import uuid
import io
import copy
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates

def get_base64_from_uploaded(file):
    # Resize extremely large images at upload to fit nicely in UI and save memory
    img = Image.open(file).convert('RGBA')
    max_w = 700
    if img.width > max_w:
        ratio = max_w / float(img.width)
        img = img.resize((max_w, int(img.height * ratio)))
        
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def init_machine_state():
    if 'machines' not in st.session_state:
        st.session_state.machines = []

def delete_sensor_callback(sensor_id):
    st.session_state.temp_sensors = [s for s in st.session_state.temp_sensors if s['id'] != sensor_id]

@st.dialog("➕ Add New Machine")
def add_machine_dialog():
    st.markdown("Upload a blueprint or photo of the machine to build its digital twin.")
    new_name = st.text_input("Machine Name", placeholder="e.g. Centrifugal Pump A")
    new_type = st.text_input("Machine Type", placeholder="e.g. Pump, Motor, Fan")
    uploaded_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Save Machine", type="primary", use_container_width=True):
        if not new_name or not uploaded_file:
            st.error("Please provide both a name and an image blueprint.")
        else:
            b64_img = get_base64_from_uploaded(uploaded_file)
            st.session_state.machines.append({
                "id": str(uuid.uuid4())[:8],
                "name": new_name,
                "type": new_type if new_type else "Generic",
                "image_b64": b64_img,
                "sensors": []
            })
            st.success(f"{new_name} added!")
            time.sleep(0.5)
            st.rerun()

@st.dialog("⚙️ Sensor Configuration", width="large")
def configure_machine_dialog(machine_id):
    st.markdown("""
        <style>
            div[data-testid="stDialog"] div[role="dialog"] {
                width: 55vw !important;
                max-width: 900px !important;
            }
        </style>
    """, unsafe_allow_html=True)

    machine_idx = next((i for i, m in enumerate(st.session_state.machines) if m['id'] == machine_id), None)
    if machine_idx is None:
        return
        
    machine = st.session_state.machines[machine_idx]
    
    if 'temp_sensors' not in st.session_state:
        st.session_state.temp_sensors = copy.deepcopy(machine['sensors'])
    if 'last_click' not in st.session_state:
        st.session_state.last_click = None

    img_key = f"sandbox_{machine['id']}"

    # FLAWLESS SYNC: Intercept the new click before rendering the image so the dot appears instantly!
    click_coords = st.session_state.get(img_key)
    if click_coords is not None:
        coord_str = f"{click_coords['x']},{click_coords['y']}"
        if st.session_state.last_click != coord_str:
            st.session_state.last_click = coord_str
            new_id = 1 if len(st.session_state.temp_sensors) == 0 else max([s['id'] for s in st.session_state.temp_sensors]) + 1
            st.session_state.temp_sensors.append({
                "id": new_id,
                "x": click_coords['x'],
                "y": click_coords['y'],
                "type": "Vibration",
                "axis": "Z"
            })
        
    st.markdown(f"### Sensor Configuration: {machine['name']}")
    st.caption("Click on the machine image to place sensor markers.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_img, gap, col_tools = st.columns([1.5, 0.1, 1.2])
    
    with col_img:
        with st.container(border=True):
            image_data = base64.b64decode(machine['image_b64'])
            img = Image.open(io.BytesIO(image_data)).convert('RGBA')
            
            img.thumbnail((550, 400))
            
            draw = ImageDraw.Draw(img)
            for sensor in st.session_state.temp_sensors:
                x, y = sensor.get('x', 50), sensor.get('y', 50)
                r = 14
                draw.ellipse((x - r, y - r, x + r, y + r), fill="#3b82f6", outline="white", width=2)
                draw.text((x - 4, y - 6), str(sensor['id']), fill="white")
        
            # Just render it without capturing return value (already handled above)
            streamlit_image_coordinates(img, key=img_key)

    with col_tools:
        st.markdown("**Sensors List**")
        if len(st.session_state.temp_sensors) == 0:
            st.caption("No sensors placed yet.")
        else:
            for idx, sensor in enumerate(st.session_state.temp_sensors):
                with st.expander(f"🟢 Sensor {sensor['id']}", expanded=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        sensor['type'] = st.text_input("Type", sensor['type'], key=f"t_{sensor['id']}")
                        sensor['axis'] = st.text_input("Axis", sensor['axis'], key=f"a_{sensor['id']}")
                    with c2:
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.button("🗑️", key=f"del_{sensor['id']}", help="Remove this sensor", use_container_width=True, on_click=delete_sensor_callback, args=(sensor['id'],))
                            
        st.markdown("<br><br>", unsafe_allow_html=True)
        cf1, cf2 = st.columns([1, 1.5])
        if cf1.button("Cancel", use_container_width=True):
            if 'temp_sensors' in st.session_state: del st.session_state.temp_sensors
            if 'last_click' in st.session_state: del st.session_state.last_click
            st.rerun()
            
        if cf2.button("Save Configuration", type="primary", use_container_width=True):
            st.session_state.machines[machine_idx]['sensors'] = st.session_state.temp_sensors
            if 'temp_sensors' in st.session_state: del st.session_state.temp_sensors
            if 'last_click' in st.session_state: del st.session_state.last_click
            st.success("Saved!")
            time.sleep(0.5)
            st.rerun()

def machines_view():
    init_machine_state()

    st.title("🏭 Machines")
    st.markdown("Manage equipment libraries and configure physical sensor locations.")
    
    # Top Action Bar
    t1, t2 = st.columns([5, 1])
    with t2:
        if st.button("➕ Add New Machine", type="primary", use_container_width=True):
            add_machine_dialog()
            
    st.markdown("---")
    
    if len(st.session_state.machines) == 0:
        st.info("Your library is empty. Click 'Add New Machine' at the top right to begin.")
    else:
        cols = st.columns(3)
        for index, machine in enumerate(st.session_state.machines):
            col = cols[index % 3]
            with col:
                card_html = f"""
                <div style="background-color: var(--secondary-background-color); border: 1px solid rgba(128,128,128,0.2); border-radius: 12px; overflow: hidden; margin-bottom: 5px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                    <div style="width: 100%; height: 180px; overflow: hidden; position: relative;">
                        <img src="data:image/png;base64,{machine['image_b64']}" style="width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s ease;">
                    </div>
                    <div style="padding: 16px;">
                        <h4 style="margin: 0; color: var(--text-color); font-size: 1.2em; font-weight: 600;">{machine['name']}</h4>
                        <p style="margin: 5px 0 0 0; color: var(--text-color); opacity: 0.7; font-size: 0.9em;">
                            {machine['type']} • {len(machine['sensors'])} Sensors Mapped
                        </p>
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                
                # Action Buttons
                btn_cfg, btn_del = st.columns([4, 1])
                with btn_cfg:
                    if st.button(f"⚙️ Configure", key=f"btn_cfg_{machine['id']}", use_container_width=True):
                        if 'temp_sensors' in st.session_state: del st.session_state.temp_sensors
                        if 'last_click' in st.session_state: del st.session_state.last_click
                        configure_machine_dialog(machine['id'])
                with btn_del:
                    if st.button("🗑️", key=f"btn_del_{machine['id']}", help="Delete entire machine", type="secondary"):
                        st.session_state.machines = [m for m in st.session_state.machines if m['id'] != machine['id']]
                        st.rerun()
                st.markdown("<br>", unsafe_allow_html=True)
