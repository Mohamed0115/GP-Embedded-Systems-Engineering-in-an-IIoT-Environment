import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
import datetime
import asyncio
import base64
import os
from core.state_manager import get_user_data, add_to_history
from core.utils import compute_fft, compute_rms

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
def acquire_channel_data(ip, port, channel, gain, measurement_type, sensitivity, fmax, lines):
    # Map measurement type to SP (Signal Path)
    # Velocity = 6 (hardware integrator + highpass filter per Chapter 5.6)
    # All other types = 1 (raw signal)
    sp = 6 if measurement_type.lower() == "velocity" else 1
    
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

    # ===== Change 8: Improved Configure Channel dialog =====
    # Follows ITA-110 Manual Chapter 5 for proper acquisition parameters.
    # Dynamic types: Acceleration, Velocity, Displacement use AQ command with Gain, Sensitivity, Fmax, Lines
    # Static types: Temperature, Pressure use AP command with Sensitivity only (no gain/fmax/lines)
    @st.dialog("⚙️ Configure Channel", width="medium")
    def configure_channel_dialog(gw_ip, ch_num):
        key = (gw_ip, ch_num)
        curr_config = st.session_state.configured_channels.get(key, {})
        
        st.markdown(f"#### Configure Channel **CH{ch_num}**")
        st.caption(f"Gateway: {gw_ip}")
        
        st.text_input("Location (Area - Machine - Point) *", value="Production Floor A", disabled=True)
        
        types = ["Select measurement type", "Acceleration", "Velocity", "Displacement", "Temperature", "Pressure"]
        curr_type = curr_config.get("type", "Select measurement type")
        type_idx = types.index(curr_type) if curr_type in types else 0
        m_type = st.selectbox("Measurement Type *", options=types, index=type_idx)
        
        # Dynamic template based on measurement type
        is_dynamic = m_type in ["Acceleration", "Velocity", "Displacement"]
        is_static = m_type in ["Temperature", "Pressure"]
        
        gain_val = "1"
        sensitivity_val = 100.0
        unit_val = "mV"
        fmax_val = 1000
        lines_val = 400
        
        if is_dynamic:
            # ===== Dynamic measurement: show Gain, Sensitivity, Fmax, Lines =====
            
            # Velocity uses hardware integrator (SP=6), so show a note
            if m_type == "Velocity":
                st.info("ℹ️ Velocity uses the hardware integrator (SP=6) to convert acceleration to velocity. See Manual Chapter 5.6.")
            
            gains = ["Select gain", "1", "2", "5", "10", "20", "50", "100"]
            curr_gain = curr_config.get("gain", "Select gain")
            gain_idx = gains.index(curr_gain) if curr_gain in gains else 0
            gain_val = st.selectbox("Gain *", options=gains, index=gain_idx,
                                     help="Gain multiplier for the ADC. Higher gain = more sensitivity but less range.")
            
            c_sens, c_unit = st.columns(2)
            with c_sens:
                sensitivity_val = st.number_input("Sensitivity *", min_value=0.1, value=float(curr_config.get("sensitivity", 100.0)), step=0.1, placeholder="e.g., 100")
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
            
            st.markdown("---")
            st.markdown("##### Acquisition Parameters")
            c_fmax, c_lines = st.columns(2)
            with c_fmax:
                # F1max options per Manual Chapter 5.1 — correspond to the 11 valid BW values
                fmax_opts = [25, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 40000]
                curr_fmax = curr_config.get("fmax", 1000)
                fmax_idx = fmax_opts.index(curr_fmax) if curr_fmax in fmax_opts else 5
                fmax_val = st.selectbox("F1max (Hz) *", options=fmax_opts, index=fmax_idx, help="Maximum frequency of interest (bandwidth)")
            with c_lines:
                # Spectral lines per Manual Chapter 5.2 — full set of valid values
                lines_opts = [25, 50, 100, 200, 400, 800, 1600, 3200, 6400, 12800, 25600, 51200]
                curr_lines = curr_config.get("lines", 400)
                lines_idx = lines_opts.index(curr_lines) if curr_lines in lines_opts else 4  # default 400
                lines_val = st.selectbox("Spectral Lines *", options=lines_opts, index=lines_idx, help="Number of spectral lines (resolution)")
            
            # Computed SR and TL per Chapter 5.1 and 5.2
            sr_computed = int(fmax_val * 2.56)
            tl_computed = int(lines_val * 2.56)
            # Acquisition time per Chapter 5.2: Taq = Lines / Bandwidth
            acq_time = lines_val / fmax_val
            st.info(f"SR = {sr_computed} Hz | TL = {tl_computed} samples | Acquisition Time ≈ {acq_time:.2f}s")
            
        elif is_static:
            # ===== Static measurement: Sensitivity only, no Gain/Fmax/Lines =====
            # Process measurements use AP command (not AQ), gain is always 1, per Manual Chapter 5.4
            st.caption("Static measurement — uses AP command. No dynamic acquisition parameters needed.")
            c_sens, c_unit = st.columns(2)
            with c_sens:
                sensitivity_val = st.number_input("Sensitivity *", min_value=0.1, value=float(curr_config.get("sensitivity", 100.0)), step=0.1, placeholder="e.g., 100")
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
        
        if m_type != "Select measurement type":
            if st.button("Save Configuration", type="primary", use_container_width=True):
                if is_dynamic and gain_val == "Select gain":
                    st.error("Please select a gain value!")
                else:
                    config_data = {
                        "type": m_type,
                        "gain": gain_val,
                        "sensitivity": sensitivity_val,
                        "unit": unit_val,
                        "configured": True
                    }
                    if is_dynamic:
                        config_data["fmax"] = fmax_val
                        config_data["lines"] = lines_val
                    st.session_state.configured_channels[key] = config_data
                    log_gateway_transaction("CONFIG_CHANNEL", f"Configured channel CH{ch_num} on {gw_ip} to {m_type} (Gain={gain_val}, Sens={sensitivity_val} {unit_val})", "Success")
                    st.success("Configuration saved!")
                    time.sleep(1)
                    st.rerun()

    # ===== Change 9: Renamed "Time Domain" → "Time Waveform" and "Frequency Domain (FFT)" → "Spectrum" =====
    @st.dialog("📊 Take Reading", width="large")
    def take_reading_dialog(gw_ip, gw_port, ch_num):
        key = (gw_ip, ch_num)
        config = st.session_state.configured_channels.get(key, {})
        
        m_type = config.get('type', '')
        is_static = m_type in ["Temperature", "Pressure"]
        
        st.markdown(f"### Take Reading on Channel **CH{ch_num}**")
        st.markdown(f"**Gateway**: `{gw_ip}:{gw_port}`  |  **Type**: `{m_type}` ({config.get('sensitivity')} {config.get('unit')}, Gain={config.get('gain')})")
        
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
                    raw_data, sr = acquire_channel_data(
                        ip=gw_ip,
                        port=gw_port,
                        channel=ch_num,
                        gain=config.get("gain"),
                        measurement_type=config.get("type"),
                        sensitivity=config.get("sensitivity"),
                        fmax=fmax,
                        lines=lines
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
            
            # ===== Change 9: Renamed tab labels =====
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
                    fig_fft = go.Figure(go.Scatter(x=f_list, y=fft_list, line=dict(color="#FF4B4B")))
                    fig_fft.update_layout(
                        xaxis_title="Frequency (Hz)", 
                        yaxis_title="Amplitude", 
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

    # ===== Change 7: Schedule Readings dialog =====
    @st.dialog("📅 Schedule Readings", width="medium")
    def schedule_readings_dialog(gw_ip):
        """Configure scheduled/automatic readings for a gateway."""
        gw = None
        for g in st.session_state.gateways:
            if g["ip"] == gw_ip:
                gw = g
                break
        
        if gw is None:
            st.error("Gateway not found!")
            return
        
        st.markdown(f"#### Schedule for **{gw['name']}**")
        st.caption(f"Configure automatic periodic readings for all configured channels.")
        
        # Initialize schedule state if needed
        sched_key = f"schedule_{gw_ip}"
        if sched_key not in st.session_state:
            st.session_state[sched_key] = {
                "enabled": False,
                "interval": "Every 1 hour",
                "start_time": datetime.time(8, 0),
                "channels": "All configured"
            }
        curr_sched = st.session_state[sched_key]
        
        # Enable/disable toggle
        enabled = st.toggle("Enable Scheduled Readings", value=curr_sched.get("enabled", False))
        
        if enabled:
            st.markdown("---")
            
            # Interval selection
            interval_opts = [
                "Every 5 minutes", "Every 10 minutes", "Every 15 minutes", "Every 30 minutes",
                "Every 1 hour", "Every 2 hours", "Every 4 hours", "Every 8 hours",
                "Every 12 hours", "Every 24 hours"
            ]
            curr_interval = curr_sched.get("interval", "Every 1 hour")
            interval_idx = interval_opts.index(curr_interval) if curr_interval in interval_opts else 4
            interval = st.selectbox("Reading Interval", options=interval_opts, index=interval_idx)
            
            # Start time
            start_time = st.time_input("Start Time", value=curr_sched.get("start_time", datetime.time(8, 0)))
            
            # Channel selection
            ch_opts = ["All configured"]
            # Add individually configured channels
            for k, v in st.session_state.configured_channels.items():
                if k[0] == gw_ip and v.get("configured"):
                    ch_opts.append(f"CH{k[1]} ({v.get('type', '')})")
            
            channel_sel = st.selectbox("Channels to Read", options=ch_opts)
            
            st.markdown("---")
            
            # Save button
            if st.button("Save Schedule", type="primary", use_container_width=True):
                st.session_state[sched_key] = {
                    "enabled": True,
                    "interval": interval,
                    "start_time": start_time,
                    "channels": channel_sel
                }
                log_gateway_transaction("SCHEDULE", f"Scheduled readings for {gw['name']}: {interval} starting at {start_time}", "Success")
                st.success("Schedule saved!")
                time.sleep(1)
                st.rerun()
            
            # Info about backend requirement
            st.warning("⚠️ Note: Scheduled readings require a backend scheduler service (not yet connected). The schedule configuration is saved but readings will not run automatically until the backend is integrated.")
        else:
            # Disable schedule
            if curr_sched.get("enabled"):
                if st.button("Disable Schedule", type="secondary", use_container_width=True):
                    st.session_state[sched_key]["enabled"] = False
                    log_gateway_transaction("SCHEDULE", f"Disabled scheduled readings for {gw['name']}", "Success")
                    st.info("Schedule disabled.")
                    time.sleep(1)
                    st.rerun()
            else:
                st.caption("Toggle the switch above to configure automatic readings.")

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
