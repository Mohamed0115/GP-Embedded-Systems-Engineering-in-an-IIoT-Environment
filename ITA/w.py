import asyncio
import re  # For IP validation
import csv  # For saving to file
import time  # For timestamps and sleep
import select  # For non-blocking input
import sys  # For stdin
from connect import connect
from disconnect import disconnect
from send import send
from receiver import receive

def timed_input(prompt, timeout_sec=5):
    """Synchronous timed input using select."""
    print(prompt, end='', flush=True)
    ready, _, _ = select.select([sys.stdin], [], [], timeout_sec)
    if ready:
        return sys.stdin.readline().strip().lower()
    return ''  # Default skip

async def main_async():
    ip = input("Enter ITA-110 IP address: ") or '192.168.13.10'
    # Validate IP format
    if not re.match(r'^(\d{1,3}\.){3}\d{1,3}$', ip) or any(int(octet) > 255 for octet in ip.split('.')):
        print(f"Invalid IP address: {ip}. Example: 192.168.13.10")
        return
    
    port = 8020
    timeout = 30
    interval_seconds = int(input("Enter interval between acquisitions (seconds, e.g. 10): ") or 10)  # New: User sets loop delay
    
    channel = int(input("Enter channel (1-16): ") or 1)
    gain = int(input("Enter gain (1,2,5,10,20,50,100): ") or 10)
    signal_path = int(input("Enter signal path (1-6): ") or 1)
    sample_rate = int(input("Enter sample rate (Hz, e.g. 5120 for 2kHz BW): ") or 5120)
    trace_length = int(input("Enter trace length (e.g. 1024 for 400 lines): ") or 1024)
    to_timeout = int(input("Enter timeout (1-99 min): ") or 5)
    
    # Function to generate setup commands (reusable for config change)
    def get_setup_commands(ch, ga, sp, sr, tl, to_val):
        return [
            f"CH {ch}",
            f"GA {ga}",
            f"SP {sp}",
            f"SR {sr}",
            f"TL {tl}",
            f"TO {to_val}"
        ]
    
    setup_commands = get_setup_commands(channel, gain, signal_path, sample_rate, trace_length, to_timeout)
    
    reader = None
    writer = None
    try:
        reader, writer = await connect(ip, port, timeout)
        print("Connected.")
        
        # Test basic communication
        await send(writer, 'FV?')
        fv_resp = await receive(reader, 'FV?')
        print(f"Firmware version: {fv_resp['response']}")
        
        # Check device status
        await send(writer, 'DS?')
        status_resp = await receive(reader, 'DS?')
        print(f"Device status: {status_resp['response']}")
        if 'ER' in status_resp['response'] or 'BUSY' in status_resp['response']:
            raise ValueError("Device not ready - check errors or reset")
        
        # Send initial setup
        for cmd in setup_commands:
            print(f"Sending: {cmd}")
            await send(writer, cmd)
            resp = await receive(reader, timeout=timeout)
            print(f"Response: {resp['response'] if resp['type'] == 'ascii' else resp}")
            if 'NA' in resp.get('response', '') or 'ER' in resp.get('response', ''):
                raise ValueError(f"Error in setup command {cmd}")
            await asyncio.sleep(0.5)
        
        # Continuous loop for acquisition
        acquisition_count = 0
        while True:  # Runs forever; Ctrl+C to stop
            acquisition_count += 1
            print(f"\nAcquisition #{acquisition_count}:")
            
            # Acquire data
            print("Sending: AQ")
            await send(writer, 'AQ')
            aq_resp = await receive(reader, timeout=timeout * 2)
            print(f"AQ response: {aq_resp['response']}")
            if 'OK:AQ' not in aq_resp['response']:
                raise ValueError("Acquisition failed - possible trigger/gate issue")
            
            # Fetch binary data
            print("Sending: BD?")
            await send(writer, 'BD?')
            data_resp = await receive(reader, command='BD?', timeout=timeout * 3)
            print(f"Data: Type={data_resp['type']}, Length={data_resp['trace_length']}, Samples (first 5): {data_resp['data'][:5]}")
            
            # Save to separate CSV with timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f'ita_data_{timestamp}.csv'
            with open(filename, 'w', newline='') as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow(['Sample Index', 'Raw Value'])  # Header
                for idx, value in enumerate(data_resp['data']):
                    csv_writer.writerow([idx, value])
            print(f"Data saved to {filename} (full {data_resp['trace_length']} samples).")
            
            # Timed input (5s) for command or config - default continue if timeout or enter
            user_input = await asyncio.to_thread(timed_input, "\nEnter command (e.g., 'DT 24/12/25'), 'c' to change config, or press Enter to continue (skips in 5s if no input): ")
            
            if user_input == 'c':
                print("Changing config...")
                channel = int(input("New channel (1-16, or enter for current): ") or channel)
                gain = int(input("New gain (1,2,5,10,20,50,100, or enter): ") or gain)
                signal_path = int(input("New signal path (1-6, or enter): ") or signal_path)
                sample_rate = int(input("New sample rate (Hz, or enter): ") or sample_rate)
                trace_length = int(input("New trace length (or enter): ") or trace_length)
                to_timeout = int(input("New timeout (1-99 min, or enter): ") or to_timeout)
                
                # Resend new setup
                setup_commands = get_setup_commands(channel, gain, signal_path, sample_rate, trace_length, to_timeout)
                for cmd in setup_commands:
                    print(f"Sending new: {cmd}")
                    await send(writer, cmd)
                    resp = await receive(reader, timeout=timeout)
                    print(f"Response: {resp['response'] if resp['type'] == 'ascii' else resp}")
                    if 'NA' in resp.get('response', '') or 'ER' in resp.get('response', ''):
                        print(f"Warning: Error in new setup {cmd}")
                    await asyncio.sleep(0.5)
            elif user_input:
                # Send custom command
                print(f"Sending custom: {user_input}")
                await send(writer, user_input)
                custom_resp = await receive(reader, timeout=timeout)
                print(f"Custom response: {custom_resp['response'] if custom_resp['type'] == 'ascii' else custom_resp}")
            
            # Wait for next interval
            await asyncio.sleep(interval_seconds)
    
    except KeyboardInterrupt:
        print("Stopped by user.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await disconnect(writer)
        print("Disconnected.")

if __name__ == "__main__":
    asyncio.run(main_async())

# 192.168.13.10
# 10
# CH 1; GA 10; SP 1; SR 5120; TL 1024; TO 5

#8 rounds 
#24 Acquisition Commands (8*3)
#19 System Commands (8*2)+3
#15 Network Commands (8+7)