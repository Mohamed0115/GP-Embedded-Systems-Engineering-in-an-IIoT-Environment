import sys
import os

sys.path.append(os.path.abspath("../Gateways"))
sys.path.append(os.path.abspath("../Gateways/ITA"))

from ITA.CDSR import connect as ita_conn, disconnect as ita_disconn
from ITA.commands_ip import excute_data_command, excute_command
from CTC.functions import conn as ctc_conn
from CTC.commands import take_dynamic_vibration_reading

print("IMPORTS SUCCESSFUL!")
