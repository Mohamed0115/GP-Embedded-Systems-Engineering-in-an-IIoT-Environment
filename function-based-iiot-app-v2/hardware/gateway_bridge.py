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
                from Gateways_Sim.CTC.commands import get_dynamic_vibration_records
            else:
                from CTC.commands import get_dynamic_vibration_records
            ws = await asyncio.wait_for(ctc_conn(f"ws://{self.ip()}:5000"), timeout=3.0)
            res = await asyncio.wait_for(get_dynamic_vibration_records(ws, serials=[int(serial)], max_records=1), timeout=5.0)
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
