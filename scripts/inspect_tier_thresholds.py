import geopandas as gpd
import pandas as pd
import numpy as np

# 1. Load data (we only read attributes, skipping geometry for speed)
file_path = '/home/ben/gds_data/project1/MT_wvc_lixels_perennial_water_99.gpkg'
layer_name = 'lixels_perennial_metrics'

print("Loading lixel metrics...")
# If pyogrio is installed, read attributes only for maximum speed
try:
    import pyogrio
    df = pyogrio.read_dataframe(file_path, layer=layer_name, columns=['hazard_tier', 'crash_count', 'density'])
except Exception:
    df = gpd.read_file(file_path, layer=layer_name, ignore_geometry=True)

# 2. Strict order of your hazard tiers
tier_order = [
    "No Collisions",
    "0-50th Percentile",
    "50-75th Percentile",
    "75-90th Percentile",
    "90-99th Percentile",
    ">99th Percentile"
]

# 3. Aggregate statistics per tier
summary = df.groupby('hazard_tier', observed=False).agg(
    total_segments=('crash_count', 'count'),
    min_crashes=('crash_count', 'min'),
    mean_crashes=('crash_count', 'mean'),
    max_crashes=('crash_count', 'max'),
    sum_crashes=('crash_count', 'sum'),
    min_density=('density', 'min'),
    max_density=('density', 'max')
).reindex(tier_order)

# Format for clean terminal printing
pd.set_option('display.float_format', lambda x: f'{x:,.4f}')
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

print("\n" + "="*85)
print("     HAZARD TIER THRESHOLDS: RAW CARCASS COUNTS vs. MODELED DENSITY")
print("="*85)
print(summary[['total_segments', 'min_crashes', 'mean_crashes', 'max_crashes', 'sum_crashes', 'min_density', 'max_density']])
print("="*85)

# Also check for Highways only (Primary & Secondary) if RoadClass exists:
if 'RoadClass' in df.columns:
    highways = df[df['RoadClass'].isin(['Primary', 'Secondary', 'Ramp'])]
    print("\n" + "="*85)
    print("     HIGHWAYS ONLY (PRIMARY & SECONDARY): CARCASS COUNTS BY TIER")
    print("="*85)
    hw_summary = highways.groupby('hazard_tier', observed=False).agg(
        total_segments=('crash_count', 'count'),
        min_crashes=('crash_count', 'min'),
        mean_crashes=('crash_count', 'mean'),
        max_crashes=('crash_count', 'max'),
        sum_crashes=('crash_count', 'sum')
    ).reindex(tier_order)
    print(hw_summary)
    print("="*85)