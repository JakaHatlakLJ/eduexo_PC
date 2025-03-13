# Eduexo Experiment (PC)

This project integrates a Brain-Machine Interface (BMI) to train a neural network for classifying human intentions during experiments. Participants are asked to think about moving their arm up or down, and the EXO device either aids or contradicts their movement. EEG signals are recorded during these tasks, which are later used to classify the participant's intentions. This setup allows for precise control and monitoring of the experiment and communication with both EXO and computer which reads 'Events stream' in real time.

## Prerequisites

- Python 3.x
- Git
- Visual Studio Code (recommended)
- Compatible hardware for data streaming (e.g., EXO device)
    - The EXO device must meet specific requirements for compatibility. Ensure that your device firmware is up-to-date and that it supports the necessary data streaming protocols. Refer to: [https://github.com/JakaHatlakLJ/eduexo_EEG]

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd Eduexo_PC
```

2. Install all requriements from `requirements.txt` in your environment:
```bash
pip install -r requirements.txt
```

## Project Hierarchy

The project directory is organized as follows. Once `experiment_do.py` is run for the first time with the default `experiment_config.json`, all subfolders will automatically be created and populated if not already.

```
Eduexo_PC/
├── main/                               # Main scripts
│   ├── experiment_do.py                # Run experiment
│   ├── experiment_interface.py         # Interface logic
│   ├── experiment_state_machine.py     # State machine
│   ├── experiment_logging.py           # Logging functions
│   ├── experiment_LSL.py               # LSL integration
│   └── experiment_config.json          # Configuration file
├── analysis/                           # Analysis scripts
│   ├── experiment_results/             # Results storage
│   ├── frequency_data/                 # Frequency data
│   └── jupyter/                        # Jupyter notebooks
│       └── control_frequency.ipynb     # Control frequency analysis
├── testing_&_debugging/                # Testing scripts
│   ├── LSL_inlet.py                    # LSL inlet
│   ├── LSL_outlet.py                   # LSL outlet
│   ├── LSL_parameter_sender.py         # Send parameters to EXO
│   ├── LSL_predictions_inlet.py        # Test predictions inlet
│   ├── LSL_read_events_stream.py       # Test events stream
│   └── LSL_synthetic_predictions.py    # Test real event decoding
├── requirements.txt                    # Dependencies
└── README.md                           # Documentation
```

## Setting Up the Experiment

Before running the `experiment_do.py` script, you need to follow these steps:

1. **Configure and setup EXO:**
    - Install all requirements on EXO and make sure you can run scripts on it.
    - Refer to: [https://github.com/JakaHatlakLJ/eduexo_EEG]

2. **Configure the Experiment:**
    - Open `experiment_config.json`.
    - Modify the configuration parameters as needed for your experiment.

## Running the Experiment

1. Once the setup is complete, you can run the experiment using the following command:
```sh
python experiment_do.py
```

2. Run `EXO_main.py` on EXO at the same time and follow the instructions. (If run for testing purposes you can additionaly use LSL_send_position.py on EXO)

3. If run with real decoding, another LSL stream of name "PredictionStream" is needed. For testing run /testing_&_debugging/LSL_synthetic_predictions.py in a seperate terminal to mimic the real decoder.

This will start the experiment based on the configurations prepared in the previous steps.

## Additional Information

- Refer to the docstrings and comments within each script for more detailed instructions and explanations.
- The `requirements.txt` file should contain all the necessary Python packages needed to run the project.

### `experiment_config.json` explanation

```json
{
    "experiment": {
        "number_of_trials": 200                        "Total number of assisted trials in the experiment.",
        "number_of_control_trials": 10                 "Number of control trials (without EXO active).",
        "state_wait_time_range": [1, 1]                "Range of times in WAIT state.",
        "imagination_time_range": [5, 5]               "Range of times for IMAGINATION phase.",
        "intention_time_range": [2, 3]                 "Range of times for INTENTION phase.",
        "trial_timeout": 3                             "Timeout duration for each trial.",
        "screen_width": 2000                           "Width of the display screen.",
        "screen_height": 1050                          "Height of the display screen.",
        "maximum_arm_position_deg": 165                "Maximum arm position in degrees. (straight arm is 180 deg)",
        "minimum_arm_position_deg": 55                 "Minimum arm position in degrees.",
        "data_stream_interval": 0.01                   "Interval for motor parameters streaming.",
        "synthetic_decoder": 1                         "Flag to choose decoder (1 for synthetic, 0 for real)",
        "synthetic_decoder_correct_percantage": 0.7    "Correct Execution percentage for synthetic decoder.",
        "save_data": 1                                 "Flag to save data (1 to save, 0 not to save).",
        "results_path":"./analysis/experiment_results" "Path to save experiment results.",
        "frequency_path":"./analysis/frequency_data"   "Path to save frequency data."
    },
    "participant": {
        "age": 22                                      "Age of the participant.",
        "id": 1                                        "ID of the participant.",
        "name":"Jaka"                                  "Name of the participant."
    }
}
```
### Additional Scripts:

   You can run other scripts for specific functionalities or testing as needed. For example, to test if "events_stream" is sending out correct data, use this in a seperate terminal:
   ```sh
   python LSL_read_events_stream.py
   ```
