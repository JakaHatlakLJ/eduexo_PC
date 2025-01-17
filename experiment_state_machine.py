from time import time
import numpy as np
import random
import numpy as np
import pygame



# Ta program skrbi za sledenje in določanje stanj v katerih se nahaja trial. vsi možni stati so definirani v StateMachine classu ki določa naslednje stanje in naslednji trial glede na kvazi slučajen seznam eventov.
# State_dict beleži vse potrebne podatke za izris in beleženje stanj. ves cas se ga updata in bere iz njega. ugotovi kako ga uporabljati in spremeni

# poleg tega programa potrebujes se enega za branje lsl streama in updatanje state_dicta ter za izrisovanje interfacea za preglednejšo kodo ustavri še program za izrisovanje interfacea in avtomatsko updatanje pozicij kroga


class StateMachine:
    """
    EVENT IDS vs EVEN TYPES:\n
    99 - nothing\n
    10 - prompt "UP" shown\n
    11 - user started moving during "UP" trial\n
    20 - prompt "DOWN" shown\n
    21 - user started moving during "DOWN" trial\n
    30 - successful trial\n
    40 - failed trial\n
    50 - trial timeout\n
    """
    
    INITIAL_SCREEN = 0
    
    RETURN_TO_CENTER = 1
    IN_MIDDLE_CIRCLE = 2

    GO_TO_UPPER_BAND = 3
    IN_UPPER_BAND = 4
    GO_OUT_OF_UPPER_BAND = 5

    GO_TO_LOWER_BAND = 6
    IN_LOWER_BAND = 7
    GO_OUT_OF_LOWER_BAND = 8

    FAILURE = 9
    TIMEOUT = 10
    PAUSE = 11
    EXIT = 12
    
    def __init__(self, trial_No = 4):
        self.current_state = None

        self.trial_No = trial_No
        self.i = 0
        self.times = []
        
        # construct reverse state lookup
        all_variables = vars(StateMachine)
        self.reverse_state_lookup = {all_variables[name]: name for name in all_variables if isinstance(all_variables[name], int) and name.isupper()}
        
    
    def maybe_update_state(self, state_dict):
        experiment_over = False  

        self.one_time_ENTER(state_dict) # One time ENTER trigger
        self.one_time_ESCAPE(state_dict) # One time ESC trigger
        self.latch_SPACE(state_dict) # SPACE latch

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

        #### WHEN WAITING FOR INITAL POSITION
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
                    if self.events[self.i] == 1:
                        state_dict["event_id"] = 10
                        state_dict["event_type"] = "UP"
                        state_dict["current_trial_No"] = self.i + 1
                        self.current_state = StateMachine.GO_TO_UPPER_BAND
                        self.set_go_to_band(state_dict)
                        self.i += 1
                    else:
                        state_dict["event_type"] = "DOWN"
                        state_dict["event_id"] = 20
                        state_dict["current_trial_No"] = self.i + 1
                        self.current_state = StateMachine.GO_TO_LOWER_BAND
                        self.set_go_to_band(state_dict)
                        self.i += 1

        #### WHEN "UP" TRIAL IS HAPPENING
        elif self.current_state == StateMachine.GO_TO_UPPER_BAND:
            if state_dict["in_the_middle"] is False:
                state_dict["event_type"] = "m_UP"
                state_dict["event_id"] = 11
            if state_dict["is_UP"]:
                self.current_state = StateMachine.IN_UPPER_BAND
                self.set_in_upper_band(state_dict)
                self.set_success(state_dict)
                self.times.append(state_dict["TO"]-state_dict["remaining_time"])
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
                    state_dict["avg_time"] = round(sum(self.times)/len(self.times), 2)
                    state_dict["succ_trials"] = len(self.times)

        #### WHEN "DOWN" TRIAL IS HAPPENING
        elif self.current_state == StateMachine.GO_TO_LOWER_BAND:
            if state_dict["in_the_middle"] is False:
                state_dict["event_type"] = "m_DOWN"
                state_dict["event_id"] = 21
            if state_dict["is_DOWN"]:
                self.current_state = StateMachine.IN_LOWER_BAND
                self.set_in_lower_band(state_dict)
                self.set_success(state_dict)
                self.times.append(state_dict["TO"]-state_dict["remaining_time"])
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
                    state_dict["avg_time"] = round(sum(self.times)/len(self.times), 2)
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
                self.previous_state = self.current_state
                self.current_state = StateMachine.PAUSE
                state_dict["timeout"] = state_dict["remaining_time"]
        
        #### UNPAUSE
        elif self.current_state == StateMachine.PAUSE:
            if state_dict["space_pressed"] == False:
                self.current_state = self.previous_state
                state_dict["trial_time"] = time()

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
        elif state_dict["escape_pressed"] == True :
            self.current_state = StateMachine.EXIT
            self.set_exit_or_error(state_dict, "firebrick", "EXPERIMENT TERMINATED")

        #### STREAM BREAK
        if state_dict["stream_online"] == False:
            self.current_state = StateMachine.EXIT
            self.set_exit_or_error(state_dict, "firebrick", "STREAM OFFLINE", "Press ESC to exit or press ENTER when stream is online")


        #### WHILE TRIAL IS IN PROGRESS
        if self.current_state in {StateMachine.GO_TO_LOWER_BAND, StateMachine.GO_TO_UPPER_BAND}:
            state_dict["remaining_time"] = round(state_dict["timeout"] - (time() - state_dict["trial_time"]), 1)
            state_dict["trial_in_progress"] = True
            if state_dict["remaining_time"] <= 0:
                self.current_state = StateMachine.TIMEOUT
                self.set_trial_timeout(state_dict)
        else:
            state_dict["trial_in_progress"] = False
            state_dict["remaining_time"] = ""


        if self.current_state is not None:
            state_dict["current_state"] = self.reverse_state_lookup[self.current_state]        
        else:
            state_dict["current_state"] = "None"

        if self.current_state == StateMachine.RETURN_TO_CENTER:
            state_dict["event_id"] = 99
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

        ones = np.ones(int(self.trial_No/2))
        zeros = np.zeros(int(self.trial_No/2))
        self.events = np.append(ones, zeros)
        random.shuffle(self.events) # quasi-random events

    def set_return_to_center(self, state_dict):
        state_dict["state_start_time"] = None
        state_dict["main_text"] = "Return to center"
        state_dict["timeout"] = state_dict["TO"]

    def set_in_middle_circle(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = np.random.uniform(*state_dict["state_wait_time_range"]) # s
        state_dict["main_text"] = "Wait for trial start"
    
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
        
    def set_success(self, state_dict):
        state_dict["event_type"] = "SUCCESS"
        state_dict["event_id"] = 30    

    def set_failure(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = 1.5
        state_dict["main_text"] = state_dict["event_type"] = "FAIL"
        state_dict["event_id"] = 40  

    def set_trial_timeout(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = 1.5
        state_dict["main_text"] = state_dict["event_type"] = "TIMEOUT"
        state_dict["event_id"] = 50 

    def set_trial_termination(self, state_dict):        
        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = 0.5

    def set_exit_or_error(self, state_dict, background_color = "green4", main_text = "EXPERIMENT FINISHED", sub_text = "Press ESC to exit or ENTER to restart."):
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