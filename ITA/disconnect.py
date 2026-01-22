async def disconnect(writer):
    """
    Asynchronously disconnect from the ITA-110 device.
    """
    if writer:
        writer.close()
        await writer.wait_closed()