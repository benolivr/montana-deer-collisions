import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

palette = ['#30123b', '#3e9bfe', '#46f884', '#e1dd37', '#f05b12', '#7a0403']

tier_order = [
    "0. No Collisions",
    "1. Low",
    "2. Moderate",
    "3. High",
    "4. Very High",
    "5. Critical Hotspot"
]

# Load data
gdf = gpd.read_file('/home/ben/gds_data/project1/MT_wvc_lixels_perennial_water.gpkg', layer='lixels_perennial_metrics')

# -------------------------------------------------------------
# PYTHON VIEW 1: Normalized Collision Rate by Distance Band
# -------------------------------------------------------------
# Define realistic ecological distance bands
bins = [0, 50, 100, 250, 500, 1000, 2500, 5000, np.inf]
labels = ['0-50m', '50-100m', '100-250m', '250-500m', '500-1km', '1-2.5km', '2.5-5km', '>5km']

gdf['dist_band'] = pd.cut(gdf['dist_to_perennial_water_m'], bins=bins, labels=labels, right=False)

# Aggregate: Total crashes and Total road length (km) per band
band_summary = gdf.groupby('dist_band', observed=False).agg(
    total_crashes=('crash_count', 'sum'),
    lixel_count=('lixel_id', 'count')
).reset_index()

# Each lixel is 0.160 km
band_summary['road_length_km'] = band_summary['lixel_count'] * 0.160
band_summary['crashes_per_km'] = band_summary['total_crashes'] / band_summary['road_length_km']

# Plot View 1
plt.figure(figsize=(10, 6))
sns.set_theme(style="whitegrid")

ax = sns.barplot(
    data=band_summary, 
    x='dist_band', 
    y='crashes_per_km', 
    palette='Blues_r'
)

plt.title("Wildlife Collision Rate Normalized by Road Length vs. Riparian Distance", fontsize=14, fontweight='bold')
plt.xlabel("Distance to Nearest Waterbody / Flowline", fontsize=12)
plt.ylabel("Crashes per Kilometer of Road", fontsize=12)
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig('python_view_1_distance_decay_perennial_water.png', dpi=300)
print("Saved python_view_1_distance_decay_perennial_water.png")

# -------------------------------------------------------------
# FIXED VIEW 2: Clean Boxplot without Outlier Smear
# -------------------------------------------------------------
plt.figure(figsize=(12, 6))
sns.set_theme(style="whitegrid")

ax = sns.boxplot(
    data=gdf, 
    x='hazard_tier', 
    y='dist_to_perennial_water_m', 
    order=tier_order,            # <--- FIX: Forces correct numerical order
    palette=palette,
    showfliers=False,            # <--- FIX: Removes the 12,000 black dot smear!
    showmeans=True,
    meanprops={"marker":"o", "markerfacecolor":"white", "markeredgecolor":"black", "markersize": 8},
    width=0.6,
    linewidth=1.2
)

plt.title("Distance to Riparian Features by Collision Hazard Tier (Whiskers: 1.5x IQR)", fontsize=14, fontweight='bold')
plt.xlabel("Modeled Collision Hazard Tier", fontsize=12)
plt.ylabel("Distance to Nearest Water (Meters)", fontsize=12)
plt.ylim(0, 1000) # Zooms into the meaningful 0-1000m zone
plt.tight_layout()
plt.savefig('python_view_2_clean_boxplot_perennial_water.png', dpi=300)
print("Saved python_view_2_clean_boxplot_perennial_water.png")

gdf['is_riparian'] = gdf['dist_to_perennial_water_m'] <= 200

exposure = gdf.groupby('hazard_tier', observed=False)['is_riparian'].mean() * 100
exposure = exposure.reindex(tier_order).reset_index()

plt.figure(figsize=(10, 5))
sns.barplot(
    data=exposure,
    x='hazard_tier',
    y='is_riparian',
    palette=palette
)

plt.title("Proportion of Road Segments Within Riparian Buffer (<200m)", fontsize=14, fontweight='bold')
plt.xlabel("Collision Hazard Tier", fontsize=12)
plt.ylabel("% of Segments within 200m of Water", fontsize=12)
plt.ylim(0, 100)
plt.tight_layout()

plt.savefig('python_view_2_riparian_exposure_perennial_water.png', dpi=300)
print("Saved python_view_2_riparian_exposure_perennial_water.png")