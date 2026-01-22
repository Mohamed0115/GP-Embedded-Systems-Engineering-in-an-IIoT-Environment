async def send(writer, command):
    """
    Asynchronously send a command to the ITA-110.
    Appends \r and encodes as ASCII.
    """
    full_command = command + '\r'
    writer.write(full_command.encode('ascii'))
    await writer.drain()