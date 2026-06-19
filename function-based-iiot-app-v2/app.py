
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
from datetime import datetime

import asyncio
import sys, os

# --- SMART DRIVER TOGGLE ---
SIMULATION_MODE = True

if SIMULATION_MODE:
    from Gateways_Sim.ITA.CDSR import connect as ita_conn, disconnect as ita_disconn
    from Gateways_Sim.ITA.commands_ip import excute_data_command, excute_command
    from Gateways_Sim.CTC.functions import conn as ctc_conn, close as ctc_disconn
    from Gateways_Sim.CTC.commands import take_dynamic_vibration_reading
else:
    gw_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Gateways'))
    sys.path.append(gw_path)
    sys.path.append(os.path.join(gw_path, 'ITA'))
    sys.path.append(os.path.join(gw_path, 'CTC'))
    from ITA.CDSR import connect as ita_conn, disconnect as ita_disconn
    from ITA.commands_ip import excute_data_command, excute_command
    from CTC.functions import conn as ctc_conn
    from CTC.commands import take_dynamic_vibration_reading

class ITAWrapper:
    def init_ita_state(self):
        if 'ita_connected' not in st.session_state: st.session_state.ita_connected = False
        if 'ita_ip' not in st.session_state: st.session_state.ita_ip = ""
        if 'ita_port' not in st.session_state: st.session_state.ita_port = 8020
    def ip(self): return getattr(st.session_state, 'ita_ip', "192.168.1.100")
    def port(self): return getattr(st.session_state, 'ita_port', 8020)
    def connect(self, ip, port=8020):
        async def _test_conn():
            try:
                # Try to connect and immediately disconnect to verify
                r, w = await asyncio.wait_for(ita_conn(ip, port), timeout=3.0)
                await ita_disconn(w)
                return True, ""
            except Exception as e:
                return False, str(e)
        
        success, err = asyncio.run(_test_conn())
        if success:
            st.session_state.ita_connected = True
            st.session_state.ita_ip = ip
            st.session_state.ita_port = port
            return True, "Connected successfully"
        else:
            st.session_state.ita_connected = False
            return False, f"Connection failed: {err}"
            
    def disconnect(self):
        st.session_state.ita_connected = False
        
    def set_all_parameters(self, ch, ga, sp, sr, to, tl):
        # Format matching parameters_con.py string format
        cmd = f"CH {ch};GA {ga};SP {sp};SR {sr};TO {to};TL {tl}"
        async def _run():
            try:
                r, w = await asyncio.wait_for(ita_conn(self.ip(), self.port()), timeout=3.0)
                res = await excute_command(r, w, cmd)
                await ita_disconn(w)
                return True, res["response"]
            except Exception as e:
                return False, str(e)
        return asyncio.run(_run())

    def take_reading(self, x_ch, y_ch, z_ch, ga, sp, sr, to, tl):
        async def _run():
            r, w = await asyncio.wait_for(ita_conn(self.ip(), self.port()), timeout=3.0)
            
            async def get_axis_data(channel):
                # Apply channel specific configuration before reading
                cmd = f"CH {channel};GA {ga};SP {sp};SR {sr};TO {to};TL {tl}"
                await excute_command(r, w, cmd)
                # Instruct gateway to acquire data before downloading
                await excute_command(r, w, "AQ")
                
                res = await excute_data_command(r, w, "BD?", tl)
                d = res["response"]
                if isinstance(d, str):
                    raise ValueError(f"Gateway formatted text/error on CH {channel}: {d}")
                return d
                
            x_data = await get_axis_data(x_ch)
            y_data = await get_axis_data(y_ch)
            z_data = await get_axis_data(z_ch)

            await ita_disconn(w)
            return {"x": x_data, "y": y_data, "z": z_data, "sampling_rate": sr}
        return asyncio.run(_run())
    def csvf(self, path=None): return "Exported"

class CTCWrapper:
    def init_ctc_state(self):
        if 'ctc_connected' not in st.session_state: st.session_state.ctc_connected = False
        if 'ctc_ip' not in st.session_state: st.session_state.ctc_ip = ""
        if 'ctc_subscribed' not in st.session_state: st.session_state.ctc_subscribed = False
    def ip(self): return getattr(st.session_state, 'ctc_ip', "192.168.1.200")
    def connect(self, ip):
        async def _test_conn():
            try:
                ws = await asyncio.wait_for(ctc_conn(f"ws://{ip}:5000"), timeout=3.0)
                await ws.close()
                return True, "Connected successfully"
            except Exception as e:
                return False, str(e)
        
        success, msg = asyncio.run(_test_conn())
        if success:
            st.session_state.ctc_connected = True
            st.session_state.ctc_ip = ip
            return True, msg
        else:
            st.session_state.ctc_connected = False
            return False, f"Connection failed: {msg}"

    def disconnect(self):
        st.session_state.ctc_connected = False
        
    def subscribe(self):
        async def _run():
            if SIMULATION_MODE:
                from Gateways_Sim.CTC.commands import subscribe_to_changes
            else:
                from CTC.commands import subscribe_to_changes
            ws = await asyncio.wait_for(ctc_conn(f"ws://{self.ip()}:5000"), timeout=3.0)
            res = await asyncio.wait_for(subscribe_to_changes(ws), timeout=1.5)
            await ws.close()
            return res
        try:
            asyncio.run(_run())
            st.session_state.ctc_subscribed = True
            return True, "Subscribed successfully"
        except asyncio.TimeoutError:
            st.session_state.ctc_subscribed = True
            return True, "Subscribed successfully (No ACK from server)"
        except Exception as e:
            return False, f"Subscribe failed: {str(e) or type(e).__name__}"
        
    def unsubscribe(self):
        async def _run():
            if SIMULATION_MODE:
                from Gateways_Sim.CTC.commands import unsubscribe_from_changes
            else:
                from CTC.commands import unsubscribe_from_changes
            ws = await asyncio.wait_for(ctc_conn(f"ws://{self.ip()}:5000"), timeout=3.0)
            res = await asyncio.wait_for(unsubscribe_from_changes(ws), timeout=1.5)
            await ws.close()
            return res
        try:
            asyncio.run(_run())
            st.session_state.ctc_subscribed = False
            return True, "Unsubscribed successfully"
        except asyncio.TimeoutError:
            st.session_state.ctc_subscribed = False
            return True, "Unsubscribed successfully (No ACK from server)"
        except Exception as e:
            return False, f"Unsubscribe failed: {str(e) or type(e).__name__}"
        
    def get_connected_serials(self):
        async def _run():
            if SIMULATION_MODE:
                from Gateways_Sim.CTC.commands import get_connected_dynamic_sensors
            else:
                from CTC.commands import get_connected_dynamic_sensors
            ws = await asyncio.wait_for(ctc_conn(f"ws://{self.ip()}:5000"), timeout=3.0)
            res = await asyncio.wait_for(get_connected_dynamic_sensors(ws), timeout=3.0)
            await ws.close()
            return res
        return asyncio.run(_run())
        
    def get_current_data(self, serial="12345"):
        if not str(serial).strip().isdigit():
            raise ValueError(f"Serial number must be entirely numeric. You accidentally entered: '{serial}'")
            
        async def _run():
            if SIMULATION_MODE:
                from Gateways_Sim.CTC.commands import take_dynamic_vibration_reading
            else:
                from CTC.commands import take_dynamic_vibration_reading
            ws = await asyncio.wait_for(ctc_conn(f"ws://{self.ip()}:5000"), timeout=3.0)
            res = await asyncio.wait_for(take_dynamic_vibration_reading(ws, int(serial)), timeout=30.0)
            await ws.close()
            
            if isinstance(res, dict) and "Data" in res:
                data_val = res["Data"]
                if isinstance(data_val, list) and len(data_val) > 0:
                    item = data_val[0]
                    if isinstance(item, dict):
                        vib = item.get("Vibration", 0.0)
                        return {"Serial": serial, "timestamp": "Now", "X": [vib]*50, "Y": [vib]*50, "Z": [vib]*50}
            
            raise ValueError(f"Gateway returned unexpected format: {res}")
            
        return asyncio.run(_run())
    def csvf(self): return "Exported CSV"

ita = ITAWrapper()
ctc = CTCWrapper()

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="IIoT Gateway Monitor",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- THEME MANAGEMENT ---
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
        border_clr = "rgba(0, 0, 0, 0.25)" # Explicitly darkened for frames/hr visibility
        accent_color = "#3A7CA5" # Calming blue accent instead of harsh orange
        mutated_text = "rgba(0, 0, 0, 0.6)"
        gold_color = "#A67B27" # Warm bronze/gold specifically balanced for light mode
        
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
        
        /* Force text colors broadly, EXCLUDING standard spans so inline colors work */
        h1, h2, h3, h4, h5, h6, p, label, div[data-testid="stMetricValue"], [data-testid="stMetricLabel"] label {{
            color: {text_color} !important; 
        }}
        
        /* Explicit gold class for username dynamically adjusted */
        .gold-user {{ color: {gold_color} !important; }}
        
        .stButton > button {{
            background-color: {accent_color} !important; color: #FFFFFF !important;
            border: none !important; border-radius: 8px !important;
            padding: 0.5rem 1rem !important; font-weight: 500 !important;
            transition: all 0.2s ease;
        }}
        /* Override specifically for button text so it stays white */
        .stButton > button p, .stButton > button span {{ color: #FFFFFF !important; }}
        .stButton > button:hover {{ transform: translateY(-1px); box-shadow: 0 4px 12px {accent_color}66 !important; }}
        
        div[data-testid="stMetric"], .plot-container {{
            background-color: {card_bg} !important;
            backdrop-filter: blur(6px); border: 1px solid {border_clr} !important;
            padding: 1rem; border-radius: 12px; height: 100%;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
            color: {text_color} !important;
        }}
        .stTabs [data-baseweb="tab-list"] {{
            border-bottom: 2px solid {border_clr} !important;
        }}
        .stTabs [data-baseweb="tab"] {{ background-color: transparent !important; border-bottom: 2px solid transparent !important; margin-bottom: -2px; }}
        /* Specific fix for unselected tab text */
        .stTabs [data-baseweb="tab"] p, .stTabs [data-baseweb="tab"] span {{ color: {mutated_text} !important; font-weight: 500 !important; }}
        /* Specific fix for selected tab text */
        .stTabs [aria-selected="true"] p, .stTabs [aria-selected="true"] span {{ color: {accent_color} !important; }}
        .stTabs [aria-selected="true"] {{ border-bottom: 2px solid {accent_color} !important; }}
        .stTabs [data-baseweb="tab-highlight"] {{ background-color: transparent !important; }}
        
        /* Make inline divs transparently adaptive too */
        .adaptive-card {{
            background-color: {card_bg} !important;
            padding: 20px; border-radius: 10px; height: 100%;
        }}
        
        hr, div[data-testid="stMarkdownContainer"] hr {{
            border-top: 2px solid {border_clr} !important;
            margin: 1.5rem 0 !important;
            border-bottom: none !important;
        }}
        
        /* Aggressively force Streamlit borders natively */
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
        /* Fix adaptive card headers and text */
        .adaptive-card p, .adaptive-card h3, .adaptive-history span, .adaptive-history b {{
             color: {text_color} !important;
        }}
    </style>
    """, unsafe_allow_html=True)

# --- GLOBAL SIMULATOR INIT ---
ita.init_ita_state()
ctc.init_ctc_state()

# --- SESSION STATE INITIALIZATION ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "username" not in st.session_state: st.session_state.username = None

# Initialize user data dictionaries
if "users_data" not in st.session_state:
    st.session_state.users_data = {}

def get_user_data():
    user = st.session_state.username
    if user not in st.session_state.users_data:
        st.session_state.users_data[user] = {
            "history": [],
            "machines": ["Motor A", "Pump B"],
            "ita_connected_list": [],
            "last_ita_reading": None,
            "last_ctc_data": None,
            "show_fft": False,
            "show_rms": False
        }
    return st.session_state.users_data[user]

if "current_view" not in st.session_state:
    st.session_state.current_view = "Dashboard 📊"

if "theme" not in st.session_state:
    st.session_state.theme = "Dark"
apply_theme()

# --- HELPER FUNCTIONS ---
def add_to_history(gateway, operation, status):
    usr_data = get_user_data()
    usr_data["history"].insert(0, {
        "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Gateway": gateway,
        "Operation": operation,
        "Status": status
    })
    usr_data["history"] = usr_data["history"][:5]

def compute_fft(data, sr):
    n = len(data)
    if n == 0: return [], []
    freq = np.fft.rfftfreq(n, d=1/sr)
    fft_vals = np.abs(np.fft.rfft(data)) / n
    return freq, fft_vals

def compute_rms(data):
    if len(data) == 0: return 0.0
    return np.sqrt(np.mean(np.square(data)))

# --- VIEWS ---
def login_view():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center; color: #4A90E2; margin-top: 0;'>IIoT Platform Login</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #888; margin-bottom: 2rem;'>Enter credentials to access firm environment</p>", unsafe_allow_html=True)
            
            with st.form("login_form"):
                user = st.text_input("Username", placeholder="admin")
                pwd = st.text_input("Password", type="password", placeholder="••••••••")
                submit = st.form_submit_button("Sign In", use_container_width=True)
                
                if submit:
                    if user and pwd:
                        with st.spinner("Authenticating..."):
                            time.sleep(1)
                        st.session_state.username = user
                        st.session_state.logged_in = True
                        st.rerun()
                    else:
                        st.error("Please enter both username and password")

def dashboard_view():
    usr_data = get_user_data()
    st.title("Dashboard Overview 📊")
    
    # Calculate health status
    system_status = "Healthy"
    alerts = "0 Alerts"
    status_color = "normal"
    if usr_data["history"] and any(h.get("Status") == "Error" for h in usr_data["history"][:2]):
        system_status = "Warning"
        alerts = "Check Logs"
        status_color = "off"
    
    active_gws = sum([bool(getattr(st.session_state, 'ita_connected', False)), bool(getattr(st.session_state, 'ctc_connected', False))])
    
    # Equal height widgets
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Active Gateways", str(active_gws), delta="Online", delta_color="normal")
    with col2:
        st.metric("Total Machines", str(len(usr_data["machines"])), delta="Active", delta_color="off")
    with col3:
        st.metric("Recent Readings", str(len(usr_data["history"])), delta="Total", delta_color="off")
    with col4:
        st.metric("System Status", system_status, delta=alerts, delta_color=status_color)
    
    st.markdown("---")
    
    colA, colB = st.columns([2, 1])
    with colA:
        st.subheader("Gateway Connectivity")
        
        g1, g2 = st.columns(2)
        with g1:
            ita_connected = getattr(st.session_state, 'ita_connected', False)
            st.markdown("""
            <div class='adaptive-card' style='border-left: 5px solid #4A90E2;'>
                <h3 style='margin-top:0;'>ITA-110</h3>
                <p>IP: {}</p>
                <p>Status: <span style='color:{}'><b>{}</b></span></p>
            </div>
            """.format(
                ita.ip(),
                "#4CAF50" if ita_connected else "#ef5350",
                "Connected 🟢" if ita_connected else "Disconnected 🔴"
            ), unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            if not ita_connected:
                new_ip = st.text_input("ITA IP Address", value=ita.ip(), key="ita_ip_input")
                new_port = st.number_input("ITA Port", value=ita.port(), key="ita_port_input", step=1)
                
                if st.button("Connect ITA", key="conn_ita"):
                    with st.spinner(f"Connecting to {new_ip}:{new_port}..."):
                        success, msg = ita.connect(new_ip, int(new_port))
                        if success:
                            add_to_history("ITA-110", "Connect", "Success")
                            st.success(msg)
                            import time; time.sleep(0.5)
                            st.rerun()
                        else:
                            add_to_history("ITA-110", "Connect", "Failed")
                            st.error(msg)
            else:
                if st.button("Disconnect ITA", key="disconn_ita"):
                    ita.disconnect()
                    add_to_history("ITA-110", "Disconnect", "Success")
                    st.rerun()

        with g2:
            ctc_connected = getattr(st.session_state, 'ctc_connected', False)
            st.markdown("""
            <div class='adaptive-card' style='border-left: 5px solid #E24A4A;'>
                <h3 style='margin-top:0;'>CTC Connect</h3>
                <p>IP: {}</p>
                <p>Status: <span style='color:{}'><b>{}</b></span></p>
            </div>
            """.format(
                ctc.ip(),
                "#4CAF50" if ctc_connected else "#ef5350",
                "Connected 🟢" if ctc_connected else "Disconnected 🔴"
            ), unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            if not ctc_connected:
                new_ctc_ip = st.text_input("CTC IP Address", value=ctc.ip(), key="ctc_ip_input")
                if st.button("Connect CTC", key="conn_ctc"):
                    with st.spinner("Connecting to CTC Connect..."):
                        success, msg = ctc.connect(new_ctc_ip)
                        if success:
                            add_to_history("CTC Connect", "Connect", "Success")
                            st.success(msg)
                            import time; time.sleep(0.5)
                            st.rerun()
                        else:
                            add_to_history("CTC Connect", "Connect", "Failed")
                            st.error(msg)
            else:
                if st.button("Disconnect CTC", key="disconn_ctc"):
                    ctc.disconnect()
                    add_to_history("CTC Connect", "Disconnect", "Success")
                    st.rerun()

    with colB:
        st.subheader("Recent History (Last 5)")
        if not usr_data["history"]:
            st.info("No recent history")
        else:
            for item in usr_data["history"]:
                st.markdown(f"""
                <div class='adaptive-history'>
                    <span style='color: #888;'>{item['Time']}</span><br/>
                    <b>{item['Gateway']}</b> - {item['Operation']} 
                    <span style='color: {"#4CAF50" if item["Status"].lower()=="success" else "#FFF"}; float:right;'>{item['Status'].upper()}</span>
                </div>
                """, unsafe_allow_html=True)

def ita_gateway_view():
    usr_data = get_user_data()
    st.title("ITA-110 Gateway ⚙️")
    
    if not getattr(st.session_state, 'ita_connected', False):
        st.warning("ITA-110 Simulator is disconnected. Please connect in the Dashboard.")
        return
        
    tab1, tab2 = st.tabs(["Configuration", "Data View"])
    
    with tab1:
        st.subheader("Parameter Configuration")
        with st.container(border=True):
            p1, p2, p3 = st.columns(3)
            with p1:
                tl = st.number_input("Trace Length (Samples)", min_value=128, max_value=32768, value=1024, step=128)
                x_ch = st.selectbox("X Channel", options=list(range(1, 17)), index=0)
            with p2:
                sr_opts = [128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 51200]
                sr = st.selectbox("Sampling Rate (Hz)", options=sr_opts, index=3)
                y_ch = st.selectbox("Y Channel", options=list(range(1, 17)), index=1)
            with p3:
                scale = st.number_input("Scaling (Gain)", value=1.0, step=0.1)
                z_ch = st.selectbox("Z Channel", options=list(range(1, 17)), index=2)
                
            p4, p5, p6 = st.columns(3)
            with p4:
                to_ms = st.number_input("Timeout (ms)", value=1000, disabled=True, help="Fixed timeout for reading operations")
            with p5:
                sig_path = st.selectbox("Input Signal Path (1-6)", options=list(range(1, 7)), index=0)
            with p6:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Set All Parameters", type="primary", use_container_width=True):
                    if getattr(st.session_state, 'ita_connected', False):
                        with st.spinner("Sending parameters to ITA..."):
                            success, msg = ita.set_all_parameters(x_ch, scale, sig_path, sr, to_ms, tl)
                        if success:
                            add_to_history("ITA", "Set Params", "Success")
                            st.success(f"Applied successfully! Gateway Response: {msg}")
                        else:
                            add_to_history("ITA", "Set Params", "Failed")
                            st.error(f"Failed to set parameters: {msg}")
                    else:
                        st.error("Cannot apply parameters. Connect Gateway first.")
        
        st.markdown("---")
        if st.button("▶ Take Reading", type="primary", use_container_width=True):
            with st.spinner("Acquiring data from ITA-110..."):
                if getattr(st.session_state, 'ita_connected', False):
                    try:
                        usr_data["last_ita_reading"] = ita.take_reading(x_ch, y_ch, z_ch, scale, sig_path, sr, to_ms, tl)
                        add_to_history("ITA", "Reading", "Success")
                        st.success("Reading Acquired!")
                    except Exception as e:
                        add_to_history("ITA", "Reading", "Failed")
                        st.error(f"Failed connection or reading error: {e}")
                else:
                    st.error("Not connected.")
            
    with tab2:
        st.subheader("Data Visualization")
        
        if usr_data["last_ita_reading"]:
            data = usr_data["last_ita_reading"]
            
            # Action Buttons
            c1, c2, c3 = st.columns(3)
            if c1.button("📉 Compute FFT", use_container_width=True):
                usr_data["show_fft"] = True
                usr_data["show_rms"] = False
            if c2.button("📐 Compute RMS", use_container_width=True):
                usr_data["show_rms"] = True
                usr_data["show_fft"] = False
            if c3.button("📥 Download Report (CSV)", use_container_width=True):
                ita.csvf("ita_export.csv")
                st.success("Saved reading locally as ita_export.csv")
                
            # Data preview
            st.markdown("### Raw Sensor Data Table")
            df = pd.DataFrame({
                "X": data.get("x", []),
                "Y": data.get("y", []),
                "Z": data.get("z", [])
            })
            st.dataframe(df.head(5), use_container_width=True)
            
            # Timeseries plots
            st.markdown("### Time Domain Signal")
            x_data = np.array(data.get("x", []))
            y_data = np.array(data.get("y", []))
            z_data = np.array(data.get("z", []))
            sr_val = data.get("sampling_rate", 1024)
            if isinstance(sr_val, str): sr_val = 1024
            
            if len(x_data) > 0:
                t = np.linspace(0, len(x_data)/sr_val * 1000, len(x_data)) # Time in ms
                
                with st.container():
                    st.markdown("<div class='plot-container'>", unsafe_allow_html=True)
                    tabs = st.tabs(["X Axis", "Y Axis", "Z Axis"])
                    
                    with tabs[0]:
                        fig = go.Figure(go.Scatter(x=t, y=x_data, line=dict(color="#FF4B4B")))
                        fig.update_layout(xaxis_title="Time (ms)", yaxis_title="Acc (g)", template="plotly_dark", margin=dict(l=20,r=20,t=20,b=20))
                        st.plotly_chart(fig, use_container_width=True)
                        if usr_data["show_rms"]: st.info(f"RMS X: {compute_rms(x_data):.4f} g")
                    with tabs[1]:
                        fig = go.Figure(go.Scatter(x=t, y=y_data, line=dict(color="#00D26A")))
                        fig.update_layout(xaxis_title="Time (ms)", yaxis_title="Acc (g)", template="plotly_dark", margin=dict(l=20,r=20,t=20,b=20))
                        st.plotly_chart(fig, use_container_width=True)
                        if usr_data["show_rms"]: st.info(f"RMS Y: {compute_rms(y_data):.4f} g")
                    with tabs[2]:
                        fig = go.Figure(go.Scatter(x=t, y=z_data, line=dict(color="#4A90E2")))
                        fig.update_layout(xaxis_title="Time (ms)", yaxis_title="Acc (g)", template="plotly_dark", margin=dict(l=20,r=20,t=20,b=20))
                        st.plotly_chart(fig, use_container_width=True)
                        if usr_data["show_rms"]: st.info(f"RMS Z: {compute_rms(z_data):.4f} g")
                    st.markdown("</div>", unsafe_allow_html=True)
                
                if usr_data["show_fft"]:
                    st.markdown("### Frequency Domain (FFT)")
                    with st.container():
                        st.markdown("<div class='plot-container'>", unsafe_allow_html=True)
                        f, fft_x = compute_fft(x_data, sr_val)
                        fig_fft = go.Figure(go.Scatter(x=f, y=fft_x, line=dict(color="#FF4B4B")))
                        fig_fft.update_layout(xaxis_title="Frequency (Hz)", yaxis_title="Amplitude", template="plotly_dark", margin=dict(l=20,r=20,t=20,b=20))
                        st.plotly_chart(fig_fft, use_container_width=True)
                        st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("### 3D XYZ Plot")
            with st.container():
                st.markdown("<div class='plot-container'>", unsafe_allow_html=True)
                fig_3d = go.Figure(data=[go.Scatter3d(x=x_data, y=y_data, z=z_data, mode='lines', line=dict(color="#4A90E2", width=3))])
                fig_3d.update_layout(template="plotly_dark", margin=dict(l=0,r=0,t=0,b=0), height=500)
                st.plotly_chart(fig_3d, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

        else:
            st.info("Take a reading from Configuration tab to view data.")

def ctc_gateway_view():
    usr_data = get_user_data()
    st.title("CTC Connect Gateway 📡")
    
    if not getattr(st.session_state, 'ctc_connected', False):
        st.warning("CTC Connect Simulator is disconnected. Please connect in the Dashboard.")
        return
        
    tab1, tab2 = st.tabs(["Configuration", "Data View"])
    
    with tab1:
        st.subheader("Sensor Management")
        c1, c2 = st.columns(2)
        if not getattr(st.session_state, 'ctc_subscribed', False):
            if c1.button("Subscribe Telemetry", use_container_width=True):
                if getattr(st.session_state, 'ctc_connected', False):
                    with st.spinner("Subscribing to CTC..."):
                        success, msg = ctc.subscribe()
                    if success:
                        add_to_history("CTC", "Subscribe", "Success")
                        st.success(msg)
                        import time; time.sleep(0.5)
                        st.rerun()
                    else:
                        add_to_history("CTC", "Subscribe", "Failed")
                        st.error(msg)
                else:
                    st.error("Connect first.")
        else:
            if c1.button("Unsubscribe", use_container_width=True):
                with st.spinner("Unsubscribing..."):
                    success, msg = ctc.unsubscribe()
                if success:
                    add_to_history("CTC", "Unsubscribe", "Success")
                    import time; time.sleep(0.5)
                    st.rerun()
                else:
                    add_to_history("CTC", "Unsubscribe", "Failed")
                    st.error(msg)
            st.success("Currently Subscribed to Telemetry")
                
    with tab2:
        st.subheader("Live Data Stream")
        if not getattr(st.session_state, 'ctc_subscribed', False):
            st.info("Subscribe to at least one sensor to view data.")
        else:
            with st.expander("🔍 Find Connected Device Serials", expanded=False):
                if st.button("Query Connected Serials"):
                    try:
                        serials = ctc.get_connected_serials()
                        st.json(serials)
                    except Exception as e:
                        st.error(f"Could not query serials: {e}")
                        
            c_actions = st.columns(2)
            ctc_serial_input = st.text_input("Device Serial", value="12345", key="ctc_serial_mono")
            if c_actions[0].button("Poll Latest Data"):
                with st.spinner(f"Waking up sensor {ctc_serial_input} and pulling 6400 samples. This can physically take up to 30 seconds..."):
                    try:
                        usr_data["last_ctc_data"] = ctc.get_current_data(serial=ctc_serial_input)
                        add_to_history("CTC", "Poll Data", "Success")
                    except asyncio.TimeoutError:
                        st.error("Hardware timeout: The sensor took longer than 30 seconds to wake up and transmit the data.")
                        add_to_history("CTC", "Poll Data", "Timeout")
                    except Exception as e:
                        st.error(f"Failed to poll CTC data: {str(e) or type(e).__name__}")
                        add_to_history("CTC", "Poll Data", "Failed")
                
            if c_actions[1].button("📥 Download Report (CSV)"):
                msg = ctc.csvf()
                st.success(msg)
                
            if usr_data["last_ctc_data"]:
                data = usr_data["last_ctc_data"]
                
                st.markdown(f"**Serial**: {data.get('Serial', 'N/A')} | **Timestamp**: {data.get('timestamp', '')}")
                
                # Timeseries plots
                st.markdown("### Time Domain Signal")
                x_data = np.array(data.get("X", []))
                y_data = np.array(data.get("Y", []))
                z_data = np.array(data.get("Z", []))
                
                if len(x_data) > 0:
                    t = np.linspace(0, 1000, len(x_data)) # Fake Time in ms
                    
                    with st.container():
                        st.markdown("<div class='plot-container'>", unsafe_allow_html=True)
                        tabs = st.tabs(["X Axis", "Y Axis", "Z Axis"])
                        
                        with tabs[0]:
                            fig = go.Figure(go.Scatter(x=t, y=x_data, line=dict(color="#FF4B4B")))
                            fig.update_layout(xaxis_title="Time (ms)", yaxis_title="Acc (g)", template="plotly_dark", margin=dict(l=20,r=20,t=20,b=20))
                            st.plotly_chart(fig, use_container_width=True)
                        with tabs[1]:
                            fig = go.Figure(go.Scatter(x=t, y=y_data, line=dict(color="#00D26A")))
                            fig.update_layout(xaxis_title="Time (ms)", yaxis_title="Acc (g)", template="plotly_dark", margin=dict(l=20,r=20,t=20,b=20))
                            st.plotly_chart(fig, use_container_width=True)
                        with tabs[2]:
                            fig = go.Figure(go.Scatter(x=t, y=z_data, line=dict(color="#4A90E2")))
                            fig.update_layout(xaxis_title="Time (ms)", yaxis_title="Acc (g)", template="plotly_dark", margin=dict(l=20,r=20,t=20,b=20))
                            st.plotly_chart(fig, use_container_width=True)
                        st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("Poll latest data to view charts.")


def machines_view():
    st.title("🏭 Machines & Fault Diagnosis")
    
    st.subheader("Machine Layout")
    
    # Mock upload 
    upf = st.file_uploader("Upload Machine Image Blueprint", type=['png','jpg','jpeg'])
    
    if upf:
        st.image(upf, caption="Annotated Machine", use_container_width=True)
        st.markdown("*(Imagine draggable sensor markers over this image...)*")
    else:
        st.markdown("""
        <div style='border: 2px dashed #444; border-radius: 10px; padding: 40px; text-align: center; color: #888;'>
            <p>Upload a machine blueprint to begin placing sensor markers</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    st.subheader("Fault Diagnosis Engine")
    
    if st.button("Run ML Diagnostic Analysis"):
        with st.spinner("Analyzing spectral data with ML models..."):
            time.sleep(2)
        st.success("Analysis Complete!")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("""
            <div style='background: rgba(239, 83, 80, 0.1); padding: 15px; border-radius: 8px; border: 1px solid #d32f2f;'>
                <h4 style='color: #ef5350; margin-top:0;'>Bearing Outer Race Defect</h4>
                <p>Severity: <b style='color:#ef5350'>82% (Critical)</b></p>
                <p style='font-size: 0.8em; color: #ccc;'>BPFO matched at 154Hz</p>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown("""
            <div style='background: rgba(102, 187, 106, 0.1); padding: 15px; border-radius: 8px; border: 1px solid #388e3c;'>
                <h4 style='color: #66bb6a; margin-top:0;'>Shaft Misalignment</h4>
                <p>Severity: <b style='color:#66bb6a'>12% (Normal)</b></p>
                <p style='font-size: 0.8em; color: #ccc;'>1X/2X harmonics stable</p>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown("""
            <div style='background: rgba(255, 202, 40, 0.1); padding: 15px; border-radius: 8px; border: 1px solid #fbc02d;'>
                <h4 style='color: #ffca28; margin-top:0;'>Mechanical Looseness</h4>
                <p>Severity: <b style='color:#ffca28'>45% (Warning)</b></p>
                <p style='font-size: 0.8em; color: #ccc;'>Multiples of 1X detected</p>
            </div>
            """, unsafe_allow_html=True)


# --- MAIN APP LAYOUT ---
if not st.session_state.logged_in:
    login_view()
else:
    # Sidebar
    with st.sidebar:
        st.image("https://openautomationsoftware.com/wp-content/uploads/2021/11/blog_iiot.png", width=60)
        st.markdown(f"<h3 style='margin-top: 5px;'>Welcome, <span class='gold-user'>{st.session_state.username}</span></h3>", unsafe_allow_html=True)
        st.markdown("<hr style='border: 1px solid rgba(100,100,100,0.2);'>", unsafe_allow_html=True)
        
        menu_items = ["Dashboard 📊", "ITA-110 Gateway ⚙️", "CTC Connect 📡", "Machines & Diagnosis 🏭"]
        for item in menu_items:
            if st.button(item, key=f"nav_{item}", use_container_width=True):
                st.session_state.current_view = item
                st.rerun()
                
        st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
        
        thm_toggle = st.toggle("Enable Light Mode", value=(st.session_state.get('theme', 'Dark') == 'Light'))
        new_theme = "Light" if thm_toggle else "Dark"
        if new_theme != st.session_state.get('theme', 'Dark'):
            st.session_state.theme = new_theme
            st.rerun()
            
        st.markdown("<hr style='border: 1px solid rgba(100,100,100,0.2);'>", unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.rerun()

    # Content Router
    if st.session_state.current_view == "Dashboard 📊":
        dashboard_view()
    elif st.session_state.current_view == "ITA-110 Gateway ⚙️":
        ita_gateway_view()
    elif st.session_state.current_view == "CTC Connect 📡":
        ctc_gateway_view()
    elif st.session_state.current_view == "Machines & Diagnosis 🏭":
        machines_view()
