import asyncio
import struct
from parameters_con import parameters

async def connect(ip,port ):  #try if there is no exception
    reader , writer = await asyncio.open_connection(ip,port)
    return reader , writer

async def disconnect(writer):
    if writer:
        writer.close()
        await writer.wait_closed()

async def send(writer , command):
    full = command + '\r'
    writer.write(full.encode('ascii'))
    await writer.drain()

async def receive_normal(reader):
    data = b""
    timeout = 2
    while True:
        try:
            chunk = await asyncio.wait_for(reader.readuntil(b"\r"), timeout)
            if not chunk:
                break
            data += chunk 
        except asyncio.TimeoutError:
            break
        except Exception as e:
            raise UnicodeDecodeError(e)
        
    text = data.decode("ascii")
    messages = text.split("\r")  # split by carriage return
    messages = [m for m in messages if m]  # remove empty strings
    return {'response' : messages}


async def receive_data(reader,command,TL):

    data =b''
    sample_size = 4
    data_len = TL * sample_size if command == 'BD?' else 0
    data_len += 16
        
    try :
        while True:
            # Text errors typically have 'ER' or 'NA' in the first few bytes. 
            # If so, exit the wait loop early instead of blocking.
            if b'ER' in data[:20] or b'NA' in data[:20]:
                break
            ##heere i added a new part    i added 0 to 9000 to 90000
            chunk = await asyncio.wait_for( reader.read(90000) ,timeout= 3.0)
            if not chunk:
                break
            data +=chunk
            
            if len(data) >= data_len:
                break
    except asyncio.TimeoutError:
        if len(data) == 0:
            raise ValueError("Receive timeout")
    except Exception as e:
        raise UnicodeDecodeError(e)
        
    
    
    prefix = command[0:2].encode()+b'='
    if data.startswith(prefix):
        header = data[3:16]
        binary_data = data[16:data_len-16]
        status, range_val, schema, channel, format_val, trace_length, running_speed = struct.unpack('>BBBBBIf', header)
        samples = [struct.unpack('>i', binary_data[i:i+4])[0] for i in range(0, len(binary_data), 4)]
        return {
            
            'response' : samples,
            'status' : status,
            'range_val ' : range_val,
            'schema ' : schema,
            'runnig_speed ' : running_speed

        }
    else:
        response = data.decode("ascii").strip()
        return {'response' : response}    
            
        
# steam -  turbine - fan - agetator (mixer) - gnariwator (mixer) <vibration [rotating]>
#portal
#ods