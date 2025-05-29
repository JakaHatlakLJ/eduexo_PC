import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv(r"C:\Users\anjaz\OneDrive\Desktop\JAKA\Eduexo_PC\analysis\experiment_results\participant_001\experiment_data_09.tsv", sep="\t")

# Create a figure with two subplots
fig, axs = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

# Plot Current Torque
axs[0].plot(df['current_torque'], label='Current Torque', color='blue')
axs[0].set_ylabel('Torque')
axs[0].set_title('Current Torque Over Time')
axs[0].grid(True)
axs[0].legend()

# Plot Demanded Torque
axs[1].plot(df['demanded_torque'], label='Demanded Torque', color='green')
axs[1].set_xlabel('Index')
axs[1].set_ylabel('Torque')
axs[1].set_title('Demanded Torque Over Time')
axs[1].grid(True)
axs[1].legend()

plt.tight_layout()
plt.show()
