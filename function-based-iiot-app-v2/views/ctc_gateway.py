import streamlit as st
import numpy as np
import plotly.graph_objects as go
from core.state_manager import get_user_data, add_to_history
from hardware.gateway_bridge import ctc

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
                    ctc.subscribe()
                    add_to_history("CTC", "Subscribe", "Success")
                    st.success("Subscribed to telemetry topics")
                    st.rerun()
                else:
                    st.error("Connect first.")
        else:
            if c1.button("Unsubscribe", use_container_width=True):
                ctc.unsubscribe()
                add_to_history("CTC", "Unsubscribe", "Success")
                st.rerun()
            st.success("Currently Subscribed to Telemetry")
                
    with tab2:
        st.subheader("Live Data Stream")
        if not getattr(st.session_state, 'ctc_subscribed', False):
            st.info("Subscribe to at least one sensor to view data.")
        else:
            c_actions = st.columns(2)
            if c_actions[0].button("Poll Latest Data"):
                with st.spinner("Polling CTC data..."):
                    usr_data["last_ctc_data"] = ctc.get_current_data()
                add_to_history("CTC", "Poll Data", "Success")
                
            if c_actions[1].button("📥 Download Report (CSV)"):
                msg = ctc.csvf()
                st.success(msg)
                
            if usr_data.get("last_ctc_data"):
                data = usr_data["last_ctc_data"]
                
                st.markdown(f"**Serial**: {data.get('Serial', 'N/A')} | **Timestamp**: {data.get('timestamp', '')}")
                
                x_data = np.array(data.get("X", []))
                y_data = np.array(data.get("Y", []))
                z_data = np.array(data.get("Z", []))
                
                if len(x_data) > 0:
                    t = np.linspace(0, 1000, len(x_data))
                    
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
