import os
import numpy as np
import json
import random

class Logger:

    def __init__(self, results_path, participant_id, no_log):
        self.results_path = results_path

        self.participant_id = participant_id
        assert isinstance(self.participant_id, int), "Participant ID has to be an integer!"

        self.participant_folder = f"participant_{self.participant_id:03d}"
        self.no_log = no_log
        self.trajectory_data_exists = None

        if not self.no_log:
            os.makedirs(os.path.join(self.results_path, self.participant_folder), exist_ok=True)
            self.data_exists = False

        self.data_dict = {}
        self.data_dict["current_torque"] = 0
        self.data_dict["demanded_torque"] = 0
        self.data_dict["current_position"] = 0
        self.data_dict["current_velocity"] = 0
        self.data_dict["event_id"] = 0
        self.data_dict["event_type"] = 0
        self.data_dict["timestamp"] = 0
        self.data_dict["prediction"] = 0

    def create_file(self):
        self.column_names = []
        self.original_state_dict_keys = set(self.data_dict.keys())
        sorted_keys = sorted(self.data_dict.keys())
        for key in sorted_keys:
            if isinstance(self.data_dict[key], int) or isinstance(self.data_dict[key], float) or isinstance(self.data_dict[key], str) or self.data_dict[key] is None:
                self.column_names.append(key)
            elif isinstance(self.data_dict[key], list) or isinstance(self.data_dict[key], np.ndarray) or isinstance(self.data_dict[key], tuple):
                self.column_names += [key + "."+str(idx) for idx in range(len(self.data_dict[key]))]
            else:
                print("Unrecognized data type:", type(self.data_dict[key]), self.data_dict[key], key)

        file_idx = len([filename for filename in os.listdir(os.path.join(self.results_path, self.participant_folder)) if filename.startswith("experiment_data")])
        file_idx = f'{file_idx:02d}'

        self.data_file = open(os.path.join(self.results_path, self.participant_folder, f'experiment_data_{file_idx}.tsv'),"w")
        self.data_file.write("\t".join(self.column_names) + "\n")
        self.data_exists = True

    def save_datapoint(self):
        if self.no_log:
            return
        
        if not self.data_exists:
            self.create_file()

        assert len(self.original_state_dict_keys) == len(self.data_dict), f"Mismatch in the number of original keys and the number of keys in the current self.data_dict.\n{set(self.data_dict.keys()) - self.original_state_dict_keys}"

        datapoint_to_write = []
        for column_name in self.column_names:
            column_split = column_name.split(".")

            current = self.data_dict
            for column_substring in column_split:
                if column_substring.isdigit():
                    column_substring = int(column_substring)
                current = current[column_substring]
            
            datapoint_to_write.append(str(current))

        self.data_file.write("\t".join(datapoint_to_write) + "\n")

    def save_experiment_config(self, experiment_config, filename=None):
        if not self.no_log:
            if filename is None:
                file_idx = len([filename for filename in os.listdir(os.path.join(self.results_path, self.participant_folder)) if filename.startswith("experiment_config")])
                filename = "experiment_config" + f"{file_idx:02d}" + ".json"
            else:
                assert filename.endswith(".json")
            json.dump(experiment_config, open(os.path.join(self.results_path, self.participant_folder, filename),"w"), indent=4, sort_keys=True)

    def save_data_dict(self, state_dict, reset=False):
        if reset == True:
            self.data_dict = {key:0 for key in self.data_dict}
        
        self.data_dict["current_torque"] = state_dict["current_torque"]
        self.data_dict["demanded_torque"] = state_dict["current_torque"] + round(random.uniform(-0.5,0.5), 3)
        self.data_dict["current_position"] = state_dict["current_position"]
        self.data_dict["current_velocity"] = state_dict["current_velocity"]
        self.data_dict["event_id"] = state_dict["event_id"]
        self.data_dict["event_type"] = state_dict["event_type"]
        self.data_dict["timestamp"] = state_dict["timestamp"]
        self.data_dict["prediction"] = state_dict["event_type"]

        self.save_datapoint()

        # print(self.data_dict)

    def close(self):
        self.data_file.close()
