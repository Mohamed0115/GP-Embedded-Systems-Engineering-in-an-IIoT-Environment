# ============================================================================
# db_gateway_helpers.py — PostgreSQL Database Helpers for gateways.py
# ============================================================================
# This file is ALL COMMENTS. Nothing here runs.
# Your job is to UNCOMMENT and implement each function below using psycopg2.
#
# STEP 0: Install psycopg2
# --------------------------
#   pip install psycopg2-binary
#
# STEP 1: Create your PostgreSQL connection
# -------------------------------------------
# import psycopg2
# from psycopg2.extras import RealDictCursor
#
# DB_CONFIG = {
#     "host": "localhost",
#     "port": 5432,
#     "dbname": "iiot_platform",
#     "user": "your_username",
#     "password": "your_password"
# }
#
# def get_db_connection():
#     """Open a new PostgreSQL connection. Always close after use."""
#     conn = psycopg2.connect(**DB_CONFIG)
#     return conn
#
#
# ============================================================================
# STEP 2: Create Tables (run this SQL once in pgAdmin or psql)
# ============================================================================
#
# -- Table: gateways
# -- Stores each gateway device that the user adds from the "Add Gateway" dialog.
# CREATE TABLE gateways (
#     ip          VARCHAR(45) PRIMARY KEY,   -- e.g. "192.168.1.130"
#     port        INTEGER NOT NULL DEFAULT 8020,
#     vendor      VARCHAR(20) NOT NULL,      -- "ITA" or "CTC"
#     name        VARCHAR(100) NOT NULL,     -- User-given name like "Gateway-001"
#     location    VARCHAR(200) DEFAULT 'Not specified',
#     model       VARCHAR(50) DEFAULT 'ITA-110',
#     sn          VARCHAR(100) NOT NULL,     -- Serial number
#     status      VARCHAR(20) DEFAULT 'online',   -- "online" / "offline"
#     last_seen   VARCHAR(50) DEFAULT '1s ago',
#     connection  VARCHAR(20) DEFAULT 'Ethernet', -- "Ethernet" / "WiFi"
#     channels    INTEGER DEFAULT 16,
#     sampling    VARCHAR(20) DEFAULT 'Paused',   -- "Running" / "Paused"
#     date_added  VARCHAR(20)                      -- e.g. "06/19/2026"
# );
#
# -- Table: channel_configs
# -- Stores the sensor configuration for each channel on each gateway.
# -- The primary key is (gateway_ip + channel_num) — one config per channel.
# CREATE TABLE channel_configs (
#     gateway_ip      VARCHAR(45) NOT NULL REFERENCES gateways(ip) ON DELETE CASCADE,
#     channel_num     INTEGER NOT NULL,
#     type            VARCHAR(30),       -- "Acceleration", "Velocity", "Displacement", "Temperature", "Pressure"
#     gain            VARCHAR(10),       -- "1", "2", "5", "10", "20", "50", "100"
#     sensitivity     FLOAT DEFAULT 100.0,
#     unit            VARCHAR(20),       -- "mV/g", "mV/mm/s", "mV/µm", "mV/°C", "mV/Bar", "mV"
#     fmax            INTEGER,           -- e.g. 1000 (Hz)
#     lines           INTEGER,           -- e.g. 400
#     signal_path_sp  INTEGER DEFAULT 1, -- SP value: 1=Raw, 2=Band, 3=Demod, 5=HPF, 6=HW HPF
#     axis            VARCHAR(30),       -- "X Axis", "Y Axis", "Z Axis", "H Axis", "V Axis", "A Axis"
#     hpf             VARCHAR(30),       -- Optional: "HPF 0.5 Hz", "HPF 2 Hz", etc.
#     bpf             VARCHAR(60),       -- Optional: "Low: 50 Hz, High: 200 Hz", etc.
#     point_id        VARCHAR(50),       -- Links to diagnosis hierarchy point (e.g. "pt_abc123")
#     location_display VARCHAR(300),     -- Human-readable path like "RITEC > Cairo > Compressors > A-341A > MNDE"
#     configured      BOOLEAN DEFAULT TRUE,
#     last_val        VARCHAR(20),       -- Last RMS reading value as string (e.g. "0.0234")
#     last_unit       VARCHAR(10),       -- e.g. "g", "mm/s"
#     last_time       VARCHAR(20),       -- e.g. "14:32:05"
#     PRIMARY KEY (gateway_ip, channel_num)
# );
#
# -- Table: readings
# -- Stores every data acquisition result. Each row = one reading from one channel.
# -- WARNING: time_waveform, spectrum_freq, spectrum_amp can be HUGE arrays (thousands of floats).
# --   Option A: Store as JSONB (simple but bloats DB).
# --   Option B: Save arrays to .csv files on disk and store the file path here (recommended).
# CREATE TABLE readings (
#     id              SERIAL PRIMARY KEY,
#     gateway_ip      VARCHAR(45) NOT NULL,
#     channel_num     INTEGER NOT NULL,
#     point_id        VARCHAR(50),        -- Which diagnosis point this reading belongs to
#     axis            VARCHAR(30),        -- "V Axis", "H Axis", etc.
#     time_waveform   JSONB,              -- Array of calibrated float values  (or file path as TEXT)
#     spectrum_freq   JSONB,              -- Array of frequency bins            (or file path as TEXT)
#     spectrum_amp    JSONB,              -- Array of FFT amplitude values      (or file path as TEXT)
#     sr              INTEGER,            -- Sample rate used for this reading
#     rms_value       FLOAT,              -- Pre-computed RMS for quick display
#     timestamp       TIMESTAMP DEFAULT NOW(),
#     FOREIGN KEY (gateway_ip, channel_num) REFERENCES channel_configs(gateway_ip, channel_num) ON DELETE CASCADE
# );
#
# -- Table: scheduler_groups
# -- Stores the schedule groups that the user creates in the "Schedule Channels" dialog.
# CREATE TABLE scheduler_groups (
#     id              SERIAL PRIMARY KEY,
#     gateway_ip      VARCHAR(45) NOT NULL REFERENCES gateways(ip) ON DELETE CASCADE,
#     group_name      VARCHAR(100) DEFAULT 'Group 1',
#     channels        JSONB DEFAULT '[]',     -- Array of channel labels like ["CH3 (Acceleration — V Axis)"]
#     schedule_type   VARCHAR(30) DEFAULT 'Simple Interval', -- "Simple Interval", "Daily at Specific Time", etc.
#     interval        VARCHAR(30) DEFAULT 'Every 1 hour',    -- For "Simple Interval" type
#     n_hours         INTEGER DEFAULT 1,                     -- For "Every N Hours" type
#     times_per_day   INTEGER DEFAULT 2,                     -- For "Multiple Times per Day" type
#     daily_time      TIME DEFAULT '08:00:00',               -- For "Daily" and "Multiple" types
#     enabled         BOOLEAN DEFAULT TRUE
# );
#
# -- Table: gateway_logs  (OPTIONAL — you may keep this in session_state if you only need current-session logs)
# -- Stores the low-level hardware command logs (CH, GA, SP, SR, AQ, BD?, etc.)
# CREATE TABLE gateway_logs (
#     id              SERIAL PRIMARY KEY,
#     timestamp       TIMESTAMP DEFAULT NOW(),
#     command         VARCHAR(100),      -- e.g. "CONNECT", "SEND", "RECEIVE", "DISCONNECT"
#     response        TEXT,              -- The response text from the gateway
#     status          VARCHAR(20)        -- "Success", "Failed", "Pending"
# );
#
#
# ============================================================================
# STEP 3: Python helper functions (uncomment and implement)
# ============================================================================
#
# ------- GATEWAYS -------
#
# def db_get_all_gateways():
#     """Fetch all gateways from the database and return as a list of dicts.
#     This replaces: st.session_state.gateways
#     Called at: gateways_view() initialization (line ~112)
#     """
#     conn = get_db_connection()
#     cur = conn.cursor(cursor_factory=RealDictCursor)
#     cur.execute("SELECT * FROM gateways ORDER BY date_added DESC")
#     rows = cur.fetchall()
#     cur.close()
#     conn.close()
#     return [dict(row) for row in rows]
#
#
# def db_insert_gateway(gateway_dict):
#     """Insert a new gateway into the database.
#     This replaces: st.session_state.gateways.append(new_gw)
#     Called at: add_gateway_dialog() when user clicks "Create Gateway" (line ~302)
#     
#     gateway_dict keys: name, location, model, sn, status, last_seen, connection, ip, port, channels, sampling, date_added
#     """
#     conn = get_db_connection()
#     cur = conn.cursor()
#     cur.execute("""
#         INSERT INTO gateways (ip, port, vendor, name, location, model, sn, status, last_seen, connection, channels, sampling, date_added)
#         VALUES (%(ip)s, %(port)s, %(vendor)s, %(name)s, %(location)s, %(model)s, %(sn)s, %(status)s, %(last_seen)s, %(connection)s, %(channels)s, %(sampling)s, %(date_added)s)
#     """, gateway_dict)
#     conn.commit()
#     cur.close()
#     conn.close()
#
#
# def db_delete_gateway(ip):
#     """Delete a gateway by IP. CASCADE will also delete its channel_configs, scheduler_groups, readings.
#     This replaces: st.session_state.gateways = [g for g in st.session_state.gateways if g["ip"] != gw_ip]
#     Called at: action == "delete_gw" handler (line ~166)
#     """
#     conn = get_db_connection()
#     cur = conn.cursor()
#     cur.execute("DELETE FROM gateways WHERE ip = %s", (ip,))
#     conn.commit()
#     cur.close()
#     conn.close()
#
#
# def db_update_gateway(ip, updates_dict):
#     """Update a gateway's fields (name, location, sn, ip, port, connection).
#     This replaces: st.session_state.gateways[gw_idx]["name"] = g_name  (lines ~757-762)
#     Called at: edit_gateway_dialog() when user clicks "Save Changes" (line ~752)
#     
#     updates_dict example: {"name": "Gateway-002", "location": "Floor B", "sn": "ITA-120-NEW", ...}
#     """
#     conn = get_db_connection()
#     cur = conn.cursor()
#     set_clause = ", ".join([f"{k} = %s" for k in updates_dict.keys()])
#     values = list(updates_dict.values()) + [ip]
#     cur.execute(f"UPDATE gateways SET {set_clause} WHERE ip = %s", values)
#     conn.commit()
#     cur.close()
#     conn.close()
#
#
# def db_update_gateway_status(ip, status, sampling=None):
#     """Update gateway online/offline status and optionally sampling state.
#     This replaces: g["status"] = "online" / g["sampling"] = "Running"  (lines ~161, ~176)
#     Called at: toggle_sampling and reconnect_gw actions
#     """
#     conn = get_db_connection()
#     cur = conn.cursor()
#     if sampling:
#         cur.execute("UPDATE gateways SET status = %s, sampling = %s WHERE ip = %s", (status, sampling, ip))
#     else:
#         cur.execute("UPDATE gateways SET status = %s WHERE ip = %s", (status, ip))
#     conn.commit()
#     cur.close()
#     conn.close()
#
#
# ------- CHANNEL CONFIGS -------
#
# def db_get_all_channel_configs():
#     """Fetch all channel configs and return as a dict keyed by (gateway_ip, channel_num).
#     This replaces: st.session_state.configured_channels
#     Called at: gateways_view() initialization (line ~115)
#     """
#     conn = get_db_connection()
#     cur = conn.cursor(cursor_factory=RealDictCursor)
#     cur.execute("SELECT * FROM channel_configs")
#     rows = cur.fetchall()
#     cur.close()
#     conn.close()
#     result = {}
#     for row in rows:
#         key = (row["gateway_ip"], row["channel_num"])
#         result[key] = dict(row)
#     return result
#
#
# def db_upsert_channel_config(gateway_ip, channel_num, config_dict):
#     """Insert or update a channel configuration.
#     This replaces: st.session_state.configured_channels[key] = config_data
#     Called at: configure_channel_dialog() "Save Configuration" button (line ~539)
#               and after a reading updates last_val/last_unit/last_time (line ~604)
#     
#     config_dict keys: type, gain, sensitivity, unit, fmax, lines, signal_path_sp, axis, hpf, bpf,
#                       point_id, location_display, configured, last_val, last_unit, last_time
#     """
#     conn = get_db_connection()
#     cur = conn.cursor()
#     cur.execute("""
#         INSERT INTO channel_configs (gateway_ip, channel_num, type, gain, sensitivity, unit, fmax, lines,
#             signal_path_sp, axis, hpf, bpf, point_id, location_display, configured, last_val, last_unit, last_time)
#         VALUES (%s, %s, %(type)s, %(gain)s, %(sensitivity)s, %(unit)s, %(fmax)s, %(lines)s,
#             %(signal_path_sp)s, %(axis)s, %(hpf)s, %(bpf)s, %(point_id)s, %(location_display)s,
#             %(configured)s, %(last_val)s, %(last_unit)s, %(last_time)s)
#         ON CONFLICT (gateway_ip, channel_num)
#         DO UPDATE SET
#             type = EXCLUDED.type,
#             gain = EXCLUDED.gain,
#             sensitivity = EXCLUDED.sensitivity,
#             unit = EXCLUDED.unit,
#             fmax = EXCLUDED.fmax,
#             lines = EXCLUDED.lines,
#             signal_path_sp = EXCLUDED.signal_path_sp,
#             axis = EXCLUDED.axis,
#             hpf = EXCLUDED.hpf,
#             bpf = EXCLUDED.bpf,
#             point_id = EXCLUDED.point_id,
#             location_display = EXCLUDED.location_display,
#             configured = EXCLUDED.configured,
#             last_val = EXCLUDED.last_val,
#             last_unit = EXCLUDED.last_unit,
#             last_time = EXCLUDED.last_time
#     """, {"gateway_ip": gateway_ip, "channel_num": channel_num, **config_dict})
#     conn.commit()
#     cur.close()
#     conn.close()
#
#
# ------- READINGS -------
#
# def db_insert_reading(gateway_ip, channel_num, point_id, axis, calibrated, freq_list, amp_list, sr, rms_value):
#     """Insert a new reading into the database.
#     This replaces: diag_nodes[pt_id]["readings"][axis_name] = {...}
#     Called at: take_reading_dialog() after acquire_channel_data() succeeds (lines ~606-620)
#               and _run_scheduler_loop() after scheduled acquisition (lines ~860-865)
#     
#     IMPORTANT: calibrated, freq_list, amp_list are Python lists of floats — potentially thousands of values.
#     Option A (simple): Pass them as JSON using psycopg2.extras.Json()
#     Option B (recommended for production): Save to .csv/.parquet file, store file path instead.
#     """
#     import json
#     conn = get_db_connection()
#     cur = conn.cursor()
#     cur.execute("""
#         INSERT INTO readings (gateway_ip, channel_num, point_id, axis, time_waveform, spectrum_freq, spectrum_amp, sr, rms_value)
#         VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s)
#     """, (gateway_ip, channel_num, point_id, axis,
#           json.dumps(calibrated), json.dumps(freq_list), json.dumps(amp_list),
#           sr, rms_value))
#     conn.commit()
#     cur.close()
#     conn.close()
#
#
# def db_get_readings_for_point(point_id):
#     """Fetch all readings for a diagnosis point, grouped by axis.
#     This replaces: diag_nodes[pt_id]["readings"]
#     Called at: new_diagnosis.py when rendering the point detail view
#     
#     Returns: dict like {"V Axis": {"time_waveform": [...], "spectrum_freq": [...], ...}, ...}
#     """
#     conn = get_db_connection()
#     cur = conn.cursor(cursor_factory=RealDictCursor)
#     cur.execute("""
#         SELECT axis, time_waveform, spectrum_freq, spectrum_amp, sr, timestamp
#         FROM readings
#         WHERE point_id = %s
#         ORDER BY timestamp DESC
#     """, (point_id,))
#     rows = cur.fetchall()
#     cur.close()
#     conn.close()
#     result = {}
#     for row in rows:
#         axis = row["axis"]
#         if axis not in result:  # Only keep the latest reading per axis
#             result[axis] = {
#                 "time_waveform": row["time_waveform"],
#                 "spectrum_freq": row["spectrum_freq"],
#                 "spectrum_amp": row["spectrum_amp"],
#                 "sr": row["sr"],
#                 "timestamp": row["timestamp"].isoformat() if row["timestamp"] else ""
#             }
#     return result
#
#
# ------- SCHEDULER GROUPS -------
#
# def db_get_scheduler_groups(gateway_ip):
#     """Fetch all schedule groups for a gateway.
#     This replaces: st.session_state[groups_key]  where groups_key = f"schedule_groups_{gw_ip}"
#     Called at: schedule_readings_dialog() initialization (line ~939)
#     """
#     conn = get_db_connection()
#     cur = conn.cursor(cursor_factory=RealDictCursor)
#     cur.execute("SELECT * FROM scheduler_groups WHERE gateway_ip = %s ORDER BY id", (gateway_ip,))
#     rows = cur.fetchall()
#     cur.close()
#     conn.close()
#     groups = []
#     for row in rows:
#         groups.append({
#             "id": row["id"],
#             "name": row["group_name"],
#             "channels": row["channels"],   # Already a Python list thanks to JSONB
#             "schedule_type": row["schedule_type"],
#             "interval": row["interval"],
#             "n_hours": row["n_hours"],
#             "times_per_day": row["times_per_day"],
#             "daily_time": row["daily_time"],
#             "enabled": row["enabled"]
#         })
#     return groups
#
#
# def db_insert_scheduler_group(gateway_ip, group_dict):
#     """Insert a new schedule group.
#     This replaces: st.session_state[groups_key].append({...})
#     Called at: schedule_readings_dialog() "Add Group" button (line ~960)
#     """
#     import json
#     conn = get_db_connection()
#     cur = conn.cursor()
#     cur.execute("""
#         INSERT INTO scheduler_groups (gateway_ip, group_name, channels, schedule_type, interval, n_hours, times_per_day, daily_time, enabled)
#         VALUES (%s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s)
#     """, (gateway_ip, group_dict["name"], json.dumps(group_dict["channels"]),
#           group_dict["schedule_type"], group_dict["interval"],
#           group_dict["n_hours"], group_dict["times_per_day"],
#           str(group_dict.get("daily_time", "08:00:00")),
#           group_dict["enabled"]))
#     conn.commit()
#     cur.close()
#     conn.close()
#
#
# def db_delete_scheduler_group(group_id):
#     """Delete a schedule group by its database ID.
#     This replaces: st.session_state[groups_key].pop(idx)
#     Called at: schedule_readings_dialog() when user clicks trash icon (line ~1051)
#     """
#     conn = get_db_connection()
#     cur = conn.cursor()
#     cur.execute("DELETE FROM scheduler_groups WHERE id = %s", (group_id,))
#     conn.commit()
#     cur.close()
#     conn.close()
#
#
# def db_save_all_scheduler_groups(gateway_ip, groups_list):
#     """Replace all groups for a gateway with the given list (delete + re-insert).
#     This replaces: st.session_state[groups_key] = groups
#     Called at: schedule_readings_dialog() "Save & Start Schedule" button (line ~1075)
#     """
#     import json
#     conn = get_db_connection()
#     cur = conn.cursor()
#     # Delete all existing groups for this gateway
#     cur.execute("DELETE FROM scheduler_groups WHERE gateway_ip = %s", (gateway_ip,))
#     # Re-insert all groups
#     for grp in groups_list:
#         cur.execute("""
#             INSERT INTO scheduler_groups (gateway_ip, group_name, channels, schedule_type, interval, n_hours, times_per_day, daily_time, enabled)
#             VALUES (%s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s)
#         """, (gateway_ip, grp["name"], json.dumps(grp["channels"]),
#               grp["schedule_type"], grp.get("interval", "Every 1 hour"),
#               grp.get("n_hours", 1), grp.get("times_per_day", 2),
#               str(grp.get("daily_time", "08:00:00")),
#               grp.get("enabled", True)))
#     conn.commit()
#     cur.close()
#     conn.close()
#
#
# ------- GATEWAY LOGS (OPTIONAL) -------
#
# def db_insert_gateway_log(command, response, status):
#     """Insert a hardware transaction log.
#     This replaces: st.session_state.gateway_logs.append({...})
#     Called at: log_gateway_transaction() (line ~27)
#     NOTE: This is OPTIONAL. You may choose to keep logs in session_state if you only
#     need them during the current browser session. If you want persistent logs, use this.
#     """
#     conn = get_db_connection()
#     cur = conn.cursor()
#     cur.execute("""
#         INSERT INTO gateway_logs (command, response, status)
#         VALUES (%s, %s, %s)
#     """, (command, response, status))
#     conn.commit()
#     cur.close()
#     conn.close()
#
#
# def db_get_all_gateway_logs():
#     """Fetch all logs for the logs dialog.
#     This replaces: st.session_state.gateway_logs
#     Called at: show_logs_dialog() (line ~204)
#     """
#     conn = get_db_connection()
#     cur = conn.cursor(cursor_factory=RealDictCursor)
#     cur.execute("SELECT * FROM gateway_logs ORDER BY timestamp DESC LIMIT 200")
#     rows = cur.fetchall()
#     cur.close()
#     conn.close()
#     return [dict(row) for row in rows]
#
#
# def db_clear_gateway_logs():
#     """Delete all gateway logs.
#     This replaces: st.session_state.gateway_logs = []
#     Called at: show_logs_dialog() "Clear Logs" button (line ~242)
#     """
#     conn = get_db_connection()
#     cur = conn.cursor()
#     cur.execute("DELETE FROM gateway_logs")
#     conn.commit()
#     cur.close()
#     conn.close()
