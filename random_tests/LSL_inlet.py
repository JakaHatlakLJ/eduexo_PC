from pylsl import resolve_byprop, StreamInlet
from time import sleep

streams = resolve_byprop('type', 'EXO', timeout=5)
if not streams:
    raise RuntimeError(f"No LSL stream found of type: 'EXO'")
inlet = StreamInlet(streams[0])

while True:
    inlet.flush()
    sample, timestamp = inlet.pull_sample()
    if sample is not None:
        print(sample)
        sleep(0.2)