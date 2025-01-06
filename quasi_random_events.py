import random
import numpy as np


# import time
# random.seed(time.time())

trial_No = 20
time_delay = [1, 3]

ones = np.ones(int(trial_No/2))
zeros = np.zeros(int(trial_No/2))

events = np.append(ones, zeros)
random.shuffle(events)


for trial in events:
    if trial == 1:
        print("Trial: UP")
        while not input() == "q":
            pass
        else:
            print("Target Reached")
            while not input() == "a":
                pass
            else:
                print("Next Trial")
    else:
        print("Trial: DOWN")
        while not input() == "q":
            pass
        else:
            print("Target Reached")
            while not input() == "a":
                pass
            else:
                print("Next Trial")