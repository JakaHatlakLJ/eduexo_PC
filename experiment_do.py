import json
import traceback
from time import time, sleep
import pygame
from pylsl import StreamInfo, StreamOutlet, local_clock
import threading
import logging

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
    state_dict["event_stream_interval"] = experiment_config["experiment"]["event_stream_interval"]
    
    state_dict["experiment_start"] = -1

    state_dict["enter_pressed"] = False
    state_dict["escape_pressed"] = False
    state_dict["space_pressed"] = False
    
    state_dict["stream_online"] = True

    state_dict["event_id"] = None
    state_dict["current_trial"] = None
    state_dict["current_trial_No"] = 0
    state_dict["remaining_time"] = ""


    state_dict["current_position"] = 0
    state_dict["current_velocity"] = 0
    state_dict["current_torque"] = 0

    state_dict["needs_update"] = False

    state_dict["background_color"] = "black"
     
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
    event_interval = state_dict["event_stream_interval"]   # how often we send an 'event'
    sleep_interval = 0.01    # how often we send 'data' samples
    elapsed_time = 0.0

    while not stop_event.is_set():
        try:
            # 1) Stream position/torque (data) on every loop
            timestamp = local_clock()
            position = state_dict["current_position"]  # current position
            velocity = state_dict["current_velocity"]  # current torque
            torque   = state_dict["current_torque"]   # current torque
            data_sample = {
                'Sample_Type': 'data',
                'Position': position,
                'Velocity': velocity,
                'Torque': torque,
                'Timestamp': timestamp
            }
            data_json_str = json.dumps(data_sample)
            outlet.push_sample([data_json_str], timestamp=timestamp)

            # Sleep before checking if it’s time for an event
            sleep(sleep_interval)
            elapsed_time += sleep_interval

            # 2) Send an event once every event_interval seconds
            if elapsed_time >= event_interval:
                event_id = state_dict["event_id"]
                event_type = state_dict["current_trial"]
                event_timestamp = local_clock()
                event_data = {
                    'Sample_Type': 'event',
                    'Event_ID': event_id,
                    'Event_Type': event_type,
                    'Event_Timestamp': event_timestamp,
                    'test_expansion': 10
                }
                event_json_str = json.dumps(event_data)
                outlet.push_sample([event_json_str], timestamp=event_timestamp)

                elapsed_time = 0.0

        except Exception as e:
            logger.error(f"Error in streaming Events data: {e}")
            break

    logger.info("Stopped streaming Events data.")

if __name__ == "__main__":

    # Setup logger
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("LSL")

    # Setup JSON file
    experiment_config = json.load(open("experiment_conf.json", "r"))
    
    # Create an Inlet for incoming LSL Stream
    inlet = Interface.lsl_stream()

    continue_experiment = True
    experiment_over = False
    state_dict = None

    # Initialize experiment
    state_dict = initialize_state_dict(state_dict, experiment_config)
    interface = Interface(inlet=inlet, state_dict=state_dict, width=state_dict["width"], height=state_dict["height"], maxP=state_dict["maxP"], minP=state_dict["minP"])
    state_machine = StateMachine(trial_No=state_dict["Trials_No"])

    # Create a background thread for sending Data through LSL Stream
    stop_event = threading.Event()
    streamer_thread = threading.Thread(
        target=stream_events_data,
        args=(stop_event, state_dict, logger),
        daemon=True
    )
    streamer_thread.start()

    try:
        while continue_experiment and experiment_over is False:
            # if state_dict["needs_update"]:
            #     state_dict = initialize_state_dict(state_dict, experiment_config)
            #     interface = Interface(inlet=inlet, state_dict=state_dict, width=state_dict["width"], height=state_dict["height"], maxP=state_dict["maxP"], minP=state_dict["minP"])
            #     state_machine = StateMachine(trial_No=state_dict["Trials_No"], time_delay=state_dict["state_wait_time_range"])

            # time_start = time()
            pygame.event.clear()

            experiment_over, state_dict = state_machine.maybe_update_state(state_dict)
            continue_experiment = Interface.run(interface)
            
            if "previous_state" not in state_dict:
                state_dict["previous_state"] = None
            if "current_trial" not in state_dict:
                state_dict["current_trial"] = None                     

            logger.info(f'Current state: {state_dict["current_state"]}, Remaining time: {state_dict["remaining_time"]}, Current trial No: {state_dict["current_trial_No"]}, Event ID : {state_dict["event_id"]}, Current trial: {state_dict["current_trial"]}, enter_pressed: {state_dict["enter_pressed"]}, space_pressed: {state_dict["space_pressed"]}, escape pressed: {state_dict["escape_pressed"]}')
    
    
    except Exception as e:
        logger.error(f"An error occurred during the experiment loop: {e}", exc_info=True)
        stop_event.set()
        continue_experiment = False 

            




