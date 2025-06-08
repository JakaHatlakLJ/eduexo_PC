import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import UnivariateSpline
import re
import pandas as pd

# --- Read data from CSV ---
df = pd.read_csv(r'C:\Users\anjaz\OneDrive\Desktop\JAKA\Eduexo_PC\a.csv', header=None)  # adjust filename and header as necessary
a = df[0].astype(str).tolist()  # assuming data is in the first column

# --- Step 1: Clean malformed values ---
valid_number_regex = re.compile(r"^-?\d+(\.\d+)?$")
cleaned = [float(val) for val in a if valid_number_regex.match(val.strip())]

# --- Step 2: Convert to numpy array ---
data = np.array(cleaned)

# --- Step 3: Local outlier removal ---
def remove_local_outliers(data, window_size=5, threshold=3.5):
    from scipy.stats import median_abs_deviation

    filtered = data.copy()
    half_win = window_size // 2

    for i in range(half_win, len(data) - half_win):
        window = data[i - half_win:i + half_win + 1]
        median = np.median(window)
        mad = median_abs_deviation(window)
        
        if mad == 0:
            continue

        if abs(data[i] - median) > threshold * mad:
            filtered[i] = np.nan

    return filtered

filtered_data = remove_local_outliers(data, window_size=10, threshold=5)

# --- Step 4: Fit spline ---
x = np.arange(len(filtered_data))
mask = ~np.isnan(filtered_data)
x_clean = x[mask]
y_clean = filtered_data[mask]

spline = UnivariateSpline(x_clean, y_clean, s=100)
y_spline = spline(x)

# --- Step 5: Plot ---
plt.figure(figsize=(12, 5))
plt.plot(y_spline, label="Spline Fit", linewidth=2.5)
plt.title("Spline Fitting After Local Outlier Removal")
plt.legend()
plt.grid(True)
plt.show()
