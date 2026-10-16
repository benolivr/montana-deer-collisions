import matplotlib as mpl
import matplotlib.colors as mcolors
import numpy as np

# Generate 8 exact intervals
intervals = np.linspace(0, 1, 8)
turbo_cmap = mpl.colormaps['turbo']

for val in intervals:
    rgba = turbo_cmap(val)
    hex_code = mcolors.to_hex(rgba).upper()
    rgb = tuple(int(255 * c) for c in rgba[:3])
    print(f"{hex_code}", end=", ")
    
