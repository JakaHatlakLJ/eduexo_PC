from pylsl import StreamInfo, StreamOutlet, local_clock, resolve_byprop, StreamInlet
from time import perf_counter
import threading
import json
import logging

class LSLHandler:

    def __init__(self, receive: bool=True, send: bool=True, predict: bool=False):
        """
        Initialize the LSLHandler class.

        :param receive: Flag to enable receiving data from LSL stream.
        :param send: Flag to enable sending data to LSL stream.
        :param predict: Flag to enable receiving predictions from LSL stream.
        """
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("LSL")
        self.logger = logger
        self.logger_predictions = logging.getLogger("Predictions")
        self.timestamp_g = local_clock()

        if send:
            # Create LSL stream for sending instructions to EXO
            info_EXO = StreamInfo(
                'EXOInstructions',       # name
                'Instructions',          # type
                3,                       # channel_count
                0,                       # nominal rate=0 for irregular streams
                'float32',               # channel format
                'Eduexo_PC'              # source_id
            )
            self.outlet_EXO = StreamOutlet(info_EXO)
            logger.info("Stream to EXO is online...")

            # Create LSL stream for sending events and motor data to classifier
            info_class = StreamInfo(
                'SyntheticEvents',       # name
                'Events',                # type
                1,                       # channel_count
                0,                       # nominal rate=0 for irregular streams
                'string',                # channel format
                'Eduexo_PC'              # source_id
            )
            self.outlet_classifier = StreamOutlet(info_class)
            logger.info("Stream for events is online...")
        
        if receive:
            # Resolve LSL stream for receiving EXO data and create an inlet
            logger.info("Looking for LSL stream of type: 'EXO'...")
            while True:
                streams = resolve_byprop('type', 'EXO', timeout=5)
                if streams:
                    break
                logger.warning("No LSL stream found of type: 'EXO'. Retrying...")
            self.inlet = StreamInlet(streams[0])
            logger.info("Receiving data from EXO...")

        if predict:
            # Resolve "PredictionStream" for receiving decoded events
            logger.info("Looking for LSL stream of name: 'PredictionStream'...")
            while True:
                streams_p = resolve_byprop('name', 'PredictionStream', timeout=5)
                if streams_p:
                    break
                logger.warning("No LSL stream found of name: 'PredictionStream'. Retrying...")
            self.predictions_inlet = StreamInlet(streams_p[0])
            logger.info("Receiving data from EXO...")

    def stream_events_data(self, stop_event: threading.Event, state_dict: dict, the_lock: threading.Lock):
        """
        Continuously stream position/torque data (0.1s interval)
        and send an 'event' every 10s using one LSL Outlet.

        :param stop_event: Event to signal stopping the streaming.
        :param state_dict: Dictionary containing the current state information.
        :param the_lock: Lock to synchronize access to shared resources.
        """
        # Configuration
        data_interval = state_dict["data_stream_interval"]  # how often we send 'data' samples
        last_data_time = perf_counter()
        old_event = 99
        self.timestamp_g = local_clock()

        while not stop_event.is_set():
            try:
                # 1) Stream position/torque (data) on every loop
                current_time = perf_counter()
                self.timestamp = local_clock()
                with the_lock:
                    self.timestamp_g = self.timestamp
                if current_time - last_data_time >= data_interval:
                    position = state_dict["current_position"]   # current position
                    velocity = state_dict["current_velocity"]   # current velocity
                    torque = state_dict["current_torque"]       # current torque
                    data_sample = {
                        'Sample_Type': 'data',
                        'Position': position,
                        'Velocity': velocity,
                        'Torque': torque,
                        'Timestamp': self.timestamp
                    }
                    data_json_str = json.dumps(data_sample)
                    self.outlet_classifier.push_sample([data_json_str], timestamp=self.timestamp)
                    # self.logger.info(data_json_str)

                    last_data_time = current_time

                # 2) Send an event once every time new event happens
                if old_event != state_dict["event_id"] and not state_dict["event_id"] == 99:
                    event_id = state_dict["event_id"]
                    event_type = state_dict["event_type"]
                    torque_profile = state_dict["torque_profile"]
                    event_data = {
                        'Sample_Type': 'event',
                        'Event_ID': event_id,
                        'Event_Type': event_type,
                        'TorqueProfile': torque_profile,
                        'Event_Timestamp': self.timestamp
                    }
                    event_json_str = json.dumps(event_data)
                    self.outlet_classifier.push_sample([event_json_str], timestamp=self.timestamp)
                    self.logger.info(event_json_str)
                    old_event = state_dict["event_id"]

            except Exception as e:
                self.logger.error(f"Error in streaming Events data: {e}")
                break

        self.logger.info("Stopped streaming Events data.")

    def EXO_stream_in(self, state_dict: dict):
        """
        Receive data from EXO and update the state dictionary.

        :param state_dict: Dictionary containing the current state information.
        """
        # Receive data from EXO
        self.inlet.flush()  
        sample, timestamp = self.inlet.pull_sample(timeout=3)
        
        if sample is None:
            try:
                info = self.inlet.info(timeout=0.1)  # May timeout if stream is lost
                if info is None:
                    raise TimeoutError  # Force handling below
            except TimeoutError:
                self.logger.error("Stream lost!")
                state_dict["current_position"] = None
                state_dict["stream_online"] = False
            except Exception as e:
                self.logger.error(f"Unexpected error checking stream info: {e}")
                state_dict["stream_online"] = False  # Assume lost on unexpected error
        else:
            state_dict["stream_online"] = True
            state_dict["current_position"] = round(sample[0], 5)
            state_dict["current_velocity"] = round(sample[1], 5)
            state_dict["current_torque"] = round(sample[2], 5)
            state_dict["exo_execution"] = sample[3]

    def EXO_stream_out(self, state_dict: dict, torque_profile: int, correctness: int = None):
        """
        Send a TorqueProfile, direction, and Correctness once every time a new event happens.
        
        :param state_dict: Dictionary containing the current state information.
        :param torque_profile: Torque profile to be sent.
        :param correctness: Correctness of the execution.
        """
        if state_dict["synthetic_decoder"]:
            # Determine direction based on trial type and correctness
            if state_dict["trial"] == "UP":
                if correctness == 1:
                    direction = 10
                else:
                    direction = 20
            else:
                if correctness == 1:
                    direction = 20
                else:
                    direction = 10
        else:
            if state_dict["prediction"] == "UP":
                direction = 10
                if state_dict["trial"] == "UP":
                    correctness = 1
                else:
                    correctness = 0
            else:
                direction = 20
                if state_dict["trial"] == "UP":
                    correctness = 0
                else:
                    correctness = 1

        # Send instructions data to EXO
        instructions_data = [int(torque_profile), int(correctness), int(direction)]
        self.outlet_EXO.push_sample(instructions_data)
        # print(instructions_data)

        # Map torque profile to its corresponding name
        t_profile_dict = {0: "trapezoid", 1: "triangular", 2: "sinusoide", 3: "rectangular_pulse", 4: "smoothed_trapezoid"}

        state_dict["torque_profile"] = t_profile_dict[torque_profile]
        state_dict["correctness"] = correctness

    def get_predictions(self, stop_event: threading.Event, state_dict: dict = None, verbose: bool=False):
            if state_dict is None:
                state_dict = {}
            previous_time = perf_counter()
            while not stop_event.is_set():
                self.predictions_inlet.flush()
                recieved = False
                while state_dict["current_state"] in {"TRIAL_UP", "TRIAL_DOWN"}:
                    current_time = perf_counter()
                    if current_time - previous_time >= 1/200:
                        sample, timestamp = self.predictions_inlet.pull_sample(timeout=0.1)
                        if sample is not None and len(sample) > 0:
                            prediction_data = json.loads(sample[0])  # If there's only 1 channel
                            if not recieved:
                                if state_dict["activate_EXO"]:
                                    state_dict["prediction"] = prediction_data["predicted_event_name"]
                                recieved = True
                                if verbose:
                                    self.logger_predictions.info(prediction_data)
                        previous_time = current_time
