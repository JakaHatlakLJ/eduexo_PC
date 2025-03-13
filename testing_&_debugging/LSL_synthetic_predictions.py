from pylsl import StreamInfo, StreamOutlet, local_clock
import json
import random
from time import sleep 
info = StreamInfo("PredictionStream", "",1, 0,"string")
outlet = StreamOutlet(info)
data_sample = {"classifier_name": "ClassifierName", "timestamp": "2025-03-13 12:23:07", "predicted_event_name": "bbbb", "true_event_name": "bbbb", "event_type": "bbbb"}
while True:
    input("Press enter to send a prediction sample")
    data_sample["timestamp"] = local_clock()
    data_sample["true_event_name"] = random.choice([0,1])
    data_sample["predicted_event_name"] = random.choice(["UP","DOWN"])
    data_sample["event_type"] = random.choice([0,1,2,3,4])
    data_json = json.dumps(data_sample)
    outlet.push_sample([data_json], timestamp=local_clock())
    print(data_json)
