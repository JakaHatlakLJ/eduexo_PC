from pylsl import StreamInlet, resolve_stream
import time
import signal

sample_names = ['Position', 'Velocity', 'Torque']

# Register an handler for the timeout
def handler(signum, frame):
     print("Forever is over!")
     raise Exception("end of time")

signal.signal(signal.SIGALRM, handler)

# Define a timeout for your function
signal.alarm(10)

# Resolve a stream
try:
    streams = resolve_stream('type', 'EXO')
except Exception as e:
     print(e)

# Create an inlet
inlet = StreamInlet(streams[0])  

print("Receiving data...")
while True:
    sample, timestamp = inlet.pull_sample()
    sample_round = list(zip(sample_names, [round(num, 2) for num in sample]))
    sample_formated = "\t".join([f"{name}: {value:<{8}}" for name, value in sample_round])
    print(f"{sample_formated} Timestamp: {timestamp}")
  



