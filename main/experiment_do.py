import json
from time import perf_counter
import pygame
from pylsl import StreamInfo, StreamOutlet, local_clock
import threading
import logging
import os

import argparse
from experiment_interface import Interface
from experiment_state_machine import StateMachine
from experiment_logging import Logger

def initialize_state_dict(state_dict, experiment_config):
    """
    Read JSON configuration file and create state_dict for saving current program parameters
    """
    if state_dict is None:
        state_dict = {}
        state_dict["state_wait_time"] = -1

    state_dict["Trials_No"] = experiment_config["experiment"]["number_of_trials"]
    state_dict["state_wait_time_range"] = experiment_config["experiment"]["state_wait_time_range"]
    state_dict["timeout"] = state_dict["TO"] = experiment_config["experiment"]["trial_timeout"]
    state_dict["width"] = experiment_config["experiment"]["screen_width"]
    state_dict["height"] = experiment_config["experiment"]["screen_height"]
    state_dict["maxP"] = experiment_config["experiment"]["maximum_arm_position_deg"]
    state_dict["minP"] = experiment_config["experiment"]["minimum_arm_position_deg"]
    state_dict["data_stream_interval"] = experiment_config["experiment"]["data_stream_interval"]
    state_dict["imagination_time"] = experiment_config["experiment"]["imagination_time"]
    state_dict["intention_time"] = experiment_config["experiment"]["intention_time"]

    state_dict["experiment_start"] = -1

    state_dict["enter_pressed"] = False
    state_dict["escape_pressed"] = False
    state_dict["space_pressed"] = False
    
    state_dict["stream_online"] = True

    state_dict["trial"] = ""
    state_dict["event_id"] = 99
    state_dict["event_type"] = ""
    state_dict["current_trial_No"] = 0
    state_dict["remaining_time"] = ""
    state_dict["avg_time"] = None

    state_dict["current_position"] = 0
    state_dict["current_velocity"] = 0
    state_dict["current_torque"] = 0

    state_dict["needs_update"] = False

    state_dict["background_color"] = "black"
    state_dict["color"] = "white"
     
    return state_dict

def stream_events_data(stop_event, state_dict, logger):
    """
    Continuously stream position/torque data (0.1s interval)
    and send an 'event' every 10s using one LSL Outlet.
    """
    # Create LSL stream with the same metadata
    info = StreamInfo(
        'SyntheticEvents',       # name
        'Events',                # type
        1,                       # channel_count
        0,                       # nominal rate=0 for irregular streams
        'string',                # channel format
        'synthetic_events_id'    # source_id
    )
    outlet = StreamOutlet(info)
    logger.info("Stream is online...")

    # Configuration
    data_interval = state_dict["data_stream_interval"]          # how often we send 'data' samples
    last_data_time = perf_counter()
    old_event = 99

    while not stop_event.is_set():
        try:
            # 1) Stream position/torque (data) on every loop
            current_time = perf_counter()
            timestamp = local_clock()
            global timestamp_g
            with the_lock:
                timestamp_g = timestamp
            if current_time - last_data_time >= data_interval:
                position = state_dict["current_position"]   # current position
                velocity = state_dict["current_velocity"]   # current torque
                torque   = state_dict["current_torque"]     # current torque
                data_sample = {
                    'Sample_Type': 'data',
                    'Position': position,
                    'Velocity': velocity,
                    'Torque': torque,
                    'Timestamp': timestamp
                }
                data_json_str = json.dumps(data_sample)
                outlet.push_sample([data_json_str], timestamp=timestamp)
                # print(data_json_str)

                last_data_time = current_time

            # 2) Send an event once every time new event happens
            if old_event != state_dict["event_id"] and not state_dict["event_id"] == 99:
                event_id = state_dict["event_id"]
                event_type = state_dict["event_type"]
                event_data = {
                    'Sample_Type': 'event',
                    'Event_ID': event_id,
                    'Event_Type': event_type,
                    'Event_Timestamp': timestamp,
                }
                event_json_str = json.dumps(event_data)
                outlet.push_sample([event_json_str], timestamp=timestamp)
                print(event_json_str)
                old_event = state_dict["event_id"]

        except Exception as e:
            logger.error(f"Error in streaming Events data: {e}")
            break

    logger.info("Stopped streaming Events data.")

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--no_log", action="store_true", help="Disable logging")
    args = parser.parse_args()

    # Setup JSON file
    experiment_config = json.load(open(r"main\experiment_config.json", "r"))
    
    # Setup logger
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("LSL")

    # Setup results logging
    save_data = True if experiment_config["experiment"]["save_data"] == 1 else False
    data_log = Logger(experiment_config["experiment"]["results_path"], experiment_config["experiment"]["frequency_path"], experiment_config["participant"]["id"], no_log=args.no_log, save_data=save_data)
    data_log.save_experiment_config(experiment_config)

    # Create an Inlet for incoming LSL Stream
    inlet = Interface.lsl_stream()

    # Initialize experiment
    state_dict = None
    state_dict = initialize_state_dict(state_dict, experiment_config)
    interface = Interface(inlet=inlet, state_dict=state_dict, width=state_dict["width"], height=state_dict["height"], maxP=state_dict["maxP"], minP=state_dict["minP"])
    state_machine = StateMachine(trial_No=state_dict["Trials_No"])

    # Create a background thread for sending Data through LSL Stream
    stop_event = threading.Event()
    the_lock = threading.Lock()
    streamer_thread = threading.Thread(
        target=stream_events_data,
        args=(stop_event, state_dict, logger),
        daemon=True
    )
    streamer_thread.start()
    
    continue_experiment = True
    experiment_over = False
    timestamp_g = local_clock()


    try:
        while continue_experiment and experiment_over is False:
            if state_dict["needs_update"]:
                state_dict = initialize_state_dict(state_dict, experiment_config)
                interface = Interface(inlet=inlet, state_dict=state_dict, width=state_dict["width"], height=state_dict["height"], maxP=state_dict["maxP"], minP=state_dict["minP"])
                state_machine = StateMachine(trial_No=state_dict["Trials_No"])

            # time_start = time()
            pygame.event.clear()
            with the_lock:
                state_dict["timestamp"] = timestamp_g

            experiment_over, state_dict= state_machine.maybe_update_state(state_dict)
            continue_experiment = Interface.run(interface)
            
            if "previous_state" not in state_dict:
                state_dict["previous_state"] = None
            if "event_type" not in state_dict:
                state_dict["event_type"] = None                     

            data_log.save_data_dict(state_dict)
            data_log.frequency_log(state_dict)

            # logger.info(f'Current state: {state_dict["current_state"]}, Trial : {state_dict["trial"]}, Event ID : {state_dict["event_id"]}, Event type: {state_dict["event_type"]}, trial in progress : {state_dict["trial_in_progress"]}')
    
    except Exception as e:
        logger.error(f"An error occurred during the experiment loop: {e}", exc_info=True)
    
    except KeyboardInterrupt:
        stop_event.set()
        continue_experiment = False

    finally:
        data_log.close() 