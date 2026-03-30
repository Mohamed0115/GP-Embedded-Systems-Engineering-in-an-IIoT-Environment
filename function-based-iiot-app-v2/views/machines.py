import streamlit as st
import time

def machines_view():
    st.title("🏭 Machines & Fault Diagnosis")
    
    st.subheader("Machine Layout")
    
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
