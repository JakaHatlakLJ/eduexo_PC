import argparse
import json
import traceback
from datetime import datetime
from time import sleep, time

import numpy as np
import pygame
import os

from interf import Interfacee
from experiment_state_machine import StateMachinee




def initialize_state_dict(state_dict, experiment_config):
    if state_dict is None:
        state_dict = {}
        state_dict["state_wait_time"] = -1

    state_dict["Trials_No"] = experiment_config["Number_of_Trials"]
    state_dict["state_wait_time_range"] = experiment_config["state_wait_time_range"]
    state_dict["width"] = experiment_config["screen_width"]
    state_dict["height"] = experiment_config["screen_height"]
    state_dict["maxP"] = experiment_config["maximum_arm_position_deg"]
    state_dict["minP"] = experiment_config["minimum_arm_position_deg"]
    state_dict["total_trials"] = experiment_config["total_trials"]
    
    state_dict["experiment_start"] = -1
  
    state_dict["current_state"] = StateMachinee.INITIAL_SCREEN
    state_dict["eduexo_online"] = False

    state_dict["needs_update"] = False
    # state_dict["cbos_set"] = False
    
    return state_dict

if __name__ == "__main__":
    experiment_config = json.load(open("exper_conf.json", "r"))

    state_machine = StateMachinee()
    inlet = Interfacee.lsl_stream()

    continue_experiment = True
    state_dict = None

    try:
        while continue_experiment:
            if state_dict is None or state_dict["needs_update"]:
                state_dict = initialize_state_dict(state_dict, experiment_config)
                interface = Interfacee(inlet=inlet, width=state_dict["width"], height=state_dict["height"], maxP=state_dict["maxP"], minP=state_dict["minP"])
    
            time_start = time()
            pygame.event.get()


    
    
    
    
    
    
    
    except Exception as e:
        print(f"Error: {e}")
        print(traceback.format_exc())
        continue_experiment = False
            




