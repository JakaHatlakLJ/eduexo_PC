from pylsl import StreamInfo, StreamOutlet
import time
import random

pos_tor = True                   # True for position and torque, False for torque profile and correctness

if not pos_tor:
    dir_corr = True
    channel_count = 3
else:
    channel_count = 2

if pos_tor:
    # Create a new stream info
    info1 = StreamInfo(
        'EXOInstructions',       # name
        'Instructions',          # type
        channel_count,                       # channel_count
        0,                       # nominal rate=0 for irregular streams
        'float32',                # channel format
        'Eduexo_PC'              # source_id
    )
    # info2 = StreamInfo('MyStream2', 'EEG_KD', 2, 100, 'float32', 'test_LSL2')

    # Create an outlet
    outlet1 = StreamOutlet(info1)
    # outlet2 = StreamOutlet(info2)

    print("Now sending data...")

    while True:
        p = input('pos (value between 0 - 10): ')
        t = input('tor (value between -4 - 4 [Nm]): ')

        if p:
            pos = p
        else:
            pos = 0

        if  t:
            tor = t
        else:
            tor = 0

        outlet1.push_sample([float(pos) / 10, float(tor)])
        # outlet2.push_sample([random.random()])

else:
    # Create a new stream info
    info1 = StreamInfo(
        'EXOInstructions',       # name
        'Instructions',          # type
        3,                       # channel_count
        0,                       # nominal rate=0 for irregular streams
        'float32',                # channel format
        'Eduexo_PC'              # source_id
    )
    # Create an outlet
    outlet1 = StreamOutlet(info1)

    print("Now sending data...")

    while True:
        torque_p = input('torque profile (value between 0 - 4): ')
        corr = input('correctness (0/1): ')
        direction = input('direction (10 : UP, 20 : DOWN): ')

        if torque_p:
            tor = torque_p
        else:
            tor = 1

        if corr:
            correctness = corr
        else:
            correctness = 1

        if  direction:
            dir = direction
        else:
            dir = 20

        DATA = [tor, correctness, dir]
        DATA = [int(i) for i in DATA]
        outlet1.push_sample(DATA)
        print(DATA)
        