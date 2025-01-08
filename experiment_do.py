import json
import traceback
from datetime import datetime
from time import sleep, time
from pylsl import StreamInlet, resolve_stream

import numpy as np
import pygame
import os

from experiment_interface import Interface
from experiment_state_machine import StateMachine

def initialize_state_dict(state_dict, experiment_config):
    if state_dict is None:
        state_dict = {}
        state_dict["state_wait_time"] = -1

    state_dict["Trials_No"] = experiment_config["experiment"]["number_of_trials"]
    state_dict["state_wait_time_range"] = experiment_config["experiment"]["state_wait_time_range"]
    state_dict["timeout"] = experiment_config["experiment"]["trial_timeout"]
    state_dict["width"] = experiment_config["experiment"]["screen_width"]
    state_dict["height"] = experiment_config["experiment"]["screen_height"]
    state_dict["maxP"] = experiment_config["experiment"]["maximum_arm_position_deg"]
    state_dict["minP"] = experiment_config["experiment"]["minimum_arm_position_deg"]
    state_dict["total_trials"] = experiment_config["experiment"]["total_trials"]
    
    state_dict["experiment_start"] = -1
  
    state_dict["current_state"] = StateMachine.INITIAL_SCREEN
    state_dict["eduexo_online"] = False
    state_dict["enter_pressed"] = False
    state_dict["space_pressed"] = False
    state_dict["previous_enter_state"] = False
    state_dict["previous_space_state"] = False

    state_dict["background_color"] = "black"

    state_dict["needs_update"] = False
    # state_dict["cbos_set"] = False
    
    return state_dict

if __name__ == "__main__":
    experiment_config = json.load(open("experiment_conf.json", "r"))
    
    inlet = Interface.lsl_stream()

    continue_experiment = True
    experiment_over = False
    state_dict = None

    try:
        while continue_experiment and experiment_over is False:
            if state_dict is None or state_dict["needs_update"]:
                state_dict = initialize_state_dict(state_dict, experiment_config)
                if inlet is not None:
                    state_dict["eduexo_online"] = True
                interface = Interface(inlet=inlet, state_dict=state_dict, width=state_dict["width"], height=state_dict["height"], maxP=state_dict["maxP"], minP=state_dict["minP"])
                state_machine = StateMachine(trial_No=state_dict["Trials_No"], time_delay=state_dict["state_wait_time_range"])

            time_start = time()
            pygame.event.clear()

            experiment_over, state_dict = state_machine.maybe_update_state(state_dict)

            continue_experiment = Interface.run(interface)
            # print(state_dict)
    
    
    except Exception as e:
        print(f"Error: {e}")
        print(traceback.format_exc())
        continue_experiment = False
            




