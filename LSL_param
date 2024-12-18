from pylsl import StreamInfo, StreamOutlet
import random

# Create a new stream info
info = StreamInfo('MyStream1', 'EEG', 2, 100, 'float32', 'test_LSL1')

# Create an outlet
outlet = StreamOutlet(info)

print("Now sending data...")
while True:
    K = input('Enter desired Stiffnes [N/m]')
    D = input('Enter desired Damping [Ns/m]')
    outlet.push_sample([float(K), float(D)])
    
