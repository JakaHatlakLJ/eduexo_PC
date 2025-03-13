from time import time
import numpy as np
import random
import pygame

class StateMachine:
    """
    EVENT IDS vs EVENT TYPES:\n
    99 - nothing\n
    10 - prompt "UP" shown (RED): IMAGINE "UP"\n
    11 - prompt "UP" changed (Yellow): INTEND "UP"\n
    12 - prompt "UP" changed (Green): EXECUTE "UP"\n
    20 - prompt "DOWN" shown (RED): IMAGINE "DOWN"\n
    21 - prompt "DOWN" changed (Yellow): INTEND "DOWN"\n
    22 - prompt "DOWN" changed (Green): EXECUTE "DOWN"\n
    30 - exo execution correct\n
    40 - exo execution incorrect\n
    50 - success\n
    60 - failure\n
    70 - timeout
    """
    
    no_event                    = 99
    imagine_UP                  = 10
    intend_UP                   = 11
    execute_UP                  = 12
    imagine_DOWN                = 20
    intend_DOWN                 = 21
    execute_DOWN                = 22
    exo_execution_correct       = 30
    exo_execution_incorrect     = 40
    success                     = 50
    failure                     = 60
    timeout                     = 70
    
    # State IDs
    INITIAL_SCREEN = 0


    RETURN_TO_CENTER = 1
    IN_MIDDLE_CIRCLE = 2
    WAITING = 3
    IMAGINATION = 4
    INTENTION = 5

    TRIAL_UP = 6
    IN_UPPER_BAND = 7
    GO_OUT_OF_UPPER_BAND = 8
    TRIAL_DOWN = 9
    IN_LOWER_BAND = 10
    GO_OUT_OF_LOWER_BAND = 11

    FAILURE = 12
    TIMEOUT = 13
    PAUSE = 14
    EXIT = 15

    def __init__(self, trial_No=10, control_trial_No=2, correct_percentage=0.7):
        self.current_state = None
        self.torque_profile = 0
        self.trial_No = trial_No
        self.control_trial_No = control_trial_No
        self.correct_percentage = correct_percentage
        self.i = 0
        self.times = []
        self.correctness = None
        self.send_once = True        
        # Construct reverse state lookup
        all_variables = vars(StateMachine)
        self.reverse_state_lookup = {all_variables[name]: name for name in all_variables if isinstance(all_variables[name], int) and name.isupper()}
    
    def maybe_update_state(self, state_dict, exo_stream_out):
        """
        Updates the state of the experiment state machine based on the current state and state dictionary.
        Args:
            state_dict (dict): A dictionary containing the current state information and various flags.
            exo_stream_out (function): A function to send data through the EXO "Instructions" stream.
        Returns:
            tuple: A tuple containing a boolean indicating if the experiment is over and the updated state dictionary.
        The state machine transitions through the following states:
            - INITIAL_SCREEN: Initial screen state.
            - RETURN_TO_CENTER: Waiting for the initial position.
            - IN_MIDDLE_CIRCLE: Waiting in the middle for the trial to start.
            - WAITING: Waiting for the start of the trial.
            - IMAGINATION: Imagining movement.
            - INTENTION: Intending movement.
            - TRIAL_UP: Executing "UP" trial.
            - IN_UPPER_BAND: "UP" trial successful.
            - TRIAL_DOWN: Executing "DOWN" trial.
            - IN_LOWER_BAND: "DOWN" trial successful.
            - TIMEOUT: Timeout occurred.
            - FAILURE: Failure occurred.
            - PAUSE: Experiment paused.
            - EXIT: Exiting the experiment.
        The function handles various events and transitions, including:
            - Enter key press to start the experiment.
            - Space key press to pause/unpause the experiment.
            - Escape key press to terminate the experiment.
            - Stream online/offline status.
            - Trial execution and success/failure handling.
            - Timeout handling.
        """

        experiment_over = False  

        self.one_time_ENTER(state_dict)  # One time ENTER trigger
        self.one_time_ESCAPE(state_dict)  # One time ESC trigger
        self.latch_SPACE(state_dict)  # SPACE latch

        #### WHEN NONE
        if self.current_state is None:  
            self.current_state = StateMachine.INITIAL_SCREEN
            self.set_initial_screen(state_dict)

        #### AT THE BEGINNING
        elif self.current_state == StateMachine.INITIAL_SCREEN:
            if state_dict["enter_pressed"]:
                self.current_state = StateMachine.RETURN_TO_CENTER
                self.set_start_experiment(state_dict)
                self.set_return_to_center(state_dict)

        #### WHEN WAITING FOR INITIAL POSITION
        elif self.current_state == StateMachine.RETURN_TO_CENTER:
            if state_dict["in_the_middle"]:
                self.current_state = StateMachine.IN_MIDDLE_CIRCLE
                self.set_in_middle_circle(state_dict)

        #### WHEN WAITING IN THE MIDDLE FOR TRIAL TO START
        elif self.current_state == StateMachine.IN_MIDDLE_CIRCLE:
            if state_dict["in_the_middle"] == False:
                self.current_state = StateMachine.RETURN_TO_CENTER
                self.set_return_to_center(state_dict)
            elif time() - state_dict["state_start_time"] >= state_dict["state_wait_time"]:
                if self.i < len(self.events):
                    self.current_state = StateMachine.WAITING
                    if self.synthetic_decoder:
                        self.correctness = self.correctness_list[self.i]
                        self.torque_profile = self.torque_profile_list[self.i]
                    if self.events[self.i] == 1:
                        self.i += 1
                        state_dict["trial"] = "UP"
                        state_dict["current_trial_No"] = self.i
                        self.set_waiting(state_dict)
                    else:
                        self.i += 1
                        state_dict["trial"] = "DOWN"
                        state_dict["current_trial_No"] = self.i
                        self.set_waiting(state_dict)

        #### WHEN WAITING FOR START
        elif self.current_state == StateMachine.WAITING:
            if time() - state_dict["state_start_time"] >= state_dict["state_wait_time"]:
                if state_dict["trial"] == "UP":
                    state_dict["event_id"] = StateMachine.imagine_UP
                    state_dict["event_type"] = "imagine_UP"
                else:
                    state_dict["event_type"] = "imagine_DOWN"
                    state_dict["event_id"] = StateMachine.imagine_DOWN
                self.current_state = StateMachine.IMAGINATION
                self.set_imagine(state_dict)

        #### WHEN IMAGINING MOVEMENT
        elif self.current_state == StateMachine.IMAGINATION:
            if time() - state_dict["state_start_time"] >= state_dict["state_wait_time"]:
                if state_dict["trial"] == "UP":
                    state_dict["event_type"] = "intend_UP"
                    state_dict["event_id"] = StateMachine.intend_UP
                else:
                    state_dict["event_type"] = "intend_DOWN"
                    state_dict["event_id"] = StateMachine.intend_DOWN
                self.current_state = StateMachine.INTENTION
                self.set_intend(state_dict)

        #### WHEN INTENDING MOVEMENT
        elif self.current_state == StateMachine.INTENTION:
            self.send_once = True
            if time() - state_dict["state_start_time"] >= state_dict["state_wait_time"]:
                if state_dict["trial"] == "UP":
                    self.current_state = StateMachine.TRIAL_UP
                    state_dict["event_type"] = "execute_UP"
                    state_dict["event_id"] = StateMachine.execute_UP
                else:
                    self.current_state = StateMachine.TRIAL_DOWN
                    state_dict["event_type"] = "execute_DOWN"
                    state_dict["event_id"] = StateMachine.execute_DOWN
                self.set_go_to_band(state_dict)

        #### WHEN "UP" TRIAL IS HAPPENING
        elif self.current_state == StateMachine.TRIAL_UP:
            if state_dict["in_the_middle"] == False:
                if state_dict["activate_EXO"]:
                    if self.synthetic_decoder:
                        if self.send_once:
                            exo_stream_out(state_dict, self.torque_profile, self.correctness)
                            self.send_once = False
                    else: 
                        if state_dict["prediction"] is not None:
                            torque_profile = np.random.choice(a=[0, 1, 2, 3, 4],p=[0, 0.8, 0, 0.2, 0])
                            exo_stream_out(state_dict, torque_profile)
                            state_dict["prediction"] = None
            if state_dict["is_UP"]:
                self.current_state = StateMachine.IN_UPPER_BAND
                self.set_in_upper_band(state_dict)
                self.set_success(state_dict)
                self.times.append(state_dict["TO"] - state_dict["remaining_time"])
            elif state_dict["is_DOWN"]:
                self.current_state = StateMachine.FAILURE
                self.set_failure(state_dict)  

        #### IF "UP" TRIAL IS SUCCESSFUL
        elif self.current_state == StateMachine.IN_UPPER_BAND:
            if time() - state_dict["state_start_time"] >= state_dict["state_wait_time"]:
                self.current_state = StateMachine.RETURN_TO_CENTER
                self.set_return_to_center(state_dict)
                if self.i == len(self.events):
                    self.current_state = StateMachine.EXIT
                    self.set_exit_or_error(state_dict)
                    state_dict["avg_time"] = round(sum(self.times) / len(self.times), 2)
                    state_dict["succ_trials"] = len(self.times)

        #### WHEN "DOWN" TRIAL IS HAPPENING
        elif self.current_state == StateMachine.TRIAL_DOWN:
            if state_dict["in_the_middle"] == False:
                if state_dict["activate_EXO"]:
                    if self.synthetic_decoder:
                        if self.send_once:
                            exo_stream_out(state_dict, self.torque_profile, self.correctness)
                            self.send_once = False 
                    else: 
                        if state_dict["prediction"] is not None:
                            torque_profile = np.random.choice(a=[0, 1, 2, 3, 4],p=[0, 0.8, 0, 0.2, 0])
                            exo_stream_out(state_dict, torque_profile)
                            state_dict["prediction"] = None
            if state_dict["is_DOWN"]:
                self.current_state = StateMachine.IN_LOWER_BAND
                self.set_in_lower_band(state_dict)
                self.set_success(state_dict)
                self.times.append(state_dict["TO"] - state_dict["remaining_time"])
            elif state_dict["is_UP"]:
                self.current_state = StateMachine.FAILURE
                self.set_failure(state_dict)                              
        
        #### IF "DOWN" TRIAL IS SUCCESSFUL
        elif self.current_state == StateMachine.IN_LOWER_BAND:
            if time() - state_dict["state_start_time"] >= state_dict["state_wait_time"]:
                self.current_state = StateMachine.RETURN_TO_CENTER
                self.set_return_to_center(state_dict)  
                if self.i == len(self.events):
                    self.current_state = StateMachine.EXIT
                    self.set_exit_or_error(state_dict)              
                    state_dict["avg_time"] = round(sum(self.times) / len(self.times), 2)
                    state_dict["succ_trials"] = len(self.times)

        #### WHEN TIMEOUT OR FAILURE OCCUR
        elif self.current_state in {StateMachine.TIMEOUT, StateMachine.FAILURE}:
            if time() - state_dict["state_start_time"] >= state_dict["state_wait_time"]:
                if self.i == len(self.events):
                    self.current_state = StateMachine.EXIT
                    self.set_exit_or_error(state_dict)
                    if self.times == []:
                        state_dict["avg_time"] = 0
                else:
                    self.current_state = StateMachine.RETURN_TO_CENTER
                    self.set_return_to_center(state_dict)

        #### PAUSE
        if state_dict["space_pressed"] and not self.current_state == StateMachine.EXIT:
            if self.current_state != StateMachine.PAUSE:
                if state_dict["trial_in_progress"] and self.current_state in {StateMachine.TRIAL_UP, StateMachine.TRIAL_DOWN}:
                    state_dict["timeout"] = state_dict["remaining_time"]
                self.previous_trial = state_dict["trial"]
                self.previous_event_id = state_dict["event_id"]
                self.previous_event_type = state_dict["event_type"]
                state_dict["event_id"] = StateMachine.no_event
                state_dict["event_type"] = ""
                self.previous_state = self.current_state
                self.current_state = StateMachine.PAUSE
        
        #### UNPAUSE
        elif self.current_state == StateMachine.PAUSE:
            if state_dict["space_pressed"] == False:
                if self.previous_state == "IN_MIDDLE_CIRCLE":
                    self.previous_state = StateMachine.RETURN_TO_CENTER
                    self.set_return_to_center(state_dict)
                else:    
                    self.current_state = self.previous_state
                state_dict["trial_time"] = time()
                state_dict["state_start_time"] = time()
                state_dict["trial"] = self.previous_trial
                state_dict["event_id"] = self.previous_event_id
                state_dict["event_type"] = self.previous_event_type
                state_dict["trial_in_progress"] = True

        #### WHEN EXITING
        if self.current_state == StateMachine.EXIT and state_dict["stream_online"] == True:
            if state_dict["escape_pressed"]:
                experiment_over = True
            elif state_dict["enter_pressed"]:
                self.i = 0
                self.times = []
                self.current_state = None
                state_dict["space_pressed"] = False
                state_dict["needs_update"] = True
                state_dict["avg_time"] = None

        #### FORCE TERMINATION
        elif state_dict["escape_pressed"] == True:
            self.current_state = StateMachine.EXIT
            self.set_exit_or_error(state_dict, "firebrick", "EXPERIMENT TERMINATED")

        #### STREAM BREAK 
        if state_dict["stream_online"] == False:
            self.current_state = StateMachine.EXIT
            self.set_exit_or_error(state_dict, "firebrick", "STREAM OFFLINE", "Press ESC to exit or press ENTER when stream is online")

        #### WHILE TRIAL IS IN PROGRESS
        if self.current_state in {StateMachine.WAITING, StateMachine.IMAGINATION, StateMachine.INTENTION, StateMachine.TRIAL_UP, StateMachine.TRIAL_DOWN}:
            state_dict["trial_in_progress"] = True
            if self.current_state in {StateMachine.TRIAL_DOWN, StateMachine.TRIAL_UP}:
                if state_dict["exo_execution"] == 1:
                    if self.synthetic_decoder:
                        if self.correctness == 1:
                            state_dict["event_id"] = StateMachine.exo_execution_correct
                            state_dict["event_type"] = "exo_execution_correct"
                        else:
                            state_dict["event_id"] = StateMachine.exo_execution_incorrect
                            state_dict["event_type"] = "exo_execution_incorrect"

                state_dict["remaining_time"] = round(state_dict["timeout"] - (time() - state_dict["trial_time"]), 1)

                if state_dict["remaining_time"] <= 0:
                    self.current_state = StateMachine.TIMEOUT
                    self.set_trial_timeout(state_dict)
        else:
            if self.current_state not in {StateMachine.IN_UPPER_BAND, StateMachine.IN_LOWER_BAND}:
                state_dict["trial"] = ""
            state_dict["trial_in_progress"] = False
            state_dict["remaining_time"] = ""
            state_dict["torque_profile"] = "None"

        if self.current_state is not None:
            state_dict["current_state"] = self.reverse_state_lookup[self.current_state]             
        else:
            state_dict["current_state"] = "None"

        if self.control_trial_No < self.i <= self.trial_No + self.control_trial_No:
            state_dict["activate_EXO"] = True
        else:
            state_dict["activate_EXO"] = False

        if self.current_state == StateMachine.RETURN_TO_CENTER:
            state_dict["event_id"] = StateMachine.no_event
            state_dict["event_type"] = ""

        return experiment_over, state_dict

    def set_waiting_for_start(self, state_dict):
        state_dict["state_start_time"] = None
        state_dict["main_text"] = "Waiting to start recording."

    def set_initial_screen(self, state_dict): 
        state_dict["state_start_time"] = None
        state_dict["main_text"] = "Press ENTER when ready."
        state_dict["background_color"] = "green4"

    def set_start_experiment(self, state_dict):
        state_dict["experiment_start"] = time()
        state_dict["main_text"] = ""
        state_dict["background_color"] = "black"

        # Generate trial rules 
        if state_dict["synthetic_decoder"]:
            # if synthetic decoder will be used to decode events
            self.synthetic_decoder = True
            self.generate_synthetic_trials(self.control_trial_No, self.trial_No, self.correct_percentage, update_instance=True)
        else:
            # if "PredictionStream" will be used to decode events
            self.synthetic_decoder = False
            self.generate_trials(self.control_trial_No, self.trial_No, update_instance=True)

    def set_return_to_center(self, state_dict):
        state_dict["state_start_time"] = None
        state_dict["main_text"] = ""
        state_dict["timeout"] = state_dict["TO"]

    def set_in_middle_circle(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = 1.5  # s
        state_dict["main_text"] = ""
    
    def set_waiting(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = np.random.uniform(*state_dict["state_wait_time_range"])  # s
        state_dict["color"] = "white"

    def set_imagine(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = np.random.uniform(*state_dict["imagination_time_range"])  # s
        state_dict["color"] = "red"

    def set_intend(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = np.random.uniform(*state_dict["intention_time_range"])  # s
        state_dict["color"] = "yellow"

    def set_in_upper_band(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = 1
        state_dict["main_text"] = "SUCCESS"

    def set_in_lower_band(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = 1
        state_dict["main_text"] = "SUCCESS"

    def set_go_to_band(self, state_dict):
        state_dict["trial_time"] = time()
        state_dict["color"] = "green3"
        
    def set_success(self, state_dict):
        state_dict["event_type"] = "SUCCESS"
        state_dict["event_id"] = StateMachine.success    

    def set_failure(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = 1.5
        state_dict["main_text"] = state_dict["event_type"] = "FAIL"
        state_dict["event_id"] = StateMachine.failure  

    def set_trial_timeout(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = 1.5
        state_dict["main_text"] = state_dict["event_type"] = "TIMEOUT"
        state_dict["event_id"] = StateMachine.timeout 

    def set_trial_termination(self, state_dict):        
        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = 0.5

    def set_exit_or_error(self, state_dict, background_color="green4", main_text="EXPERIMENT FINISHED", sub_text="Press ESC to exit or ENTER to restart."):
        state_dict["background_color"] = background_color
        state_dict["main_text"] = main_text 
        state_dict["sub_text"] = sub_text

    @staticmethod
    def one_time_ENTER(state_dict):
        current_enter_state = pygame.key.get_pressed()[pygame.K_RETURN]
        if current_enter_state and not state_dict["previous_enter_state"]:
            state_dict["enter_pressed"] = True
        else:
            state_dict["enter_pressed"] = False
        state_dict["previous_enter_state"] = current_enter_state

    @staticmethod
    def one_time_ESCAPE(state_dict):
        current_escape_state = pygame.key.get_pressed()[pygame.K_ESCAPE]
        if current_escape_state and not state_dict["previous_escape_state"]:
            state_dict["escape_pressed"] = True
        else:
            state_dict["escape_pressed"] = False
        state_dict["previous_escape_state"] = current_escape_state

    @staticmethod
    def latch_SPACE(state_dict):
        current_space_state = pygame.key.get_pressed()[pygame.K_SPACE]
        if current_space_state and not state_dict["previous_space_state"]:
            state_dict["space_pressed"] = not state_dict.get("space_pressed", False)
        state_dict["previous_space_state"] = current_space_state

    @staticmethod
    def generate_control_trials(n):
        """Generate control trials with only incorrect executions (0)."""
        ones = np.ones(n // 2, dtype=int)
        zeros = np.zeros(n // 2, dtype=int)
        if n % 2 != 0:
            ones = np.append(ones, 1)  # Ensure UP gets the extra trial
        events = np.append(ones, zeros)
        executions = np.zeros(n, dtype=int)  # All incorrect
        torques = np.zeros(n, dtype=int) # All smth
        trials = np.column_stack((events, executions, torques))
        np.random.shuffle(trials)
        return trials

    def generate_trials(self, control_trial_No: int, trial_No: int, update_instance: bool = False) -> np.ndarray:
        """
        Generates randomized trials without execution correctness and torque profiles, used with real decoder.
        
        :param control_trial_No: Number of control trials.
        :param trial_No: Number of main trials.
        :param update_instance: If True, updates the instance variables with the generated trials.
        
        Returns:
            np.ndarray: An array of all trials.
        """

        trial_rules1 = self.generate_control_trials(control_trial_No)
        trial_rules2 = self.generate_control_trials(trial_No)
        trial_rules3 = self.generate_control_trials(control_trial_No)
        # --- COMBINE ALL TRIALS ---
        final_trials = np.vstack((trial_rules1, trial_rules2, trial_rules3), dtype=int)
        if update_instance:
            self.events = final_trials[:, 0]
        return final_trials[:, 0]

    def generate_synthetic_trials(self, control_trial_No: int, trial_No: int, correct_percentage: float=0.7, update_instance: bool = False) -> np.ndarray:
        """
        Generates a randomized trial structure with balanced correct/incorrect executions.
        
        :param control_trial_No: Number of control trials without execution.
        :param trial_No: Number of main trials with varying execution correctness.
        :param correct_percentage: Percentage of correct executions in the main trials.
        :param update_instance: If True, updates the instance variables with the generated trials.
        
        Returns:
            np.ndarray: A 2D array where each row represents a trial with columns for event type, execution correctness, and torque profile.
        """

        trial_rules1 = self.generate_control_trials(control_trial_No)
        trial_rules3 = self.generate_control_trials(control_trial_No)

        # --- MAIN TRIALS (VARYING EXECUTION CORRECTNESS) ---
        # Generate UP (1) and DOWN (0) trials, ensuring an extra UP if odd
        ones = np.ones(trial_No // 2, dtype=int)
        zeros = np.zeros(trial_No // 2, dtype=int)
        events = np.append(ones, zeros)

        if trial_No % 2 != 0:
            events = np.append(events, int(1))  # Extra UP

        # Compute number of correct/incorrect trials
        correct_count = int(np.round(trial_No * correct_percentage))
        incorrect_count = trial_No - correct_count           

        # Distribute correct/incorrect executions evenly among UPs and DOWNs
        correct_up = correct_count // 2
        correct_down = correct_count // 2
        incorrect_up = incorrect_count // 2
        incorrect_down = incorrect_count // 2

        # Assign leftover trials due to rounding
        leftover_correct = correct_count % 2
        leftover_incorrect = incorrect_count % 2

        if leftover_correct:
            correct_up += 1
        if leftover_incorrect:
            incorrect_down += 1

        # Create execution labels
        correct_labels_up = np.ones(int(correct_up), dtype=int)
        correct_labels_down = np.ones(int(correct_down), dtype=int)
        incorrect_labels_up = np.zeros(int(incorrect_up), dtype=int)
        incorrect_labels_down = np.zeros(int(incorrect_down), dtype=int)

        # Merge correct and incorrect labels while keeping balance
        executions = np.concatenate((correct_labels_up, incorrect_labels_up, correct_labels_down, incorrect_labels_down))

        torques = np.array([], dtype=int)
        for i in range(len(executions)):
            torque_profile = np.random.choice(a=[0, 1, 2, 3, 4],p=[0, 0.8, 0, 0.2, 0])
            torques = np.append(torques, torque_profile)            

        # Combine into trial matrix and shuffle
        trial_rules2 = np.column_stack((events, executions, torques))
        np.random.shuffle(trial_rules2)

        # --- COMBINE ALL TRIALS ---
        final_trials = np.vstack((trial_rules1, trial_rules2, trial_rules3), dtype=int)

        if update_instance:
            self.events = final_trials[:, 0]
            self.correctness_list = final_trials[:, 1]
            self.torque_profile_list = final_trials[:, 2]

        return final_trials
