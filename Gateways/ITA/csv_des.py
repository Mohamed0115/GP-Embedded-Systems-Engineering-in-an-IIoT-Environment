from parameters_con import parameters
from commands_ip import excute_command
import time
import csv
import asyncio
import sys

async def take_A_decision(reader,writer):
    print("not9")
    user_input = await to_of_input("\n Enter command e.g. 'DT 28/01/25' or 'c' to change config or Enter to continue")

    if user_input == 'c':
        used_parameters = parameters()
        await excute_command(reader,writer,used_parameters)
    
    elif user_input:
        await excute_command(reader,writer,user_input)

async def to_of_input(Question,timeout =5):
    print(Question)
    loop = asyncio.get_running_loop() 
    try:
        future = loop.run_in_executor(None, sys.stdin.readline) #
        result = await asyncio.wait_for(future, timeout) #
        if 'C' in result:
            return result.strip().lower()
        return result.strip()
    except asyncio.TimeoutError:
        print("\nTimeout - continuing...")
        return ''

def csvf(data_resp,axis):
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f'ita_data_{timestamp}-{axis}.csv'
    with open(filename, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Sample Index', 'Raw Value'])  # Header
        for idx, value in enumerate(data_resp['response']):
            csv_writer.writerow([idx, value])