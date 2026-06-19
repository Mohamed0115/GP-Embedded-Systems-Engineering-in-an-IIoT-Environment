import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
import datetime
import asyncio
import threading
import base64
import os
from core.state_manager import get_user_data, add_to_history
from core.utils import compute_fft, compute_rms, convert_fft_units
from views.new_diagnosis import get_all_points_for_selector

# ===== Scaling formula based on Manual Chapter 5.5 =====
# Acceleration (g) = (Raw * 10000.0) / (8388608.0 * Gain * Sensitivity)
# where sensitivity is in mV/unit (e.g. 100 mV/g, 10 mV/mm/s, etc.)
def calibrate_raw_data(raw_samples, gain, sensitivity):
    factor = 10000.0 / (8388608.0 * float(gain) * float(sensitivity))
    return [s * factor for s in raw_samples]

# ===== Log transaction to session state =====
def log_gateway_transaction(command, response, status="Success"):
    if 'gateway_logs' not in st.session_state:
        st.session_state.gateway_logs = []
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.gateway_logs.append({
        "timestamp": timestamp,
        "command": command,
        "response": response,
        "status": status
    })

# ===== Run single channel data acquisition =====
# Sends CH, GA, SP, SR, TO, TL commands to the ITA-110 gateway,
# then acquires data with AQ and reads back with BD? command.
# signal_path: SP value from config (1=Raw, 2=Band Filtered, 3=Demod, 5=HPF, 6=HW HPF)
def acquire_channel_data(ip, port, channel, gain, measurement_type, sensitivity, fmax, lines, signal_path=1):
    # Use the SP value from the saved channel config
    # Default: SP=1 (Raw Data) unless explicitly set by user in config dialog
    sp = int(signal_path)
    
    # Map F1max (bandwidth) to SR (sample rate) per Chapter 5.1:
    # SR = BW × 2.56
    sr = int(fmax * 2.56)
    
    # Map spectral lines to TL (trace length / number of samples) per Chapter 5.2:
    # TL = Lines × 2.56
    tl = int(lines * 2.56)
    
    # Connection timeout is fixed to 10 min
    to = 10 
    
    from hardware.gateway_bridge import SIMULATION_MODE
    if SIMULATION_MODE:
        from Gateways_Sim.ITA.CDSR import connect as ita_conn, disconnect as ita_disconn
        from Gateways_Sim.ITA.commands_ip import excute_data_command, excute_command
    else:
        from ITA.CDSR import connect as ita_conn, disconnect as ita_disconn
        from ITA.commands_ip import excute_data_command, excute_command

    async def _run():
        log_gateway_transaction("CONNECT", f"Connecting to {ip}:{port}...", "Pending")
        r, w = await asyncio.wait_for(ita_conn(ip, port), timeout=3.0)
        log_gateway_transaction("CONNECT", f"Connected to {ip}:{port}", "Success")
        
        # Setup channel parameters — all in a single compound command
        cmd = f"CH {channel};GA {gain};SP {sp};SR {sr};TO {to};TL {tl}"
        log_gateway_transaction("SEND", cmd, "Pending")
        res = await excute_command(r, w, cmd)
        log_gateway_transaction("RECEIVE", f"{res['response']}", "Success")
        
        # Acquire data
        log_gateway_transaction("SEND", "AQ", "Pending")
        res_aq = await excute_command(r, w, "AQ")
        log_gateway_transaction("RECEIVE", f"{res_aq['response']}", "Success")
        
        # Read Data back from device buffer
        log_gateway_transaction("SEND", f"BD? (TL={tl})", "Pending")
        res_bd = await excute_data_command(r, w, "BD?", tl)
        log_gateway_transaction("RECEIVE", f"Downloaded {len(res_bd['response'])} samples", "Success")
        
        # Disconnect
        await ita_disconn(w)
        log_gateway_transaction("DISCONNECT", "Connection closed", "Success")
        
        return res_bd["response"], sr
        
    return asyncio.run(_run())

# ===== Load the ITA-110 device image as base64 for the custom component =====
def _load_ita_image_b64():
    """Read the pre-generated base64 text file for the ITA-110 device image."""
    b64_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "ita_110_b64.txt")
    if os.path.exists(b64_path):
        with open(b64_path, "r") as f:
            return f.read().strip()
    return ""

# ===== Load the ITA-110 PDF manual as base64 for the embedded reader =====
def _load_manual_b64():
    """Read the pre-generated base64 text file for the ITA-110 manual PDF."""
    b64_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "ita_manual_b64.txt")
    if os.path.exists(b64_path):
        with open(b64_path, "r") as f:
            return f.read().strip()
    return ""


def gateways_view():
    # ===== Initialize session state =====
    if 'gateways' not in st.session_state:
        st.session_state.gateways = []
        
    if 'configured_channels' not in st.session_state:
        st.session_state.configured_channels = {}
        
    if 'gateway_logs' not in st.session_state:
        st.session_state.gateway_logs = []

    # ===== Import and declare the custom Streamlit component =====
    import streamlit.components.v1 as components
    
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    gateways_component_path = os.path.join(parent_dir, "gateways_component")
    gateways_component = components.declare_component("gateways_component", path=gateways_component_path)

    # Convert configured_channels dict keys to 'ip:channel' string keys for JSON serialization
    json_configured_channels = {
        f"{k[0]}:{k[1]}": v
        for k, v in st.session_state.configured_channels.items()
    }

    # ===== Change 3: Load the ITA-110 image base64 to pass to the component =====
    ita_image_b64 = _load_ita_image_b64()

    # ===== Render the custom component =====
    res = gateways_component(
        gateways=st.session_state.gateways,
        configured_channels=json_configured_channels,
        ita_image_b64=ita_image_b64,
        key="gateways_list_view"
    )

    # ===== React to custom component events =====
    # Compare action/gw_ip/ch fields, ignoring the _ts timestamp
    # so that repeat clicks on the same button always trigger a new event
    if res is not None:
        comparable = {k: v for k, v in res.items() if k != '_ts'}
        last_comparable = {k: v for k, v in (st.session_state.get('last_action_event') or {}).items() if k != '_ts'}
        if comparable != last_comparable or res.get('_ts') != (st.session_state.get('last_action_event') or {}).get('_ts'):
            st.session_state.last_action_event = res
            action = res["action"]
            gw_ip = res.get("gw_ip", None)
            ch_val = res.get("ch", None)
        
            # ===== Immediate actions (no dialog needed) =====
            if action == "toggle_sampling":
                for g in st.session_state.gateways:
                    if g["ip"] == gw_ip:
                        g["sampling"] = "Running" if g["sampling"] == "Paused" else "Paused"
                        log_gateway_transaction("TOGGLE_SAMPLING", f"Toggled sampling for {g['name']} to {g['sampling']}", "Success")
                st.rerun()
                
            elif action == "delete_gw":
                st.session_state.gateways = [g for g in st.session_state.gateways if g["ip"] != gw_ip]
                log_gateway_transaction("DELETE_GATEWAY", f"Deleted gateway {gw_ip}", "Success")
                st.rerun()
                
            elif action == "reconnect_gw":
                for g in st.session_state.gateways:
                    if g["ip"] == gw_ip:
                        from hardware.gateway_bridge import ita
                        success, msg = ita.connect(g["ip"], g["port"])
                        if success:
                            g["status"] = "online"
                            g["last_seen"] = "1s ago"
                            log_gateway_transaction("RECONNECT", f"Reconnected to {g['name']}", "Success")
                        else:
                            g["status"] = "offline"
                            log_gateway_transaction("RECONNECT", f"Reconnect failed: {msg}", "Failed")
                st.rerun()
                
            # ===== Change 2: Handle vendor card clicks from empty state =====
            elif action == "add_gw_ctc":
                st.toast("🔵 CTC Connect is coming soon!", icon="ℹ️")
            
            # ===== Modal actions (trigger dialog via pending_action) =====
            else:
                st.session_state.pending_action = {
                    "action": action,
                    "gw_ip": gw_ip,
                    "ch": int(ch_val) if ch_val else None
                }
                st.rerun()

    # ===============================================
    # ===== DIALOGS =====
    # ===============================================

    @st.dialog("📋 Gateway Logs", width="large")
    def show_logs_dialog():
        """Color-coded log table showing all gateway transactions."""
        if not st.session_state.gateway_logs:
            st.info("No transaction logs available.")
        else:
            # Build a color-coded HTML table for the logs
            log_rows = ""
            for log in reversed(st.session_state.gateway_logs):
                status = log.get("status", "")
                # Color code: green for success, red for failed, yellow for pending
                if status == "Success":
                    response_bg = "background-color: #dcfce7; color: #166534;"
                elif status == "Failed":
                    response_bg = "background-color: #fee2e2; color: #991b1b;"
                elif status == "Pending":
                    response_bg = "background-color: #fef3c7; color: #92400e;"
                else:
                    response_bg = ""
                log_rows += f"""<tr>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #e5e7eb; font-size: 13px; white-space: nowrap;">{log.get('timestamp', '')}</td>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #e5e7eb; font-size: 13px;">{log.get('command', '')}</td>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #e5e7eb; font-size: 13px; {response_bg} border-radius: 4px;">{log.get('response', '')}</td>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #e5e7eb; font-size: 13px; font-weight: 600; {response_bg}">{status}</td>
                </tr>"""
            
            log_html = f"""<div style="max-height: 450px; overflow-y: auto; border: 1px solid #e5e7eb; border-radius: 8px;">
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #f3f4f6; position: sticky; top: 0;">
                        <th style="padding: 10px 12px; text-align: left; font-size: 13px; font-weight: 600; border-bottom: 2px solid #d1d5db;">Timestamp</th>
                        <th style="padding: 10px 12px; text-align: left; font-size: 13px; font-weight: 600; border-bottom: 2px solid #d1d5db;">Command</th>
                        <th style="padding: 10px 12px; text-align: left; font-size: 13px; font-weight: 600; border-bottom: 2px solid #d1d5db;">Response</th>
                        <th style="padding: 10px 12px; text-align: left; font-size: 13px; font-weight: 600; border-bottom: 2px solid #d1d5db;">Status</th>
                    </tr>
                </thead>
                <tbody>{log_rows}</tbody>
            </table></div>"""
            st.markdown(log_html, unsafe_allow_html=True)
            st.markdown("")
            if st.button("Clear Logs", type="secondary", use_container_width=True):
                st.session_state.gateway_logs = []
                st.rerun()

    # ===== Change 1: Fixed Add Gateway dialog =====
    # Removed st.rerun() from vendor button clicks — the dialog now uses
    # session_state directly and re-renders naturally without killing the dialog context.
    @st.dialog("🔌 Add New Gateway", width="medium")
    def add_gateway_dialog(preset_vendor=None):
        """Dialog for adding a new ITA or CTC gateway.
        preset_vendor: If "ITA", skip vendor selection and go straight to ITA config form.
        """
        # Initialize modal_vendor from preset or session state
        if preset_vendor:
            st.session_state.modal_vendor = preset_vendor
            
        if 'modal_vendor' not in st.session_state:
            st.session_state.modal_vendor = None
        
        st.markdown("### Select Vendor")
        c1, c2 = st.columns(2)
        
        with c1:
            # Change 1 fix: No st.rerun() — just set state, dialog re-renders naturally
            if st.button("Icon Research ITA\n(High-precision DAQ)", use_container_width=True, type="primary" if st.session_state.modal_vendor == "ITA" else "secondary"):
                st.session_state.modal_vendor = "ITA"
        with c2:
            if st.button("CTC Connect\n(Coming soon)", use_container_width=True, type="primary" if st.session_state.modal_vendor == "CTC" else "secondary"):
                st.session_state.modal_vendor = "CTC"
                
        if st.session_state.modal_vendor == "CTC":
            st.warning("CTC Connect: Coming Soon!")
            
        elif st.session_state.modal_vendor == "ITA":
            st.markdown("---")
            st.markdown("#### ITA-110 Configuration (16 Channels)")
            g_name = st.text_input("Gateway Name *", placeholder="Gateway-001")
            g_loc = st.text_input("Location", placeholder="Production Floor A")
            g_sn = st.text_input("Serial Number *", placeholder="ITA-120-E8F3B4")
            g_ip = st.text_input("IP Address *", placeholder="192.168.1.130")
            g_port = st.number_input("Port *", min_value=1, max_value=65535, value=8020)
            g_net = st.selectbox("Network Type", options=["Ethernet", "WiFi"])
            
            if st.button("Create Gateway", type="primary", use_container_width=True):
                if not g_name or not g_sn or not g_ip:
                    st.error("Please fill in all required fields (*)!")
                else:
                    new_gw = {
                        "name": g_name,
                        "location": g_loc or "Not specified",
                        "model": "ITA-110",
                        "sn": g_sn,
                        "status": "online",
                        "last_seen": "1s ago",
                        "connection": g_net,
                        "ip": g_ip,
                        "port": int(g_port),
                        "channels": 16,
                        "sampling": "Paused",
                        "date_added": datetime.datetime.now().strftime("%m/%d/%Y")
                    }
                    st.session_state.gateways.append(new_gw)
                    log_gateway_transaction("ADD_GATEWAY", f"Added gateway {g_name} ({g_ip}:{g_port})", "Success")
                    st.session_state.modal_vendor = None
                    st.success("Gateway added successfully!")
                    time.sleep(1)
                    st.rerun()

    # ===== Enhanced Configure Channel dialog =====
    # Follows ITA-110 Manual Chapter 5 for proper acquisition parameters.
    # Dynamic types: Acceleration, Velocity, Displacement use AQ command
    # Static types: Temperature, Pressure use AP command
    # Signal Path (SP) values per Manual:
    #   1=Raw Data, 2=Band Filtered, 3=Bearing Demodulator,
    #   5=Highpass Filter, 6=Hardware Highpass Filter
    @st.dialog("⚙️ Configure Channel", width="medium")
    def configure_channel_dialog(gw_ip, ch_num):
        key = (gw_ip, ch_num)
        curr_config = st.session_state.configured_channels.get(key, {})
        
        st.markdown(f"#### Configure Channel **CH{ch_num}**")
        st.caption(f"Gateway: {gw_ip}")
        
        # ===== Location: select a real Point from the Diagnosis hierarchy =====
        point_options = get_all_points_for_selector()
        point_display = ["Select point..."] + [p[1] for p in point_options]
        point_ids = [None] + [p[0] for p in point_options]
        curr_point_id = curr_config.get("point_id")
        curr_point_idx = 0
        if curr_point_id and curr_point_id in point_ids:
            curr_point_idx = point_ids.index(curr_point_id)
        loc_sel = st.selectbox("Location (Machine - Point) *", options=point_display, index=curr_point_idx)
        
        # ===== Measurement Type selection =====
        types = ["Select measurement type", "Acceleration", "Velocity", "Displacement", "Temperature", "Pressure"]
        curr_type = curr_config.get("type", "Select measurement type")
        type_idx = types.index(curr_type) if curr_type in types else 0
        m_type = st.selectbox("Measurement Type *", options=types, index=type_idx)
        
        # Categorize measurement type
        is_dynamic = m_type in ["Acceleration", "Velocity", "Displacement"]
        is_static = m_type in ["Temperature", "Pressure"]
        # Acceleration and Displacement get Axis + optional filters
        needs_axis = m_type in ["Acceleration", "Displacement"]
        
        # Default values for all config fields
        gain_val = "1"
        sensitivity_val = 100.0
        unit_val = "mV"
        fmax_val = 1000
        lines_val = 400
        signal_path_val = 1      # SP value sent to ITA-110
        axis_val = None           # Only for Acceleration/Displacement
        hpf_val = None            # Optional High Pass Filter
        bpf_val = None            # Optional Bandpass Filter
        
        if is_dynamic:
            # ===== AXIS selector for Acceleration & Displacement =====
            if needs_axis:
                axis_options = ["Select axis", "X Axis", "Y Axis", "Z Axis",
                                "H Axis (Horizontal)", "V Axis (Vertical)", "A Axis (Axial)"]
                curr_axis = curr_config.get("axis", "Select axis")
                axis_idx = axis_options.index(curr_axis) if curr_axis in axis_options else 0
                axis_val = st.selectbox("Axis *", options=axis_options, index=axis_idx,
                                         help="Physical orientation of the sensor on the machine.")
            
            # ===== SIGNAL PATH selector (SP command) per Manual Chapter 5.6 =====
            # Maps user-friendly labels to the ITA-110 SP integer values
            sp_options = {
                "Select signal path": 0,
                "Raw Data": 1,
                "Band Filtered": 2,
                "Bearing Demodulator": 3,
                "Highpass Filter": 5,
                "Hardware Highpass Filter": 6
            }
            sp_labels = list(sp_options.keys())
            curr_sp = curr_config.get("signal_path_sp", 0)
            # Find the label matching the saved SP value
            curr_sp_label = next((k for k, v in sp_options.items() if v == curr_sp), "Select signal path")
            sp_idx = sp_labels.index(curr_sp_label) if curr_sp_label in sp_labels else 0
            sp_selected = st.selectbox("Signal Path *", options=sp_labels, index=sp_idx,
                                        help="Signal conditioning path in the ITA-110 hardware. "
                                             "Raw=no filter, Band Filtered=BPF, Demod=envelope, "
                                             "HPF=software highpass, HW HPF=hardware integrator+highpass (typical for Velocity).")
            signal_path_val = sp_options[sp_selected]
            
            # ===== GAIN selector =====
            gains = ["Select gain", "1", "2", "5", "10", "20", "50", "100"]
            curr_gain = curr_config.get("gain", "Select gain")
            gain_idx = gains.index(curr_gain) if curr_gain in gains else 0
            gain_val = st.selectbox("Gain *", options=gains, index=gain_idx,
                                     help="Gain multiplier for the ADC. Higher gain = more sensitivity but less range.")
            
            # ===== SENSITIVITY + UNIT =====
            c_sens, c_unit = st.columns(2)
            with c_sens:
                sensitivity_val = st.number_input("Sensitivity *", min_value=0.1,
                    value=float(curr_config.get("sensitivity", 100.0)), step=0.1, placeholder="e.g., 100")
            with c_unit:
                # Units depend on measurement type
                if m_type == "Acceleration":
                    units = ["mV/g", "mV"]
                elif m_type == "Velocity":
                    units = ["mV/mm/s", "mV"]
                else:  # Displacement
                    units = ["mV/µm", "mV"]
                unit_idx = 0
                curr_unit = curr_config.get("unit", "")
                if curr_unit in units:
                    unit_idx = units.index(curr_unit)
                unit_val = st.selectbox("Sensitivity Unit *", options=units, index=unit_idx)
            
            # ===== OPTIONAL FILTERS for Acceleration & Displacement =====
            if needs_axis:
                st.markdown("---")
                st.markdown("##### Optional Filters")
                
                # High Pass Filter (optional) — per Manual Chapter 5
                hpf_options = ["Select filter (optional)", "HPF 0.5 Hz", "HPF 2 Hz", "HPF 10 Hz", "HPF 100 Hz"]
                curr_hpf = curr_config.get("hpf", "Select filter (optional)")
                hpf_idx = hpf_options.index(curr_hpf) if curr_hpf in hpf_options else 0
                hpf_val = st.selectbox("High Pass Filter (Optional)", options=hpf_options, index=hpf_idx,
                                        help="Remove low-frequency noise below the cutoff frequency.")
                if hpf_val == "Select filter (optional)":
                    hpf_val = None
                
                # Bandpass Filter (optional)
                bpf_options = [
                    "Select filter (optional)",
                    "Low: 50 Hz, High: 200 Hz",
                    "Low: 200 Hz, High: 500 Hz",
                    "Low: 500 Hz, High: 1,000 Hz",
                    "Low: 600 Hz, High: 2,000 Hz",
                    "Low: 1,000 Hz, High: 5,000 Hz",
                    "Low: 2,000 Hz, High: 10,000 Hz",
                    "Low: 5,000 Hz, High: 20,000 Hz",
                    "Low: 10,000 Hz, High: 40,000 Hz",
                    "Low: 20,000 Hz, High: 40,000 Hz"
                ]
                curr_bpf = curr_config.get("bpf", "Select filter (optional)")
                bpf_idx = bpf_options.index(curr_bpf) if curr_bpf in bpf_options else 0
                bpf_val = st.selectbox("Bandpass Filter (Optional)", options=bpf_options, index=bpf_idx,
                                        help="Pass only frequencies within the specified range.")
                if bpf_val == "Select filter (optional)":
                    bpf_val = None
            
            # ===== ACQUISITION PARAMETERS (Fmax, Lines) =====
            st.markdown("---")
            st.markdown("##### Acquisition Parameters")
            c_fmax, c_lines = st.columns(2)
            with c_fmax:
                # F1max options per Manual Chapter 5.1
                fmax_opts = [25, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 40000]
                curr_fmax = curr_config.get("fmax", 1000)
                fmax_idx = fmax_opts.index(curr_fmax) if curr_fmax in fmax_opts else 5
                fmax_val = st.selectbox("F1max (Hz) *", options=fmax_opts, index=fmax_idx,
                                         help="Maximum frequency of interest (bandwidth)")
            with c_lines:
                # Spectral lines per Manual Chapter 5.2
                lines_opts = [25, 50, 100, 200, 400, 800, 1600, 3200, 6400, 12800, 25600, 51200]
                curr_lines = curr_config.get("lines", 400)
                lines_idx = lines_opts.index(curr_lines) if curr_lines in lines_opts else 4
                lines_val = st.selectbox("Spectral Lines *", options=lines_opts, index=lines_idx,
                                          help="Number of spectral lines (resolution)")
            
            # Computed SR, TL, and acquisition time
            sr_computed = int(fmax_val * 2.56)
            tl_computed = int(lines_val * 2.56)
            acq_time = lines_val / fmax_val
            st.info(f"SR = {sr_computed} Hz | TL = {tl_computed} samples | Acquisition Time ≈ {acq_time:.2f}s")
            
        elif is_static:
            # ===== Static measurement: Temperature / Pressure =====
            # Now includes Gain selector (previously missing)
            st.caption("Static measurement — uses AP command for process parameters.")
            
            # Gain (now included for static types too)
            gains = ["Select gain", "1", "2", "5", "10", "20", "50", "100"]
            curr_gain = curr_config.get("gain", "Select gain")
            gain_idx = gains.index(curr_gain) if curr_gain in gains else 0
            gain_val = st.selectbox("Gain *", options=gains, index=gain_idx,
                                     help="Gain multiplier for the ADC.")
            
            c_sens, c_unit = st.columns(2)
            with c_sens:
                sensitivity_val = st.number_input("Sensitivity *", min_value=0.1,
                    value=float(curr_config.get("sensitivity", 100.0)), step=0.1, placeholder="e.g., 100")
            with c_unit:
                if m_type == "Temperature":
                    units = ["mV/°C", "mV"]
                else:  # Pressure
                    units = ["mV/Bar", "mV"]
                unit_idx = 0
                curr_unit = curr_config.get("unit", "")
                if curr_unit in units:
                    unit_idx = units.index(curr_unit)
                unit_val = st.selectbox("Sensitivity Unit *", options=units, index=unit_idx)
        
        # ===== SAVE CONFIGURATION =====
        if m_type != "Select measurement type":
            if st.button("Save Configuration", type="primary", use_container_width=True):
                # Validation: gain must be selected
                if gain_val == "Select gain":
                    st.error("Please select a gain value!")
                # Validation: signal path must be selected for dynamic types
                elif is_dynamic and signal_path_val == 0:
                    st.error("Please select a signal path!")
                # Validation: axis must be selected for Acceleration/Displacement
                elif needs_axis and (axis_val is None or axis_val == "Select axis"):
                    st.error("Please select an axis!")
                else:
                    # Build config dict with all fields
                    # Store selected point_id from Location selector
                    sel_idx = point_display.index(loc_sel) if loc_sel in point_display else 0
                    selected_point_id = point_ids[sel_idx] if sel_idx > 0 else None
                    config_data = {
                        "type": m_type,
                        "gain": gain_val,
                        "sensitivity": sensitivity_val,
                        "unit": unit_val,
                        "configured": True,
                        "point_id": selected_point_id,
                        "location_display": loc_sel if sel_idx > 0 else ""
                    }
                    # Dynamic-specific fields
                    if is_dynamic:
                        config_data["fmax"] = fmax_val
                        config_data["lines"] = lines_val
                        config_data["signal_path_sp"] = signal_path_val
                    # Axis for Acceleration/Displacement
                    if needs_axis:
                        config_data["axis"] = axis_val
                        if hpf_val:
                            config_data["hpf"] = hpf_val
                        if bpf_val:
                            config_data["bpf"] = bpf_val
                    
                    st.session_state.configured_channels[key] = config_data
                    axis_info = f", Axis={axis_val}" if axis_val else ""
                    log_gateway_transaction("CONFIG_CHANNEL",
                        f"Configured CH{ch_num} on {gw_ip}: {m_type} (Gain={gain_val}, "
                        f"Sens={sensitivity_val} {unit_val}, SP={signal_path_val}{axis_info})", "Success")
                    st.success("Configuration saved!")
                    time.sleep(1)
                    st.rerun()

    # ===== Take Reading dialog with unit toggle in Spectrum =====
    @st.dialog("📊 Take Reading", width="large")
    def take_reading_dialog(gw_ip, gw_port, ch_num):
        key = (gw_ip, ch_num)
        config = st.session_state.configured_channels.get(key, {})
        
        m_type = config.get('type', '')
        is_static = m_type in ["Temperature", "Pressure"]
        
        st.markdown(f"### Take Reading on Channel **CH{ch_num}**")
        axis_info = f" — {config.get('axis', '')}" if config.get('axis') else ""
        st.markdown(f"**Gateway**: `{gw_ip}:{gw_port}`  |  **Type**: `{m_type}{axis_info}` "
                    f"({config.get('sensitivity')} {config.get('unit')}, Gain={config.get('gain')})")
        
        # Use Fmax/Lines from saved config (no need to ask again)
        fmax = config.get("fmax", 1000)
        lines = config.get("lines", 400)
        sr_computed = int(fmax * 2.56)
        tl_computed = int(lines * 2.56)
        
        if not is_static:
            st.info(f"Using saved parameters: **F1max** = `{fmax} Hz` | **Lines** = `{lines}` → SR = `{sr_computed} Hz`, TL = `{tl_computed}`")
        else:
            st.info("Static measurement — reading sensor value directly.")
        
        if 'last_dialog_reading' not in st.session_state:
            st.session_state.last_dialog_reading = None
            st.session_state.last_dialog_fft = None
            st.session_state.last_dialog_rms = None
            
        if st.button("▶ Acquire Data", type="primary", use_container_width=True):
            with st.spinner("Communicating with ITA-110..."):
                try:
                    # Pass signal_path_sp from config to the acquire function
                    raw_data, sr = acquire_channel_data(
                        ip=gw_ip,
                        port=gw_port,
                        channel=ch_num,
                        gain=config.get("gain"),
                        measurement_type=config.get("type"),
                        sensitivity=config.get("sensitivity"),
                        fmax=fmax,
                        lines=lines,
                        signal_path=config.get("signal_path_sp", 1)
                    )
                    
                    calibrated = calibrate_raw_data(raw_data, config.get("gain"), config.get("sensitivity"))
                    
                    st.session_state.last_dialog_reading = calibrated
                    st.session_state.last_dialog_rms = compute_rms(np.array(calibrated))
                    f, fft_vals = compute_fft(np.array(calibrated), sr)
                    st.session_state.last_dialog_fft = (f.tolist(), fft_vals.tolist())
                    
                    config["last_val"] = f"{st.session_state.last_dialog_rms:.4f}"
                    config["last_unit"] = "g" if m_type == "Acceleration" else (config.get("unit").split("/")[-1] if "/" in config.get("unit") else config.get("unit"))
                    config["last_time"] = datetime.datetime.now().strftime("%H:%M:%S")
                    st.session_state.configured_channels[key] = config
                    
                    # ===== Write reading to diagnosis point =====
                    pt_id = config.get("point_id")
                    axis_name = config.get("axis", "H Axis")
                    if pt_id and 'diag_data' in st.session_state:
                        diag_nodes = st.session_state.diag_data.get("nodes", {})
                        if pt_id in diag_nodes:
                            if "readings" not in diag_nodes[pt_id]:
                                diag_nodes[pt_id]["readings"] = {}
                            diag_nodes[pt_id]["readings"][axis_name] = {
                                "time_waveform": calibrated,
                                "spectrum_freq": f.tolist(),
                                "spectrum_amp": fft_vals.tolist(),
                                "sr": sr,
                                "timestamp": datetime.datetime.now().isoformat()
                            }
                    
                    st.success("Data Acquired successfully!")
                except Exception as e:
                    st.error(f"Failed to acquire reading: {e}")
                    
        if st.session_state.last_dialog_reading:
            cal_data = st.session_state.last_dialog_reading
            rms_val = st.session_state.last_dialog_rms
            
            st.markdown("---")
            st.markdown(f"#### Acquired Signal Details (RMS: **{rms_val:.4f}**)")
            
            df_export = pd.DataFrame({
                "Sample Index": list(range(len(cal_data))),
                "Physical Value": cal_data
            })
            csv_data = df_export.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Reading (CSV)",
                data=csv_data,
                file_name=f"ita_ch{ch_num}_reading.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            # ===== Two tabs: Time Waveform and Spectrum =====
            tab_time, tab_freq = st.tabs(["Time Waveform", "Spectrum"])
            with tab_time:
                t = np.linspace(0, len(cal_data)/sr_computed * 1000, len(cal_data))
                fig_time = go.Figure(go.Scatter(x=t, y=cal_data, line=dict(color="#FF4B4B")))
                fig_time.update_layout(
                    xaxis_title="Time (ms)", 
                    yaxis_title=f"Value ({config.get('unit', 'mV').split('/')[-1] if '/' in config.get('unit', 'mV') else config.get('unit', 'mV')})", 
                    template="plotly_dark", 
                    margin=dict(l=20,r=20,t=20,b=20),
                    height=300
                )
                st.plotly_chart(fig_time, use_container_width=True)
                
            with tab_freq:
                if st.session_state.last_dialog_fft:
                    f_list, fft_list = st.session_state.last_dialog_fft
                    
                    # ===== UNIT TOGGLE: Real g ↔ mm/s conversion =====
                    # Determine the native unit from the measurement type
                    if m_type == "Acceleration":
                        native_unit = "g"
                    elif m_type == "Velocity":
                        native_unit = "mm/s"
                    else:
                        native_unit = "mV"  # Displacement or other
                    
                    # Only show the toggle for Acceleration and Velocity types
                    if m_type in ["Acceleration", "Velocity"]:
                        display_unit = st.radio(
                            "Amplitude Unit",
                            options=["g", "mm/s"],
                            index=0 if native_unit == "g" else 1,
                            horizontal=True,
                            help="Switch between acceleration (g) and velocity (mm/s). "
                                 "This performs a real mathematical conversion in the frequency domain."
                        )
                        # Convert if the selected unit differs from native
                        if display_unit != native_unit:
                            plot_fft = convert_fft_units(f_list, fft_list, native_unit, display_unit).tolist()
                        else:
                            plot_fft = fft_list
                        y_label = f"Amplitude ({display_unit})"
                    else:
                        plot_fft = fft_list
                        y_label = f"Amplitude ({native_unit})"
                    
                    fig_fft = go.Figure(go.Scatter(x=f_list, y=plot_fft, line=dict(color="#FF4B4B")))
                    fig_fft.update_layout(
                        xaxis_title="Frequency (Hz)", 
                        yaxis_title=y_label, 
                        template="plotly_dark", 
                        margin=dict(l=20,r=20,t=20,b=20),
                        height=300
                    )
                    st.plotly_chart(fig_fft, use_container_width=True)

    # ===== Change 4: Embedded PDF Manual dialog =====
    @st.dialog("📖 ITA-110 Programmer's Manual", width="large")
    def show_manual_dialog():
        """Opens an embedded PDF reader so the user can flip through the ITA-110 manual."""
        manual_b64 = _load_manual_b64()
        if manual_b64:
            # Embed the PDF using an iframe with data URI
            pdf_html = f"""
            <div style="border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
                <iframe 
                    src="data:application/pdf;base64,{manual_b64}" 
                    width="100%" 
                    height="600" 
                    style="border: none;">
                </iframe>
            </div>
            """
            st.markdown(pdf_html, unsafe_allow_html=True)
        else:
            st.error("PDF manual file not found. Please ensure ita_manual_b64.txt exists in static/ folder.")

    # ===== Change 6: Edit Gateway Settings dialog =====
    @st.dialog("⚙️ Edit Gateway Settings", width="medium")
    def edit_gateway_dialog(gw_ip):
        """Edit the configuration of an existing gateway (name, location, SN, IP, port, network type)."""
        gw = None
        gw_idx = None
        for i, g in enumerate(st.session_state.gateways):
            if g["ip"] == gw_ip:
                gw = g
                gw_idx = i
                break
        
        if gw is None:
            st.error("Gateway not found!")
            return
        
        st.markdown(f"#### Edit **{gw['name']}** Settings")
        st.caption(f"Model: {gw['model']} | SN: {gw['sn']}")
        
        g_name = st.text_input("Gateway Name *", value=gw["name"])
        g_loc = st.text_input("Location", value=gw.get("location", ""))
        g_sn = st.text_input("Serial Number *", value=gw["sn"])
        g_ip = st.text_input("IP Address *", value=gw["ip"])
        g_port = st.number_input("Port *", min_value=1, max_value=65535, value=int(gw["port"]))
        net_opts = ["Ethernet", "WiFi"]
        net_idx = net_opts.index(gw.get("connection", "Ethernet")) if gw.get("connection") in net_opts else 0
        g_net = st.selectbox("Network Type", options=net_opts, index=net_idx)
        
        if st.button("Save Changes", type="primary", use_container_width=True):
            if not g_name or not g_sn or not g_ip:
                st.error("Please fill in all required fields (*)!")
            else:
                # Update the gateway in session state
                st.session_state.gateways[gw_idx]["name"] = g_name
                st.session_state.gateways[gw_idx]["location"] = g_loc or "Not specified"
                st.session_state.gateways[gw_idx]["sn"] = g_sn
                st.session_state.gateways[gw_idx]["ip"] = g_ip
                st.session_state.gateways[gw_idx]["port"] = int(g_port)
                st.session_state.gateways[gw_idx]["connection"] = g_net
                log_gateway_transaction("EDIT_GATEWAY", f"Updated gateway {g_name} ({g_ip}:{g_port})", "Success")
                st.success("Gateway settings updated!")
                time.sleep(1)
                st.rerun()

    # ===== Group-Based Schedule with Real Background Scheduler =====
    # Each group has: name, selected channels, schedule type, interval settings, enabled toggle.
    # A background thread runs the actual data acquisition at the configured intervals.
    
    # --- Background Scheduler Engine ---
    # Global dict tracking running scheduler threads per gateway IP
    # Key = gw_ip, Value = {"thread": Thread, "stop_event": Event, "groups": [...]}
    if '_scheduler_threads' not in st.session_state:
        st.session_state._scheduler_threads = {}
    
    def _run_scheduler_loop(gw_ip, gw_port, groups, configured_channels, stop_event):
        """Background thread: loops through schedule groups and acquires data when interval fires.
        
        Each group tracks its own 'next_run' timestamp. The thread sleeps 1 second between
        checks so it can respond quickly to the stop_event signal.
        
        Args:
            gw_ip: IP address of the gateway to read from.
            gw_port: TCP port of the gateway.
            groups: list of group dicts (name, channels, schedule_type, interval, enabled, etc.)
            configured_channels: dict of channel configs keyed by (ip, ch_num).
            stop_event: threading.Event — set to True to gracefully stop the thread.
        """
        import copy
        
        # Map interval labels to seconds for "Simple Interval" schedule type
        interval_to_seconds = {
            "Every 5 seconds": 5,
            "Every 1 minute": 60,
            "Every 5 minutes": 300,
            "Every 10 minutes": 600,
            "Every 15 minutes": 900,
            "Every 30 minutes": 1800,
            "Every 1 hour": 3600,
            "Every 2 hours": 7200,
            "Every 4 hours": 14400,
            "Every 8 hours": 28800,
            "Every 12 hours": 43200,
            "Every 24 hours": 86400,
        }
        
        # Initialize next_run for each group to "now" so first reading fires immediately
        group_next_run = {}
        for i, grp in enumerate(groups):
            if grp.get("enabled", False):
                group_next_run[i] = time.time()
        
        while not stop_event.is_set():
            now = time.time()
            for i, grp in enumerate(groups):
                if not grp.get("enabled", False):
                    continue
                if i not in group_next_run:
                    group_next_run[i] = now
                
                # Check if it's time to fire this group
                if now >= group_next_run[i]:
                    sched_type = grp.get("schedule_type", "Simple Interval")
                    channels = grp.get("channels", [])
                    
                    # --- Acquire data for each channel in the group ---
                    for ch_label in channels:
                        # Parse channel number from label like "CH3 (Acceleration — V Axis)"
                        try:
                            ch_num = int(ch_label.split("CH")[1].split(" ")[0])
                        except (IndexError, ValueError):
                            continue
                        
                        key = (gw_ip, ch_num)
                        config = configured_channels.get(key, {})
                        if not config.get("configured"):
                            continue
                        
                        m_type = config.get("type", "")
                        if m_type in ["Temperature", "Pressure"]:
                            continue  # Skip static for now — AP command is separate
                        
                        try:
                            raw_data, sr = acquire_channel_data(
                                ip=gw_ip,
                                port=gw_port,
                                channel=ch_num,
                                gain=config.get("gain"),
                                measurement_type=config.get("type"),
                                sensitivity=config.get("sensitivity"),
                                fmax=config.get("fmax", 1000),
                                lines=config.get("lines", 400),
                                signal_path=config.get("signal_path_sp", 1)
                            )
                            calibrated = calibrate_raw_data(raw_data, config.get("gain"), config.get("sensitivity"))
                            rms_val = compute_rms(np.array(calibrated))
                            
                            # Update config with latest reading
                            config["last_val"] = f"{rms_val:.4f}"
                            config["last_unit"] = "g" if m_type == "Acceleration" else (
                                config.get("unit", "mV").split("/")[-1] if "/" in config.get("unit", "mV") else config.get("unit", "mV"))
                            config["last_time"] = datetime.datetime.now().strftime("%H:%M:%S")
                            configured_channels[key] = config
                            
                            log_gateway_transaction("SCHEDULED_READ",
                                f"[{grp.get('name', 'Group')}] CH{ch_num} RMS={rms_val:.4f} {config['last_unit']}", "Success")
                        except Exception as e:
                            log_gateway_transaction("SCHEDULED_READ",
                                f"[{grp.get('name', 'Group')}] CH{ch_num} failed: {e}", "Failed")
                    
                    # --- Calculate next run based on schedule type ---
                    if sched_type == "Simple Interval":
                        interval_label = grp.get("interval", "Every 1 hour")
                        seconds = interval_to_seconds.get(interval_label, 3600)
                        group_next_run[i] = now + seconds
                    elif sched_type == "Every N Hours":
                        n_hours = grp.get("n_hours", 1)
                        group_next_run[i] = now + (n_hours * 3600)
                    elif sched_type == "Daily at Specific Time":
                        # Schedule for the same time tomorrow
                        group_next_run[i] = now + 86400
                    elif sched_type == "Multiple Times per Day":
                        n_times = grp.get("times_per_day", 2)
                        # Spread evenly across 24 hours
                        group_next_run[i] = now + (86400 / max(n_times, 1))
            
            # Sleep 1 second between checks — allows quick stop_event response
            stop_event.wait(1.0)
    
    def _start_scheduler(gw_ip, gw_port, groups):
        """Start a background scheduler thread for the given gateway.
        Stops any existing thread first."""
        _stop_scheduler(gw_ip)
        
        stop_event = threading.Event()
        thread = threading.Thread(
            target=_run_scheduler_loop,
            args=(gw_ip, gw_port, groups, st.session_state.configured_channels, stop_event),
            daemon=True,  # Dies when Streamlit process exits
            name=f"scheduler_{gw_ip}"
        )
        st.session_state._scheduler_threads[gw_ip] = {
            "thread": thread,
            "stop_event": stop_event,
            "started_at": datetime.datetime.now().strftime("%H:%M:%S")
        }
        thread.start()
        log_gateway_transaction("SCHEDULER", f"Started scheduler for {gw_ip} with {len(groups)} groups", "Success")
    
    def _stop_scheduler(gw_ip):
        """Stop a running scheduler thread for the given gateway."""
        info = st.session_state._scheduler_threads.get(gw_ip)
        if info and info["thread"].is_alive():
            info["stop_event"].set()
            info["thread"].join(timeout=3.0)
            log_gateway_transaction("SCHEDULER", f"Stopped scheduler for {gw_ip}", "Success")
        st.session_state._scheduler_threads.pop(gw_ip, None)
    
    @st.dialog("📅 Schedule Channels", width="large")
    def schedule_readings_dialog(gw_ip):
        """Group-based schedule dialog — each group can have different channels,
        schedule type, and interval. A real background thread acquires data automatically."""
        gw = None
        for g in st.session_state.gateways:
            if g["ip"] == gw_ip:
                gw = g
                break
        
        if gw is None:
            st.error("Gateway not found!")
            return
        
        st.markdown(f"#### Schedule Channels — **{gw['name']}**")
        
        # Initialize schedule groups state
        groups_key = f"schedule_groups_{gw_ip}"
        if groups_key not in st.session_state:
            st.session_state[groups_key] = []
        
        # Build available channel labels from configured channels
        available_channels = []
        for k, v in st.session_state.configured_channels.items():
            if k[0] == gw_ip and v.get("configured"):
                axis_str = f" — {v.get('axis')}" if v.get('axis') else ""
                label = f"CH{k[1]} ({v.get('type', '')}{axis_str})"
                available_channels.append(label)
        
        if not available_channels:
            st.warning("No configured channels found. Please configure channels first before scheduling.")
            return
        
        # ===== "+ Add Group" button =====
        col_header, col_btn = st.columns([3, 1])
        with col_header:
            st.markdown("##### Channel Groups")
        with col_btn:
            if st.button("➕ Add Group", type="primary", use_container_width=True):
                st.session_state[groups_key].append({
                    "name": f"Group {len(st.session_state[groups_key]) + 1}",
                    "channels": [],
                    "schedule_type": "Simple Interval",
                    "interval": "Every 1 hour",
                    "n_hours": 1,
                    "times_per_day": 2,
                    "daily_time": datetime.time(8, 0),
                    "enabled": True
                })
                st.rerun()
        
        # ===== Render each group as a card =====
        groups = st.session_state[groups_key]
        groups_to_delete = []
        
        for idx, grp in enumerate(groups):
            with st.container(border=True):
                # Group header: name + delete button
                c_name, c_del = st.columns([5, 1])
                with c_name:
                    grp["name"] = st.text_input("Group Name", value=grp.get("name", f"Group {idx+1}"),
                                                 key=f"grp_name_{gw_ip}_{idx}", label_visibility="collapsed",
                                                 placeholder="Enter group name...")
                with c_del:
                    if st.button("🗑️", key=f"grp_del_{gw_ip}_{idx}", help="Delete this group"):
                        groups_to_delete.append(idx)
                
                # Select Channels (multiselect)
                grp["channels"] = st.multiselect(
                    "Select Channels",
                    options=available_channels,
                    default=[ch for ch in grp.get("channels", []) if ch in available_channels],
                    key=f"grp_ch_{gw_ip}_{idx}"
                )
                
                # Schedule Type
                sched_types = ["Simple Interval", "Daily at Specific Time", "Multiple Times per Day", "Every N Hours"]
                curr_stype = grp.get("schedule_type", "Simple Interval")
                stype_idx = sched_types.index(curr_stype) if curr_stype in sched_types else 0
                grp["schedule_type"] = st.selectbox("Schedule Type", options=sched_types, index=stype_idx,
                                                     key=f"grp_stype_{gw_ip}_{idx}")
                
                # Conditional fields based on schedule type
                if grp["schedule_type"] == "Simple Interval":
                    interval_opts = [
                        "Every 5 seconds", "Every 1 minute",
                        "Every 5 minutes", "Every 10 minutes", "Every 15 minutes", "Every 30 minutes",
                        "Every 1 hour", "Every 2 hours", "Every 4 hours", "Every 8 hours",
                        "Every 12 hours", "Every 24 hours"
                    ]
                    curr_int = grp.get("interval", "Every 1 hour")
                    int_idx = interval_opts.index(curr_int) if curr_int in interval_opts else 6
                    grp["interval"] = st.selectbox("Read Interval", options=interval_opts, index=int_idx,
                                                    key=f"grp_int_{gw_ip}_{idx}")
                
                elif grp["schedule_type"] == "Daily at Specific Time":
                    grp["daily_time"] = st.time_input("Time of Day",
                        value=grp.get("daily_time", datetime.time(8, 0)),
                        key=f"grp_daily_{gw_ip}_{idx}")
                
                elif grp["schedule_type"] == "Multiple Times per Day":
                    grp["times_per_day"] = st.number_input("How many times per day?",
                        min_value=1, max_value=48, value=grp.get("times_per_day", 2),
                        key=f"grp_ntimes_{gw_ip}_{idx}")
                    grp["daily_time"] = st.time_input("First reading at",
                        value=grp.get("daily_time", datetime.time(6, 0)),
                        key=f"grp_mfirst_{gw_ip}_{idx}")
                
                elif grp["schedule_type"] == "Every N Hours":
                    grp["n_hours"] = st.number_input("Every N hours",
                        min_value=1, max_value=72, value=grp.get("n_hours", 1),
                        key=f"grp_nhours_{gw_ip}_{idx}")
                
                # Status toggle
                grp["enabled"] = st.toggle("Enabled", value=grp.get("enabled", True),
                                            key=f"grp_enabled_{gw_ip}_{idx}")
                
                # Show selected channels as colored pills
                if grp["channels"]:
                    pills_html = " ".join([
                        f'<span style="display:inline-block;padding:4px 12px;margin:2px;'
                        f'border-radius:20px;background:#3b82f6;color:white;font-size:12px;'
                        f'font-weight:500;">{ch}</span>'
                        for ch in grp["channels"]
                    ])
                    st.markdown(f"**Selected Channels:** {pills_html}", unsafe_allow_html=True)
        
        # Process group deletions
        if groups_to_delete:
            for idx in sorted(groups_to_delete, reverse=True):
                st.session_state[groups_key].pop(idx)
            st.rerun()
        
        # ===== Footer: Cancel + Save Schedule =====
        if groups:
            st.markdown("---")
            
            # Show scheduler status
            sched_info = st.session_state._scheduler_threads.get(gw_ip)
            if sched_info and sched_info["thread"].is_alive():
                st.success(f"🟢 Scheduler is **running** (started at {sched_info.get('started_at', '?')})")
                if st.button("⏹ Stop Scheduler", type="secondary", use_container_width=True):
                    _stop_scheduler(gw_ip)
                    st.info("Scheduler stopped.")
                    time.sleep(0.5)
                    st.rerun()
            
            c_cancel, c_save = st.columns(2)
            with c_cancel:
                if st.button("Cancel", use_container_width=True):
                    st.rerun()
            with c_save:
                if st.button("💾 Save & Start Schedule", type="primary", use_container_width=True):
                    # Save groups to session state
                    st.session_state[groups_key] = groups
                    
                    # Filter to only enabled groups with channels
                    active_groups = [g for g in groups if g.get("enabled") and g.get("channels")]
                    
                    if active_groups:
                        # Start the real background scheduler thread
                        gw_port = gw.get("port", 8020)
                        _start_scheduler(gw_ip, gw_port, active_groups)
                        st.success(f"Schedule saved! Scheduler started with {len(active_groups)} active group(s).")
                    else:
                        _stop_scheduler(gw_ip)
                        st.info("No active groups with channels — scheduler not started.")
                    
                    log_gateway_transaction("SCHEDULE", f"Saved {len(groups)} group(s) for {gw['name']}", "Success")
                    time.sleep(1)
                    st.rerun()

    # ===============================================
    # ===== Trigger Pending Actions =====
    # ===============================================
    if getattr(st.session_state, "pending_action", None):
        pending = st.session_state.pending_action
        st.session_state.pending_action = None  # Clear immediately
        
        if pending["action"] == "add_gw":
            add_gateway_dialog()
        # ===== Change 2: Vendor card click opens dialog with ITA pre-selected =====
        elif pending["action"] == "add_gw_ita":
            add_gateway_dialog(preset_vendor="ITA")
        elif pending["action"] == "logs":
            show_logs_dialog()
        elif pending["action"] == "config":
            configure_channel_dialog(pending["gw_ip"], pending["ch"])
        elif pending["action"] == "read":
            gw_port = 8020
            for g in st.session_state.gateways:
                if g["ip"] == pending["gw_ip"]:
                    gw_port = g["port"]
                    break
            take_reading_dialog(pending["gw_ip"], gw_port, pending["ch"])
        # ===== Change 4: Show manual =====
        elif pending["action"] == "show_manual":
            show_manual_dialog()
        # ===== Change 6: Edit gateway settings =====
        elif pending["action"] == "settings":
            edit_gateway_dialog(pending["gw_ip"])
        # ===== Change 7: Schedule readings =====
        elif pending["action"] == "schedule":
            schedule_readings_dialog(pending["gw_ip"])
