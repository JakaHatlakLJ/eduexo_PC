import mne
import matplotlib.pyplot as plt
import numpy as np

# File path (update if needed)
EEG_FILE_PATH = r"C:\Users\anjaz\OneDrive\Desktop\preprocessed_ICA_eksperiment_annotated_9.set"

# Load the EEG data
print("Loading EEG data...")
raw = mne.io.read_raw_eeglab(EEG_FILE_PATH, preload=True)
raw.filter(1, 40)  # Apply bandpass filter (1-40 Hz) to remove noise

# Plot raw EEG data
raw.plot(scalings='auto', title="Raw EEG Data", duration=5, n_channels=10)

# Select a specific channel for detailed view
CHANNEL_NAME = "Fz"  # Change this to any valid channel
if CHANNEL_NAME in raw.ch_names:
    channel_idx = raw.ch_names.index(CHANNEL_NAME)
    eeg_data, times = raw[channel_idx, :]

    plt.figure(figsize=(10, 4))
    plt.plot(times, eeg_data[0], label=f"Channel: {CHANNEL_NAME}", color="blue")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude (µV)")
    plt.title(f"EEG Signal for {CHANNEL_NAME}")
    plt.legend()
    plt.show()
else:
    print(f"Channel '{CHANNEL_NAME}' not found in EEG data.")

# Extract and plot epochs if events are found
print("\nExtracting epochs...")
events, event_id = mne.events_from_annotations(raw)
if events.shape[0] > 0:
    epochs = mne.Epochs(raw, events, event_id, tmin=-0.2, tmax=0.8, baseline=None, preload=True)
    
    # Plot ERP (Event-Related Potential) for all channels
    epochs.average().plot()

    # Topographic map (brain heatmap)
    times_to_plot = [0.1, 0.2, 0.3]  # Select time points in seconds
    epochs.average().plot_topomap(times=times_to_plot, ch_type="eeg", scalings=1.0)
else:
    print("No events found. Skipping epoch-related plots.")

print("Visualization complete!")
