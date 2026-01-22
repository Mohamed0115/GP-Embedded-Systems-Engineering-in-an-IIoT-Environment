import asyncio
import struct

async def receive(reader, command='', timeout=30):
    """
    Asynchronously receive response from ITA-110.
    Handles ASCII or binary based on command.
    Returns dict with 'type' and 'response' or parsed data.
    """
    data = b''
    try:
        while True:
            chunk = await asyncio.wait_for(reader.read(4096), timeout=timeout)
            if not chunk:
                raise ConnectionError("Connection closed")
            data += chunk
            if command.endswith('?') and (command in ['BD?', 'BH?']):
                # Binary - break after initial read, parse will handle more
                if len(data) >= 3:  # Enough for prefix
                    break
            if b'\r' in data:
                break
    except asyncio.TimeoutError:
        raise ValueError("Receive timeout - device may be slow, parameters invalid, or waiting for input/trigger")

    if command in ['BD?', 'BH?']:
        prefix = command[:-1].encode() + b'='  # e.g., b'BD='
        if not data.startswith(prefix):
            # Try to decode as ASCII error
            try:
                ascii_resp = data.decode('ascii').strip()
                return {'type': 'ascii', 'response': ascii_resp}
            except UnicodeDecodeError:
                raise ValueError(f"Invalid response for {command} - not binary or ASCII")
        
        header_start = len(prefix)
        header_end = header_start + 13  # Corrected to 13 bytes
        header = data[header_start:header_end]
        if len(header) < 13:
            while len(header) < 13:
                chunk = await asyncio.wait_for(reader.read(4096), timeout=timeout)
                if not chunk:
                    raise ConnectionError("Incomplete header")
                data += chunk
                header = data[header_start:header_end]
        
        # Corrected unpack: status(B), range(B), schema(B), channel(B), format(B), trace_length(I unsigned), running_speed(f float)
        status, range_val, schema, channel, format_val, trace_length, running_speed = struct.unpack('>BBBBBIf', header)
        if schema != 2 or format_val != 4:
            raise ValueError("Invalid schema or format")
        
        sample_size = 4
        data_len = trace_length * sample_size if command == 'BD?' else 0
        binary_start = header_end
        binary_data = data[binary_start : binary_start + data_len]
        if len(binary_data) < data_len:
            while len(binary_data) < data_len:
                chunk = await asyncio.wait_for(reader.read(4096), timeout=timeout)
                if not chunk:
                    raise ConnectionError("Incomplete binary data")
                binary_data += chunk
        
        samples = [struct.unpack('>i', binary_data[i:i+4])[0] for i in range(0, len(binary_data), 4)]
        
        return {
            'type': 'binary',
            'status': status,
            'range': range_val,
            'channel': channel,
            'trace_length': trace_length,
            'running_speed': running_speed,
            'data': samples
        }
    else:
        try:
            response = data.decode('ascii').strip()
        except UnicodeDecodeError:
            raise ValueError("Decode error - possibly binary data in ASCII mode")
        return {'type': 'ascii', 'response': response}