import os
import json

import numpy as np


class Logger:
    
    def __init__(self, results_path, participant_id, no_log):
        self.results_path = results_path
        
        self.participant_id = participant_id
        assert isinstance(self.participant_id, int), "Participant ID has to be an integer!"
        
        self.participant_folder = "participant_%03d" % self.participant_id
        self.no_log = no_log
        self.trajectory_data_exists = None
        
        if not self.no_log:
            os.makedirs(self.results_path, exist_ok=True)
            os.makedirs(os.path.join(self.results_path, self.participant_folder), exist_ok=True)
            self.trajectory_data_exists = False
            
            
    def create_trajectory_file(self, state_dict):
        self.column_names = []
        self.original_state_dict_keys = set(state_dict.keys())
        sorted_keys = sorted(state_dict.keys())
        for key in sorted_keys:
            if isinstance(state_dict[key], int) or isinstance(state_dict[key], float) or isinstance(state_dict[key], str) or state_dict[key] is None:
                self.column_names.append(key)
            elif isinstance(state_dict[key], list) or isinstance(state_dict[key], np.ndarray) or isinstance(state_dict[key], tuple):
                self.column_names += [key + "." + str(idx) for idx in range(len(state_dict[key]))]
            else:
                print("Unrecognized data type:", type(state_dict[key]), state_dict[key], key)
    
        file_idx = len([filename for filename in os.listdir(os.path.join(self.results_path, self.participant_folder)) if filename.startswith("experiment_data")])
        file_idx = str("%02d" % file_idx)

        self.trajectory_file = open(os.path.join(self.results_path, self.participant_folder, f"experiment_data_{file_idx}.tsv"), "w")
        self.trajectory_file.write("\t".join(self.column_names) + "\n")
        self.trajectory_data_exists = True
    
    def save_datapoint(self, state_dict):
        if self.no_log:
            return
        
        if not self.trajectory_data_exists:
            self.create_trajectory_file(state_dict)
            
        assert len(self.original_state_dict_keys) == len(state_dict), f"Mismatch in the number of original keys and the number of keys in the current state_dict.\n{set(state_dict.keys()) - self.original_state_dict_keys}"
        
        datapoint_to_write = []
        for column_name in self.column_names:
            column_split = column_name.split(".")
            
            current = state_dict
            for column_substring in column_split:
                if column_substring.isdigit():
                    column_substring = int(column_substring)
                current = current[column_substring]
                
            datapoint_to_write.append(str(current))
        
        self.trajectory_file.write("\t".join(datapoint_to_write) + "\n")
            
    def save_experiment_config(self, experiment_config, filename=None):
        if not self.no_log:
            if filename is None:
                file_idx = len([filename for filename in os.listdir(os.path.join(self.results_path, self.participant_folder)) if filename.startswith("experiment_config")])
                filename = "experiment_config_" + str("%02d" % file_idx) + ".json"
            else:
                assert filename.endswith(".json")
            json.dump(experiment_config, open(os.path.join(self.results_path, self.participant_folder, filename), "w"), indent=4, sort_keys=True)
            
    def save_com(self, com_dict):
        if not self.no_log:
            if os.path.exists(os.path.join(self.results_path, self.participant_folder, "participant_com.json")):
                print(f"Center of mass measurement for participant #{self.participant_id} already exists!")
                answer = input("Overwrite? (y)es, (n)o: ")
                if answer != "y":
                    exit()
                    
            json.dump(com_dict, open(os.path.join(self.results_path, self.participant_folder, "participant_com.json"), "w"), indent=4, sort_keys=True)
        
    def close(self):
        self.trajectory_file.close()