import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

print("Loading data...")
lixels = gpd.read_file('/home/ben/gds_data/project1/MT_wvc_lixels_perennial_water.gpkg', layer='lixels_perennial_metrics')
roads = gpd.read_file(
    '/home/ben/gds_data/project1/MT-roads/TransportationFramework.gdb', 
    layer='RoadCenterLine',
    columns=['RoadClass', 'geometry']
)

# Harmonize CRS
roads = roads.to_crs(lixels.crs)

print("Attaching RoadClass to lixels...")
lixel_pts = lixels[['lixel_id', 'geometry']].copy()
lixel_pts['geometry'] = lixel_pts.geometry.centroid

joined = gpd.sjoin_nearest(
    lixel_pts, 
    roads[['RoadClass', 'geometry']], 
    how='left',
    max_distance=50
).drop_duplicates(subset=['lixel_id'])

lixels['RoadClass'] = joined['RoadClass'].values

# =============================================================
# THE FILTER: Keep ONLY Primary & Secondary Highways (+ Ramps)
# =============================================================
highways = lixels[lixels['RoadClass'].isin(['Primary', 'Secondary', 'Ramp'])].copy()
print(f"Filtered from {len(lixels):,} lixels down to {len(highways):,} highway lixels.")

tier_order = [
    "0. No Collisions",
    "1. Low",
    "2. Moderate",
    "3. High",
    "4. Very High",
    "5. Critical Hotspot"
]

palette = ['#30123b', '#3e9bfe', '#46f884', '#e1dd37', '#f05b12', '#7a0403']

# -------------------------------------------------------------
# 1. REVISED VIEW 2: Highway Boxplot
# -------------------------------------------------------------
plt.figure(figsize=(12, 6))
sns.set_theme(style="whitegrid")

sns.boxplot(
    data=highways, 
    x='hazard_tier', 
    y='dist_to_perennial_water_m', 
    order=tier_order,
    palette=palette,
    showfliers=False,
    showmeans=True,
    meanprops={"marker":"o", "markerfacecolor":"white", "markeredgecolor":"black", "markersize": 8},
    width=0.6,
    linewidth=1.2
)

plt.title("Highway Proximity to Riparian Features Across Collision Hazard Tiers (Primary & Secondary Routes)", fontsize=13, fontweight='bold')
plt.xlabel("Modeled Collision Hazard Tier", fontsize=11)
plt.ylabel("Distance to Nearest Water (Meters)", fontsize=11)
plt.ylim(0, 1200)
plt.tight_layout()
plt.savefig('python_view_2_highways_boxplot_perennial_water.png', dpi=300)
print("Saved python_view_2_highways_boxplot_perennial_water.png")

# -------------------------------------------------------------
# 2. REVISED VIEW 2B: Highway Riparian Buffer Exposure (<250m)
# -------------------------------------------------------------
highways['is_riparian_250'] = highways['dist_to_perennial_water_m'] <= 250
exposure = highways.groupby('hazard_tier', observed=False)['is_riparian_250'].mean() * 100
exposure = exposure.reindex(tier_order).reset_index()

plt.figure(figsize=(10, 5))
sns.barplot(
    data=exposure,
    x='hazard_tier',
    y='is_riparian_250',
    palette=palette
)

plt.title("Proportion of Highway Segments Within 250m Riparian Buffer", fontsize=13, fontweight='bold')
plt.xlabel("Collision Hazard Tier", fontsize=11)
plt.ylabel("% of Highway Segments within 250m of Water", fontsize=11)
plt.ylim(0, 100)
plt.tight_layout()
plt.savefig('python_view_2_highways_exposure_perennial_water.png', dpi=300)
print("Saved python_view_2_highways_exposure_perennial_water.png")