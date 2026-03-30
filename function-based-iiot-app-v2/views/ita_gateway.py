import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from core.state_manager import get_user_data, add_to_history
from hardware.gateway_bridge import ita
from core.utils import compute_fft, compute_rms

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
        
        if usr_data.get("last_ita_reading"):
            data = usr_data["last_ita_reading"]
            
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
                
            st.markdown("### Raw Sensor Data Table")
            df = pd.DataFrame({
                "X": data.get("x", []),
                "Y": data.get("y", []),
                "Z": data.get("z", [])
            })
            st.dataframe(df.head(5), use_container_width=True)
            
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
                        if usr_data.get("show_rms"): st.info(f"RMS X: {compute_rms(x_data):.4f} g")
                    with tabs[1]:
                        fig = go.Figure(go.Scatter(x=t, y=y_data, line=dict(color="#00D26A")))
                        fig.update_layout(xaxis_title="Time (ms)", yaxis_title="Acc (g)", template="plotly_dark", margin=dict(l=20,r=20,t=20,b=20))
                        st.plotly_chart(fig, use_container_width=True)
                        if usr_data.get("show_rms"): st.info(f"RMS Y: {compute_rms(y_data):.4f} g")
                    with tabs[2]:
                        fig = go.Figure(go.Scatter(x=t, y=z_data, line=dict(color="#4A90E2")))
                        fig.update_layout(xaxis_title="Time (ms)", yaxis_title="Acc (g)", template="plotly_dark", margin=dict(l=20,r=20,t=20,b=20))
                        st.plotly_chart(fig, use_container_width=True)
                        if usr_data.get("show_rms"): st.info(f"RMS Z: {compute_rms(z_data):.4f} g")
                    st.markdown("</div>", unsafe_allow_html=True)
                
                if usr_data.get("show_fft"):
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
