import streamlit as st
import asyncio
import sys, os

SIMULATION_MODE = False

if SIMULATION_MODE:
    from Gateways_Sim.ITA.CDSR import connect as ita_conn, disconnect as ita_disconn
    from Gateways_Sim.ITA.commands_ip import excute_data_command, excute_command
    from Gateways_Sim.CTC.functions import conn as ctc_conn, close as ctc_disconn
    from Gateways_Sim.CTC.commands import take_dynamic_vibration_reading
else:
    gw_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Gateways'))
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
        st.session_state.ctc_connected = True
        st.session_state.ctc_ip = ip
    def disconnect(self):
        st.session_state.ctc_connected = False
    def subscribe(self):
        st.session_state.ctc_subscribed = True
    def unsubscribe(self):
        st.session_state.ctc_subscribed = False
    def get_current_data(self):
        async def _run():
            ws = await ctc_conn(f"ws://{self.ip()}:5000")
            res = await take_dynamic_vibration_reading(ws, 12345)
            if "Data" in res and len(res["Data"]) > 0:
                vib = res["Data"][0].get("Vibration", 0.0)
                return {"Serial": "12345", "timestamp": "Now", "X": [vib]*50, "Y": [vib*.5]*50, "Z": [vib*.2]*50}
            return None
        return asyncio.run(_run())
    def csvf(self): return "Exported CSV"

ita = ITAWrapper()
ctc = CTCWrapper()
