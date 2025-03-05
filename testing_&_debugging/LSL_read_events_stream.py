from pylsl import StreamInlet, resolve_stream
import datetime
import time

stream_info = resolve_stream('type', 'Events')
inlet = StreamInlet(stream_info[0])

cont = True

while cont == True:
    sample, _ = inlet.pull_sample(timeout=0.1)
    if sample is not None:
        # system_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        predict = sample[0]
    else:
        predict = None
    print(predict)

