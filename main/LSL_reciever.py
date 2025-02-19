from pylsl import StreamInlet, resolve_stream
import time

sample_names = ['Position', 'Velocity', 'Torque']

# Resolve a stream
streams = resolve_stream('type', 'EXO')

# Create an inlet
inlet = StreamInlet(streams[0])  

print("Receiving data...")
while True:
    sample, timestamp = inlet.pull_sample()
    sample_round = list(zip(sample_names, [round(num, 2) for num in sample]))
    sample_formated = "\t".join([f"{name}: {value:<{8}}" for name, value in sample_round])
    print(f"{sample_formated} Timestamp: {timestamp}")
  
