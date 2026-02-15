def parameters(x=0):
    CH = int(input("Enter channel (1-16): ") or 1)
    GA = int(input("Enter gain : ") or 10)
    SP = int(input("Enter signal path (1-6): ") or 1)
    SR = int(input("Enter sample rate (HZ , e.g. 5120): ") or 5120)
    TO = int(input("Enter timeout (1-99)min: ") or 10)
    TL = int(input("Enter trace length (e.g. 1024): ") or 1024)
    commands = f"CH {CH};" f"GA {GA};" f"SP {SP};" f"SR {SR};" f"TO {TO};" f"TL {TL}"
    return {"commands": commands, "TL": TL}
