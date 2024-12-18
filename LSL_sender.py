from pylsl import StreamInfo, StreamOutlet
import time
import random

# Create a new stream info
info1 = StreamInfo('MyStream1', 'EEG', 2, 100, 'float32', 'test_LSL1')
info2 = StreamInfo('MyStream2', 'EEG_KD', 2, 100, 'float32', 'test_LSL2')

# Create an outlet
outlet1 = StreamOutlet(info1)
outlet2 = StreamOutlet(info2)

print("Now sending data...")
while True:
    p = input('pos (value between 0 - 1): ')
    t = input('tor (value between 0 - 0.2 [Nm]): ')

    if p:
        pos = p
    else:
        pos = 0

    if  t:
        tor = t
    else:
        tor = 0

    outlet1.push_sample([float(pos), float(tor)])
    outlet2.push_sample([random.random()])
