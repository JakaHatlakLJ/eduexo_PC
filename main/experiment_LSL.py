from pylsl import StreamInfo, StreamOutlet, local_clock, resolve_byprop, StreamInlet
from time import perf_counter
import json

class LSLHandler:

    def __init__(self, logger, receive=True, send=True):
        """
        Initialize the LSLHandler class.

        Args:
            logger (Logger): Logger instance for logging messages.
            receive (bool): Flag to enable receiving data from LSL stream.
            send (bool): Flag to enable sending data to LSL stream.
        """
        self.logger = logger
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
                streams = resolve_byprop('type', 'EXO', timeout=10)
                if streams:
                    break
                logger.warning("No LSL stream found of type: 'EXO'. Retrying...")
            self.inlet = StreamInlet(streams[0])
            logger.info("Receiving data from EXO...")

    def stream_events_data(self, stop_event, state_dict, the_lock):
        """
        Continuously stream position/torque data (0.1s interval)
        and send an 'event' every 10s using one LSL Outlet.

        Args:
            stop_event (threading.Event): Event to signal stopping the streaming.
            state_dict (dict): Dictionary containing the current state information.
            the_lock (threading.Lock): Lock to synchronize access to shared resources.
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
                    # print(data_json_str)

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
                    print(event_json_str)
                    old_event = state_dict["event_id"]

            except Exception as e:
                self.logger.error(f"Error in streaming Events data: {e}")
                break

        self.logger.info("Stopped streaming Events data.")

    def EXO_stream_in(self, state_dict):
        """
        Receive data from EXO and update the state dictionary.

        Args:
            state_dict (dict): Dictionary containing the current state information.
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

    def EXO_stream_out(self, state_dict, torque_profile, correctness):
        """
        Send a TorqueProfile, direction, and Correctness once every time a new event happens.

        Args:
            state_dict (dict): Dictionary containing the current state information.
            torque_profile (int): Torque profile to be sent.
            correctness (int): Correctness of the execution.
        """
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

        # Send instructions data to EXO
        instructions_data = [int(torque_profile), int(correctness), int(direction)]
        self.outlet_EXO.push_sample(instructions_data)
        # print(instructions_data)

        # Map torque profile to its corresponding name
        t_profile_dict = {0: "trapezoid", 1: "triangular", 2: "sinusoide", 3: "rectangular_pulse", 4: "smoothed_trapezoid"}

        state_dict["torque_profile"] = t_profile_dict[torque_profile]
        state_dict["correctness"] = correctness

