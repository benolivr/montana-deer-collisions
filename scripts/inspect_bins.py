import geopandas as gpd
import pandas as pd
import numpy as np

print("Loading dataset...")
# Load the latest perennial file
gpkg_path = '/home/ben/gds_data/project1/MT_wvc_lixels_perennial_water.gpkg'
lixels = gpd.read_file(gpkg_path)

# Automatically identify the distance column
dist_col = 'dist_to_perennial_water_m' if 'dist_to_perennial_water_m' in lixels.columns else 'dist_to_water_m'

# Define the exact bins from your plot
bins = [0, 50, 100, 250, 500, 1000, 2500, 5000, np.inf]
labels = ['0-50m', '50-100m', '100-250m', '250-500m', '500-1km', '1-2.5km', '2.5-5km', '>5km']

lixels['dist_band'] = pd.cut(lixels[dist_col], bins=bins, labels=labels, right=False)

# Group and calculate the numbers
summary = lixels.groupby('dist_band', observed=False).agg(
    total_crashes=('crash_count', 'sum'),
    lixel_count=('lixel_id', 'count')
).reset_index()

summary['road_length_km'] = (summary['lixel_count'] * 0.160).round(1)
summary['pct_of_roads'] = ((summary['road_length_km'] / summary['road_length_km'].sum()) * 100).round(2)
summary['crashes_per_km'] = (summary['total_crashes'] / summary['road_length_km']).round(3)

# Display formatted table
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
print("\n" + "="*70)
print("             RIPARIAN DISTANCE BAND BREAKDOWN")
print("="*70)
print(summary.to_string(index=False))
print("="*70)