import random
import numpy as np
import time

# random.seed(time.time())

trial_No = 20

ones = np.ones(int(trial_No/2))
zeros = np.zeros(int(trial_No/2))

events = np.append(ones, zeros)
random.shuffle(events)
print(events)

