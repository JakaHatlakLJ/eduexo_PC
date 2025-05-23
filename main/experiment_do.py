import json
import pygame
import threading
import logging
import argparse

from experiment_interface import Interface
from experiment_state_machine import StateMachine
from experiment_logging import Logger
from experiment_LSL import LSLHandler

def initialize_state_dict(state_dict, experiment_config):
    """
    Read JSON configuration file and create state_dict for saving current program parameters
    """
    if state_dict is None:
        state_dict = {}
        state_dict["state_wait_time"] = -1

    # Initialize state_dict with values from experiment_config
    state_dict["trials_No"] = experiment_config["experiment"]["number_of_trials"]
    state_dict["control_trials_No"] = experiment_config["experiment"]["number_of_control_trials"]
    state_dict["trial_states"] = experiment_config["experiment"]["define_trial_states"]
    state_dict["state_wait_time_range"] = experiment_config["experiment"]["state_wait_time_range"]
    state_dict["imagination_time_range"] = experiment_config["experiment"]["imagination_time_range"]
    state_dict["intention_time_range"] = experiment_config["experiment"]["intention_time_range"]
    state_dict["timeout"] = state_dict["TO"] = experiment_config["experiment"]["trial_timeout"]
    state_dict["fullscreen"] = experiment_config["experiment"]["full_screen_mode"]
    state_dict["data_stream_interval"] = experiment_config["experiment"]["data_stream_interval"]
    state_dict["torque_profiles"] = experiment_config["experiment"]["torque_profiles"]
    state_dict["synthetic_decoder"] = True if experiment_config["experiment"]["synthetic_decoder"] == 1 else False
    state_dict["correct_percantage"] = experiment_config["experiment"]["synthetic_decoder_correct_percantage"]

    state_dict["exo_parameters"] = experiment_config["exo_parameters"]

    state_dict["enter_pressed"] = False
    state_dict["escape_pressed"] = False
    state_dict["space_pressed"] = False
    state_dict["stream_online"] = True
    state_dict["current_state"] = None
    state_dict["torque_profile"] = None
    
    prediction_stream = False
    if not state_dict["synthetic_decoder"]:
        state_dict["prediction"] = None
        prediction_stream = True

    state_dict["trial"] = ""
    state_dict["event_id"] = 99
    state_dict["event_type"] = ""
    state_dict["current_trial_No"] = 0
    state_dict["remaining_time"] = ""
    state_dict["avg_time"] = None

    state_dict["current_position"] = 0
    state_dict["current_velocity"] = 0
    state_dict["current_torque"] = 0

    # state_dict["needs_update"] = False # This is not used in the current version, if needed, uncomment the lines in the main loop and signal the update
    state_dict["activate_EXO"] = False

    state_dict["background_color"] = "black"
    state_dict["color"] = "white"
    
    return state_dict, prediction_stream

if __name__ == "__main__":

    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--no_log", action="store_true", help="Disable logging")
    args = parser.parse_args()

    # Load experiment configuration from JSON file
    experiment_config = json.load(open(r"main\experiment_config.json", "r"))
    
    # Setup logger
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("Main")

    # Setup results logging
    save_data = True if experiment_config["experiment"]["save_data"] == 1 else False
    data_log = Logger(
        experiment_config["experiment"]["results_path"],    # results path
        experiment_config["experiment"]["frequency_path"],  # frequency path
        experiment_config["participant"]["id"],             # participant ID
        args.no_log,                                        # disable logging
        save_data                                           # save data
    )
    data_log.save_experiment_config(experiment_config)

    # Initialize experiment state
    state_dict = None
    state_dict, predict = initialize_state_dict(state_dict, experiment_config)

    # Create an Inlet for incoming LSL Stream
    LSL = LSLHandler(state_dict, predict=predict)
    interface = Interface(
        state_dict  =   state_dict,
        maxP        =   state_dict["exo_parameters"]["maximum_arm_position_deg"],
        minP        =   state_dict["exo_parameters"]["minimum_arm_position_deg"]
    )
    state_machine = StateMachine(LSL, trial_No=state_dict["trials_No"], control_trial_No=state_dict["control_trials_No"], correct_percentage=state_dict["correct_percantage"])

    # Create a background thread for sending Data through LSL Stream
    stop_event = threading.Event()
    the_lock = threading.Lock()
    streamer_thread = threading.Thread(
        target=LSL.stream_events_data,
        args=(stop_event, state_dict, the_lock),
        daemon=True
    )
    streamer_thread.start()
    if not state_dict["synthetic_decoder"]:
        prediction_thread = threading.Thread(
            target=LSL.get_predictions,
            args=(stop_event, state_dict, True),
            daemon=True
        )
        prediction_thread.start()
    continue_experiment = True
    experiment_over = False

    try:
        while continue_experiment and experiment_over is False:
            # if state_dict["needs_update"]:
            #     # Reinitialize state_dict and interface if update is needed
            #     state_dict = initialize_state_dict(state_dict, experiment_config)
            #     interface = Interface(inlet=LSL.inlet, state_dict=state_dict, maxP=state_dict["exo_parameters"]["maximum_arm_position_deg"], minP=state_dict["exo_parameters"]["minimum_arm_position_deg"])
            #     state_machine = StateMachine(LSL, trial_No=state_dict["trials_No"], control_trial_No=state_dict["control_trials_No"], correct_percentage=state_dict["correct_percantage"])

            pygame.event.clear()
            with the_lock:
                state_dict["timestamp"] = LSL.timestamp_g

            # Stream data and update state
            LSL.EXO_stream_in(state_dict)
            experiment_over, state_dict = state_machine.maybe_update_state(state_dict)
            continue_experiment = Interface.run(interface, state_dict)
            
            if "previous_state" not in state_dict:
                state_dict["previous_state"] = None
            if "event_type" not in state_dict:
                state_dict["event_type"] = None                     

            # Save data and log frequency
            data_log.save_data_dict(state_dict)
            data_log.frequency_log(state_dict)

    except Exception as e:
        logger.error(f"An error occurred during the experiment loop: {e}", exc_info=True)
    
    except KeyboardInterrupt:
        stop_event.set()
        continue_experiment = False

    finally:
        data_log.close()
