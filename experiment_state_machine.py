from time import time

import random
import numpy as np
from interface import Colors



# Ta program skrbi za sledenje in določanje stanj v katerih se nahaja trial. vsi možni stati so definirani v StateMachine classu ki določa naslednje stanje in naslednji trial glede na kvazi slučajen seznam eventov.
# State_dict beleži vse potrebne podatke za izris in beleženje stanj. ves cas se ga updata in bere iz njega. ugotovi kako ga uporabljati in spremeni

# poleg tega programa potrebujes se enega za branje lsl streama in updatanje state_dicta ter za izrisovanje interfacea za preglednejšo kodo ustavri še program za izrisovanje interfacea in avtomatsko updatanje pozicij kroga





# import time
# random.seed(time.time())

trial_No = 20
time_delay = [1, 3]

ones = np.ones(int(trial_No/2))
zeros = np.zeros(int(trial_No/2))

events = np.append(ones, zeros)
random.shuffle(events) # quasi-random events


class StateMachine:
    
    INITIAL_SCREEN = 0
    WAITING_FOR_START = 1
    
    GO_TO_MIDDLE_CIRCLE = 2
    IN_MIDDLE_CIRCLE = 3
    GO_OUT_OF_MIDDLE_CIRCLE = 4
    
    GO_TO_UPPER_BAND_AFTER_TRIAL = 5
    GO_TO_LOWER_BAND_AFTER_TRIAL = 6

    GO_TO_UPPER_BAND = 7
    IN_UPPER_BAND = 8
    STAY_IN_UPPER_BAND = 9
    GO_OUT_OF_UPPER_BAND = 10

    GO_TO_LOWER_BAND = 11
    IN_LOWER_BAND = 12
    STAY_IN_LOWER_BAND = 13
    GO_OUT_OF_LOWER_BAND = 14

    TRIAL_TERMINATION = 15
    PAUSE = 16
    EXIT = 17
    
    def __init__(self):
        self.current_state = None
        self.prev_main_circle_position = None
        
        # construct reverse state lookup
        all_variables = vars(StateMachine)
        self.reverse_state_lookup = {all_variables[name]: name for name in all_variables if isinstance(all_variables[name], int) and name.isupper()}

    
    def maybe_update_state(self, state_dict):
        continue_loop = True
        
        #### WHEN NONE
        if self.current_state is None:
            self.current_state = StateMachine.WAITING_FOR_START
            self.set_waiting_for_start(state_dict)

        #### AT THE BEGINNING
        elif self.current_state == StateMachine.WAITING_FOR_START:
            if state_dict["is_recording"] == True:
                self.current_state = StateMachine.INITIAL_SCREEN
                self.set_initial_screen(state_dict)

        elif self.current_state == StateMachine.INITIAL_SCREEN:
            if state_dict["enter_pressed"]:
                self.current_state = StateMachine.GO_TO_MIDDLE_CIRCLE
                self.set_start_experiment(state_dict)
                self.set_go_to_middle_circle(state_dict)

        elif self.current_state == StateMachine.GO_TO_MIDDLE_CIRCLE:
            if np.linalg.norm(state_dict["main_circle_position"] - state_dict["middle_circle_position"]) < state_dict["middle_circle_radius"]: # spremeni v "loc" in kalibriraj na zacetni krog
                self.current_state = StateMachine.IN_MIDDLE_CIRCLE
                self.set_in_middle_circle(state_dict)

    #     elif self.current_state == StateMachine.IN_MIDDLE_CIRCLE:
    #         if time() - state_dict["state_start_time"] >= state_dict["state_wait_time"]:
    #             self.current_state = StateMachine.GO_TO_UPPER_BAND_AFTER_TRIAL
    #             self.set_go_to_upper_band_after_trial(state_dict)
    #         elif np.linalg.norm(state_dict["main_circle_position"] - state_dict["middle_circle_position"]) > state_dict["middle_circle_radius"]:
    #             self.current_state = StateMachine.GO_TO_MIDDLE_CIRCLE
    #             self.set_go_to_middle_circle(state_dict)

    #     #### GO TO THE LEFT / RIGHT AFTER INITIATION ENDS, OR AFTER TRIAL
    #     elif self.current_state == StateMachine.GO_TO_UPPER_BAND_AFTER_TRIAL:
    #         if np.linalg.norm(state_dict["main_circle_position"] - state_dict["upper_band_position"]) < state_dict["upper_band_radius"]:
    #             self.current_state = StateMachine.IN_UPPER_BAND
    #             self.set_in_upper_band(state_dict)

    #     elif self.current_state == StateMachine.GO_TO_LOWER_BAND_AFTER_TRIAL:
    #         if np.linalg.norm(state_dict["main_circle_position"] - state_dict["lower_band_position"]) < state_dict["lower_band_radius"]:
    #             self.current_state = StateMachine.IN_LOWER_BAND
    #             self.set_in_lower_band(state_dict)

    #     #### WHEN WAITING IN THE LEFT / RIGHT CIRCLE TO GO OUT
    #     elif self.current_state == StateMachine.IN_UPPER_BAND:
    #         if time() - state_dict["state_start_time"] >= state_dict["state_wait_time"]:
    #             self.current_state = StateMachine.GO_OUT_OF_UPPER_BAND
    #             self.set_go_out_of_upper_band(state_dict)
    #             self.prev_time = time()
    #         elif np.linalg.norm(state_dict["main_circle_position"] - state_dict["upper_band_position"]) > state_dict["upper_band_radius"]:
    #             self.current_state = StateMachine.GO_TO_UPPER_BAND_AFTER_TRIAL
    #             self.set_go_to_upper_band_after_trial(state_dict)

    #     elif self.current_state == StateMachine.IN_LOWER_BAND:
    #         if time() - state_dict["state_start_time"] >= state_dict["state_wait_time"]:
    #             self.current_state = StateMachine.GO_OUT_OF_LOWER_BAND
    #             self.set_go_out_of_lower_band(state_dict)
    #             self.prev_time = time()
    #         elif np.linalg.norm(state_dict["main_circle_position"] - state_dict["lower_band_position"]) > state_dict["lower_band_radius"]:
    #             self.current_state = StateMachine.GO_TO_LOWER_BAND_AFTER_TRIAL
    #             self.set_go_to_lower_band_after_trial(state_dict)

    #     #### WHEN TRIAL STARTS
    #     elif self.current_state == StateMachine.GO_OUT_OF_UPPER_BAND:
    #         state_dict["remaining_time"] -= time() - self.prev_time
    #         self.prev_time = time()

    #         if np.linalg.norm(state_dict["main_circle_position"] - state_dict["upper_band_position"]) >= state_dict["upper_band_radius"]:
    #             self.current_state = StateMachine.GO_TO_LOWER_BAND
    #             self.set_go_to_lower_band(state_dict)
    #             self.prev_time = time()

    #     elif self.current_state == StateMachine.GO_OUT_OF_LOWER_BAND:
    #         state_dict["remaining_time"] -= time() - self.prev_time
    #         self.prev_time = time()

    #         if np.linalg.norm(state_dict["main_circle_position"] - state_dict["lower_band_position"]) >= state_dict["lower_band_radius"]:
    #             self.current_state = StateMachine.GO_TO_UPPER_BAND
    #             self.set_go_to_upper_band(state_dict)
    #             self.prev_time = time()

    #     #### WHEN TRIAL IS IN PROGRESS
    #     elif self.current_state in {StateMachine.GO_TO_LOWER_BAND, StateMachine.GO_TO_UPPER_BAND}:
    #         state_dict["remaining_time"] -= time() - self.prev_time
    #         self.prev_time = time()

    #         if self.current_state == StateMachine.GO_TO_LOWER_BAND:
    #             maybe_next_state = StateMachine.STAY_IN_LOWER_BAND
    #             side = "right"
    #         else:
    #             maybe_next_state = StateMachine.STAY_IN_UPPER_BAND
    #             side = "left"
            
    #         if np.linalg.norm(state_dict["main_circle_position"] - state_dict[side + "_circle_position"]) < state_dict[side + "_circle_radius"]:
    #             self.current_state = maybe_next_state
    #             self.set_trial_termination(state_dict)

    #         elif (side == "right" and state_dict["main_circle_position"][0] > (state_dict[side + "_circle_position"][0] + state_dict[side + "_circle_radius"])) or \
    #              (side == "left" and state_dict["main_circle_position"][0] < (state_dict[side + "_circle_position"][0] - state_dict[side + "_circle_radius"])):
                
    #             if self._get_line_distance_to_center(self.prev_main_circle_position, state_dict["main_circle_position"], state_dict[side + "_circle_position"]) < state_dict[side + "_circle_radius"]:
    #                 self.set_unsuccessful_trial(state_dict, side)
    #             else:
    #                 self.set_unsuccessful_trial(state_dict, side)
                
    #             self.current_state = maybe_next_state
    #             self.set_trial_termination(state_dict)

    #     #### WHEN TRIAL ENDED, BUT WE DON'T WANT THE PARTICIPANT TO OVERSHOOT
    #     elif self.current_state in {StateMachine.STAY_IN_UPPER_BAND, StateMachine.STAY_IN_LOWER_BAND}:
    #         self.prev_time = time()
    #         trial_terminated = False

    #         if self.current_state == StateMachine.STAY_IN_LOWER_BAND:
    #             maybe_next_state = StateMachine.GO_TO_LOWER_BAND_AFTER_TRIAL
    #             side = "right"
    #         else:
    #             maybe_next_state = StateMachine.GO_TO_UPPER_BAND_AFTER_TRIAL
    #             side = "left"

    #         if time() - state_dict["state_start_time"] >= state_dict["state_wait_time"]:
    #             self.set_successful_trial(state_dict, side)
    #             trial_terminated = True

    #         elif np.linalg.norm(state_dict["main_circle_position"] - state_dict[side + "_circle_position"]) > (state_dict[side + "_circle_radius"] + state_dict["main_circle_radius"]):
    #             self.set_unsuccessful_trial(state_dict, side)
    #             trial_terminated = True

    #         if trial_terminated:
    #             self.current_state = maybe_next_state
    #             self.set_trial_termination(state_dict)

    #     elif self.current_state == StateMachine.PAUSE:
    #         if time() - state_dict["state_start_time"] >= state_dict["state_wait_time"]:
    #             self.current_state = StateMachine.GO_TO_MIDDLE_CIRCLE
    #             self.set_unpause(state_dict)
    #             self.set_waiting_for_start(state_dict)
    #             self.set_initial_screen(state_dict)
    #             self.set_start_experiment(state_dict)
    #             self.set_go_to_middle_circle(state_dict)

    #     #### WHEN TRIAL TERMINATES
    #     elif self.current_state == StateMachine.TRIAL_TERMINATION:
    #         if time() - state_dict["state_start_time"] >= state_dict["state_wait_time"]:
    #             self.current_state = StateMachine.GO_TO_START_CIRCLE
    #             self.set_go_to_start_circle(state_dict)
                
    #     elif self.current_state == StateMachine.EXIT:
    #         if state_dict["enter_pressed"]:
    #             continue_loop = False
                
    #     state_dict["remaining_time"] = float(np.clip(state_dict["remaining_time"], a_min=0, a_max=state_dict["total_time"]))
    #     state_dict["remaining_perc"] = state_dict["remaining_time"] / state_dict["total_time"]
    #     state_dict["current_state"] = self.reverse_state_lookup[self.current_state]
        
    #     if state_dict["remaining_time"] == 0 and \
    #        self.current_state not in {StateMachine.PAUSE, StateMachine.STAY_IN_LOWER_BAND, StateMachine.STAY_IN_UPPER_BAND, StateMachine.GO_TO_LOWER_BAND_AFTER_TRIAL, StateMachine.GO_TO_UPPER_BAND_AFTER_TRIAL}:
    #         if state_dict["block_idx"] < state_dict["total_blocks"] - 1:
    #             self.current_state = StateMachine.PAUSE
    #             self.set_pause(state_dict)
    #             state_dict["needs_update"] = True
    #         else:
    #             self.current_state = StateMachine.EXIT
    #             self.set_exit(state_dict)
            
    #     if "main_circle_position" in state_dict:
    #         self.prev_main_circle_position = np.copy(state_dict["main_circle_position"])
            
    #     return continue_loop, state_dict

    def _get_line_distance_to_center(self, p0, p1, c):
        # https://www.wikiwand.com/en/Distance_from_a_point_to_a_line#:~:text=horizontal%20line%20segment.-,Line%20defined%20by%20two%20points,-If%20the%20line

        numerator = np.abs((p1[0] - p0[0]) * (p0[1] - c[1]) - (p0[0] - c[0]) * (p1[1] - p0[1]))
        denominator = np.linalg.norm(p0 - p1)
        return numerator / denominator

    def set_waiting_for_start(self, state_dict):
        state_dict["state_start_time"] = None
        state_dict["main_text"] = "Waiting to start recording."
        state_dict["remaining_time"] = state_dict["total_time"]
        if state_dict["block_idx"] == 0:
            state_dict["score"] = 0
        state_dict["score_text"] = "Reward: %.2f€" % (state_dict["score"] / 20)
        
        state_dict["main_circle_color"] = Colors.BLACK
        state_dict["middle_circle_color"] = Colors.BLACK
        state_dict["upper_band_color"] = Colors.BLACK
        state_dict["lower_band_color"] = Colors.BLACK

    def set_initial_screen(self, state_dict):
        state_dict["state_start_time"] = None
        state_dict["main_text"] = "Press <Enter> when ready."

    def set_start_experiment(self, state_dict):
        state_dict["experiment_start"] = time()
        state_dict["main_circle_offset"] = (state_dict["marker_position"] - state_dict["cbos"])
        state_dict["show_progress_bar"] = state_dict["show_remaining_time"] = state_dict["show_score"] = True
        state_dict["main_text"] = ""
        state_dict["main_circle_color"] = Colors.LIGHT_GRAY

    def set_go_to_middle_circle(self, state_dict):
        state_dict["state_start_time"] = None
        state_dict["middle_circle_color"] = Colors.DARK_GRAY

    def set_in_middle_circle(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = 2.0 # s
        state_dict["middle_circle_color"] = Colors.BLUE

    def set_go_to_upper_band_after_trial(self, state_dict):
        state_dict["state_start_time"] = None
        state_dict["middle_circle_color"] = Colors.BLACK
        if state_dict["upper_band_color"] == Colors.BLACK:
            state_dict["upper_band_color"] = Colors.BLUE
        state_dict["lower_band_color"] = Colors.DARK_GRAY
    
    def set_go_to_lower_band_after_trial(self, state_dict):
        state_dict["state_start_time"] = None
        state_dict["middle_circle_color"] = Colors.BLACK
        state_dict["upper_band_color"] = Colors.DARK_GRAY
    
    def set_in_upper_band(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = np.random.uniform(*state_dict["state_wait_time_range"])

    def set_in_lower_band(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = np.random.uniform(*state_dict["state_wait_time_range"])
        
    def set_go_out_of_upper_band(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["upper_band_color"] = Colors.DARK_GRAY
        state_dict["lower_band_color"] = Colors.BLUE
    
    def set_go_out_of_lower_band(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["upper_band_color"] = Colors.BLUE
        state_dict["lower_band_color"] = Colors.DARK_GRAY

    def set_go_to_upper_band(self, state_dict):
        self.set_go_to_band(state_dict)
    
    def set_go_to_lower_band(self, state_dict):
        self.set_go_to_band(state_dict)

    def set_go_to_band(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["current_force_amplification"] = state_dict["force_amplification"]
        state_dict["current_force_decay"] = 0
        state_dict["perturbation_mode"] = "regular"
        
    def set_successful_trial(self, state_dict, side):
        state_dict["score"] += 1
        state_dict["score_text"] = "Reward: %.2f€" % (state_dict["score"] / 20)
        state_dict[side + "_circle_color"] = Colors.DARK_GREEN
        
    def set_unsuccessful_trial(self, state_dict, side):
        state_dict[side + "_circle_color"] = Colors.RED
        
    def set_trial_termination(self, state_dict):        
        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = 0.5
        # state_dict["current_force_amplification"] = 0
        state_dict["current_force_decay"] = state_dict["force_amplification"] / 100

    def set_pause(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = state_dict["pause_duration"]
        state_dict["current_force_amplification"] = 0
        state_dict["main_text"] = "Experiment paused for %d seconds" % state_dict["pause_duration"]

    def set_unpause(self, state_dict):
        state_dict["main_text"] = ""

    def set_exit(self, state_dict):
        state_dict["main_circle_color"] = Colors.BLACK
        state_dict["upper_band_color"] = Colors.BLACK
        state_dict["lower_band_color"] = Colors.BLACK
        
        state_dict["current_force_amplification"] = 0
        state_dict["show_progress_bar"] = state_dict["show_remaining_time"] = state_dict["show_score"] = False
        
        state_dict["main_text"] = "Press <Enter> to exit."