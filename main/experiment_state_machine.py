from time import time
import numpy as np
import random
import pygame
import logging

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

    def __init__(self, LSL):
        self.current_state = None
        self.torque = None
        self.torque_profile = None
        self.correctness = None
        self.LSL = LSL
        self.i = 0
        self.times = []
        self.send_once = True      
        self.stream_break = False  
        # Construct reverse state lookup
        all_variables = vars(StateMachine)
        self.reverse_state_lookup = {all_variables[name]: name for name in all_variables if isinstance(all_variables[name], int) and name.isupper()}
        self.profiles_dict = {"trapezoid" : 0, "triangular" : 1, "sinusoidal" : 2, "rectangular" : 3, "smooth trapezoid" : 4}

        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("state_machine")
        self.logger = logger

    
    def maybe_update_state(self, state_dict: dict):
        """
        Updates the state of the experiment state machine based on the current state and state dictionary.
        Args:
            state_dict (dict): A dictionary containing the current state information and various flags.
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
                self.send_once = True
                if self.i < len(self.events):
                    self.correctness = self.correctness_list[self.i]
                    self.torque_profile = self.torque_profile_list[self.i]
                    self.torque = self.torque_magnitude_list[self.i]
                    if self.events[self.i] == 1:
                        self.i += 1
                        state_dict["trial"] = "UP"
                        state_dict["current_trial_No"] = self.i
                    else:
                        self.i += 1
                        state_dict["trial"] = "DOWN"
                        state_dict["current_trial_No"] = self.i
                    if "wait" in state_dict["trial_states"]:
                        self.current_state = StateMachine.WAITING
                        self.set_waiting(state_dict)
                    else:
                        if "imagine" in state_dict["trial_states"]:
                            self.set_imagine(state_dict)
                        else:
                            if "intend" in state_dict["trial_states"]:
                                self.set_intend(state_dict)
                            else:
                                self.set_go_to_band(state_dict)


        #### WHEN WAITING FOR START
        elif self.current_state == StateMachine.WAITING:
            if time() - state_dict["state_start_time"] >= state_dict["state_wait_time"]:
                if "imagine" in state_dict["trial_states"]:
                    self.set_imagine(state_dict)
                else:
                    if "intend" in state_dict["trial_states"]:
                        self.set_intend(state_dict)
                    else:
                        self.set_go_to_band(state_dict)

        #### WHEN IMAGINING MOVEMENT
        elif self.current_state == StateMachine.IMAGINATION:
            if time() - state_dict["state_start_time"] >= state_dict["state_wait_time"]:
                if "intend" in state_dict["trial_states"]:
                    self.set_intend(state_dict)
                else:
                    self.set_go_to_band(state_dict)

        #### WHEN INTENDING MOVEMENT
        elif self.current_state == StateMachine.INTENTION:
            if time() - state_dict["state_start_time"] >= state_dict["state_wait_time"]:
                self.set_go_to_band(state_dict)

        #### WHEN "UP" TRIAL IS HAPPENING
        elif self.current_state == StateMachine.TRIAL_UP:
            if state_dict["in_the_middle"] == False:
                if state_dict["activate_EXO"]:
                    if not state_dict["real_time_prediction"]:
                        if self.send_once:
                            self.LSL.EXO_stream_out(state_dict, self.torque_profile, self.torque, self.correctness)
                            self.send_once = False
                    else: 
                        if state_dict["prediction"] is not None:
                            self.LSL.EXO_stream_out(state_dict, self.torque_profile, self.torque)
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
                    if not state_dict["real_time_prediction"]:
                        if self.send_once:
                            self.LSL.EXO_stream_out(state_dict, self.torque_profile, self.torque, self.correctness)
                            self.send_once = False
                    else: 
                        if state_dict["prediction"] is not None:
                            self.LSL.EXO_stream_out(state_dict, self.torque_profile, self.torque)
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
            if self.stream_break == True:
                self.logger.info("Reconnected!")
                self.stream_break = False
            if state_dict["escape_pressed"]:
                experiment_over = True
                self.LSL.EXO_stream_out(experiment_over=True)
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
            self.stream_break = True
            self.set_exit_or_error(state_dict, "firebrick", "STREAM OFFLINE", "Press ESC to exit or press ENTER when stream is online")

        #### WHILE TRIAL IS IN PROGRESS
        if self.current_state in {StateMachine.WAITING, StateMachine.IMAGINATION, StateMachine.INTENTION, StateMachine.TRIAL_UP, StateMachine.TRIAL_DOWN}:
            state_dict["trial_in_progress"] = True
            if self.current_state in {StateMachine.TRIAL_DOWN, StateMachine.TRIAL_UP}:
                if state_dict["exo_execution"] == 1:
                    if not state_dict["real_time_prediction"]:
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
            state_dict["torque_magnitude"] = "None"

        if self.current_state is not None:
            state_dict["current_state"] = self.reverse_state_lookup[self.current_state]             
        else:
            state_dict["current_state"] = "None"

        if state_dict["familiarization_trial_No"] < self.i <= state_dict["trials_No"] - state_dict["end_control_trials"]:
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
        state_dict["current_trial_No"] = 0

    def set_start_experiment(self, state_dict):
        self.generate_trials(state_dict)
        state_dict["experiment_start"] = time()
        state_dict["main_text"] = ""
        state_dict["background_color"] = "black"

    def set_return_to_center(self, state_dict):
        state_dict["state_start_time"] = None
        state_dict["main_text"] = ""
        state_dict["timeout"] = state_dict["TO"]

    def set_in_middle_circle(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = np.random.uniform(*state_dict["start_time_range"])  # s
        state_dict["main_text"] = ""
    
    def set_waiting(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = np.random.uniform(*state_dict["state_wait_time_range"])  # s
        state_dict["color"] = "white"

    def set_imagine(self, state_dict):
        self.current_state = StateMachine.IMAGINATION
        if state_dict["trial"] == "UP":
            state_dict["event_id"] = StateMachine.imagine_UP
            state_dict["event_type"] = "imagine_UP"
        else:
            state_dict["event_type"] = "imagine_DOWN"
            state_dict["event_id"] = StateMachine.imagine_DOWN

        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = np.random.uniform(*state_dict["imagination_time_range"])  # s
        state_dict["color"] = "red"

    def set_intend(self, state_dict):
        self.current_state = StateMachine.INTENTION
        if state_dict["trial"] == "UP":
            state_dict["event_type"] = "intend_UP"
            state_dict["event_id"] = StateMachine.intend_UP
        else:
            state_dict["event_type"] = "intend_DOWN"
            state_dict["event_id"] = StateMachine.intend_DOWN

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
        if state_dict["trial"] == "UP":
            self.current_state = StateMachine.TRIAL_UP
            state_dict["event_type"] = "execute_UP"
            state_dict["event_id"] = StateMachine.execute_UP
        else:
            self.current_state = StateMachine.TRIAL_DOWN
            state_dict["event_type"] = "execute_DOWN"
            state_dict["event_id"] = StateMachine.execute_DOWN

        state_dict["trial_time"] = time()
        state_dict["color"] = "green3"
        
    def set_success(self, state_dict):
        state_dict["event_type"] = "SUCCESS"
        state_dict["event_id"] = StateMachine.success    
        self.LSL.EXO_stream_out(state_dict, trial_over = True)

    def set_failure(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = 1.5
        state_dict["main_text"] = state_dict["event_type"] = "FAIL"
        state_dict["event_id"] = StateMachine.failure  
        self.LSL.EXO_stream_out(state_dict, trial_over = True)

    def set_trial_timeout(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = 1.5
        state_dict["main_text"] = state_dict["event_type"] = "TIMEOUT"
        state_dict["event_id"] = StateMachine.timeout 
        self.LSL.EXO_stream_out(state_dict, trial_over = True)

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
    def generate_familiarization_trials(n):
        """Generate familiarization trials with only incorrect executions (0)."""
        ones = np.ones(n // 2, dtype=int)
        zeros = np.zeros(n // 2, dtype=int)
        if n % 2 != 0:
            ones = np.append(ones, 1)  # Ensure UP gets the extra trial
        events = np.append(ones, zeros)
        executions = np.zeros(n, dtype=int)  # All incorrect
        torque_profiles = np.zeros(n, dtype=int) # All smth
        torques = np.zeros(n, dtype=int) # All smth
        trials = np.column_stack((events, executions, torque_profiles, torques))
        np.random.shuffle(trials)
        return trials

    def generate_trials(self, state_dict: dict) -> np.ndarray:
        """
        Generates a randomized trial structure with balanced correct/incorrect executions.
        
        :param control_trial_No: Number of control trials without execution.
        :param trial_No: Number of main trials with varying execution correctness.
        :param correct_percentage: Percentage of correct executions in the main trials.
        :param update_instance: If True, updates the instance variables with the generated trials.
        
        Returns:
            np.ndarray: A 2D array where each row represents a trial with columns for event type, execution correctness, and torque profile.
        """

        def generate_trials_for_condition(condition_id, assistance, condition_trial_No, torque_profile, torque_magnitude):
            """
            Generates a set of trials for a given experimental condition, specifying event types, execution correctness,
            torque profiles, and torque levels for each trial.
            Parameters:
                state_dict (dict): Dictionary containing state information, including available torque profiles.
                condition_trial_No (int): Total number of trials to generate for the condition.
                correct_percentage (float): Proportion of trials to be marked as correct (between 0 and 1).
                torque_profile (str): Name of the torque profile to use, or "random" to select randomly from available profiles.
                torque_magnitude (any): Torque level label to assign to all trials.
            Returns:
                np.ndarray: A 2D array where each row represents a trial and columns correspond to:
                    [event type (1=UP, 0=DOWN), execution correctness (1=correct, 0=incorrect), torque profile, torque level].
            """
            
            ones = np.ones(condition_trial_No // 2, dtype=int)
            zeros = np.zeros(condition_trial_No // 2, dtype=int)
            events = np.append(ones, zeros)

            if condition_trial_No % 2 != 0:
                events = np.append(events, int(1))  # Extra UP

            if assistance == "assist":
                executions = np.ones(condition_trial_No)
            elif assistance == "oppose":
                executions = np.zeros(condition_trial_No)
            else:
                self.logger.error(f"Invalid assistance type: {assistance} in condition {condition_id}.")
                return None  # Invalid assistance type

            # Create torque profiles
            if torque_profile == "random":
                torque_profile_labels = []
                for i in range(condition_trial_No):
                    torque_profile_labels.append(random.choice(list(self.profiles_dict.values())))
            elif torque_profile in self.profiles_dict:
                torque_profile_labels = [self.profiles_dict[torque_profile]] * condition_trial_No
            else:
                self.logger.error(f"Invalid torque profile: {torque_profile} in condition {condition_id}.")
                return None  # Invalid torque profile
                

            # Create torque level labels
            if torque_magnitude > state_dict["exo_parameters"]["torque_limit"]:
                self.logger.warning(f"Torque magnitude ({torque_magnitude} Nm) exceeds limit, setting to {state_dict['exo_parameters']['torque_limit']} Nm.")
                torque_magnitude = state_dict["exo_parameters"]["torque_limit"]

            torque_magnitude_labels = [torque_magnitude] * condition_trial_No

            trial_rules_for_condition = np.column_stack((events, executions, torque_profile_labels, torque_magnitude_labels))
            return trial_rules_for_condition

        familiarization_trials_rules = self.generate_familiarization_trials(state_dict["familiarization_trials_No"])
        state_dict["familiarization_trial_No"] = familiarization_trials_rules.shape[0]

        if state_dict["end_control_trials"] != 0:
            end_control_trial_rules = self.generate_familiarization_trials(state_dict["end_control_trials"])

        # --- MAIN TRIALS (VARYING EXECUTION CORRECTNESS, TORQUE PROFILE AND TORQUE LEVEL) ---
        all_condition_trials = []
        for condition_id, (assist, condition_No, torque_profile, torque) in state_dict["trial_conditions"].items():
            condition_trials = generate_trials_for_condition(condition_id, assist, condition_No, torque_profile, torque)
            all_condition_trials.append(condition_trials)

        # --- SHUFFLE MAIN TRIALS ---
        main_trial_rules = np.vstack(all_condition_trials)
        np.random.shuffle(main_trial_rules)

        # --- COMBINE ALL TRIALS ---
        if state_dict["end_control_trials"] != 0:
            final_trials = np.vstack((familiarization_trials_rules, main_trial_rules, end_control_trial_rules))
        else:
            final_trials = np.vstack((familiarization_trials_rules, main_trial_rules))

        state_dict["trials_No"] = final_trials.shape[0]

        self.events = final_trials[:, 0]
        self.correctness_list = final_trials[:, 1]
        self.torque_profile_list = final_trials[:, 2]
        self.torque_magnitude_list = final_trials[:, 3]

        return final_trials
