from pylsl import StreamInfo, StreamOutlet
import random

default_S = 0.07
default_D = 0.006

# Create a new stream info
info = StreamInfo('Parameters', 'params', 2, 100, 'float32', 'test_LSL1')

# Create an outlet
outlet = StreamOutlet(info)

print("Now sending data...")
while True:
    K = input('Enter desired Stiffnes [N/m] (default 0.07):')
    if not K:
        K = default_S
    D = input('Enter desired Damping [Ns/m] (default 0.06):')
    if not D:
        D = default_D
    outlet.push_sample([float(K), float(D)])
    
