import streamlit as st
from core.state_manager import get_user_data, add_to_history
from hardware.gateway_bridge import ita, ctc

def dashboard_view():
    usr_data = get_user_data()
    st.title("Dashboard Overview 📊")
    
    system_status = "Healthy"
    alerts = "0 Alerts"
    status_color = "normal"
    if usr_data["history"] and any(h.get("Status") == "Error" for h in usr_data["history"][:2]):
        system_status = "Warning"
        alerts = "Check Logs"
        status_color = "off"
    
    active_gws = sum([bool(getattr(st.session_state, 'ita_connected', False)), bool(getattr(st.session_state, 'ctc_connected', False))])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Active Gateways", str(active_gws), delta="Online", delta_color="normal")
    with col2: st.metric("Total Machines", str(len(usr_data["machines"])), delta="Active", delta_color="off")
    with col3: st.metric("Recent Readings", str(len(usr_data["history"])), delta="Total", delta_color="off")
    with col4: st.metric("System Status", system_status, delta=alerts, delta_color=status_color)
    
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
            """.format(ita.ip(), "#4CAF50" if ita_connected else "#ef5350", "Connected 🟢" if ita_connected else "Disconnected 🔴"), unsafe_allow_html=True)
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
            """.format(ctc.ip(), "#4CAF50" if ctc_connected else "#ef5350", "Connected 🟢" if ctc_connected else "Disconnected 🔴"), unsafe_allow_html=True)
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
