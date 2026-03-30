def parameters():
    CH_1         = int(input("Enter channel of x-axis (1-16): ") or 1)
    CH_2         = int(input("Enter channel of y-axis (1-16): ") or 1)
    CH_3         = int(input("Enter channel of z-axis (1-16): ") or 1)
    GA           = int(input("Enter gain : ") or 10)
    SP           = int(input("Enter signal path (1-6): ") or 1)
    SR           = int(input("Enter sample rate (HZ , e.g. 5120): ") or 5120)
    TO           = int(input("Enter timeout (1-99)min: ") or 10)
    TL           = int(input("Enter trace length (e.g. 1024): ") or 1024)
    commands = (
        #f"CH {CH_1};"
        f"GA {GA};"
        f"SP {SP};"
        f"SR {SR};"
        f"TO {TO};"
        f"TL {TL}"
    )
    first_channel  = f"CH {CH_1}"
    second_channel = f"CH {CH_2}"
    third_channel  = f"CH {CH_3}"
    return {
        'commands' : commands,
        'TL' :TL,
        'CH_1' : first_channel,
        'CH_2' : second_channel,
        'CH_3' : third_channel
    }

ind = 1
print(f"CH_{ind}")