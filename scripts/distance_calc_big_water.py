import geopandas as gpd
import pandas as pd
import numpy as np
import shapely
from shapely import STRtree
from tqdm import tqdm
import warnings

warnings.filterwarnings("ignore")

TARGET_CRS = "EPSG:6514"

# 1. Load data
print("Loading layers...")
lixels = gpd.read_file('/home/ben/gds_data/project1/MT_wvc_network_lixels_binned_99.gpkg', layer='network_kde_classified')
flowlines = gpd.read_file('/home/ben/gds_data/project1/MT_flowlines_duckdb.gpkg')
waterbodies = gpd.read_file('/home/ben/gds_data/project1/MT_NHD_waterbodies.gpkg')

# 2. Harmonize projections
print("Harmonizing projections to EPSG:6514...")
if lixels.crs != TARGET_CRS:
    lixels = lixels.to_crs(TARGET_CRS)
if flowlines.crs != TARGET_CRS:
    flowlines = flowlines.to_crs(TARGET_CRS)
if waterbodies.crs != TARGET_CRS:
    waterbodies = waterbodies.to_crs(TARGET_CRS)

# 3. FILTER FOR YEAR-ROUND (PERENNIAL) WATER
print("\nApplying perennial filters...")
initial_flows = len(flowlines)
initial_wbs = len(waterbodies)

# Flowlines (3DHP): Keep named streams or established tributaries (drops dry coulees/ditches)
# If 'gnisidlabel' or 'streamorder' exist, use them:
if 'gnisidlabel' in flowlines.columns:
    flowlines_perennial = flowlines[flowlines['gnisidlabel'].notna() & (flowlines['gnisidlabel'] != '')]
elif 'streamorder' in flowlines.columns:
    flowlines_perennial = flowlines[flowlines['streamorder'] >= 2]
else:
    flowlines_perennial = flowlines

# Waterbodies (NHD): Keep perennial lakes and permanent reservoirs
perennial_fcodes = [39004, 39009, 43600, 43613, 43615, 43618, 43621]
if 'FCode' in waterbodies.columns:
    waterbodies_perennial = waterbodies[waterbodies['FCode'].isin(perennial_fcodes)]
else:
    waterbodies_perennial = waterbodies

print(f"  -> Flowlines reduced from {initial_flows:,} to {len(flowlines_perennial):,} named/perennial rivers.")
print(f"  -> Waterbodies reduced from {initial_wbs:,} to {len(waterbodies_perennial):,} permanent lakes/reservoirs.")

# 4. Combine geometries
print("\nCombining perennial water features...")
water_combined = pd.concat([
    flowlines_perennial[['geometry']], 
    waterbodies_perennial[['geometry']]
], ignore_index=True)

water_combined = water_combined[~water_combined.geometry.is_empty & water_combined.geometry.is_valid]
water_geoms = water_combined.geometry.values

print(f"Building spatial index for {len(water_geoms):,} perennial features...")
tree = STRtree(water_geoms)

# 5. Extract lixel midpoints & calculate distances
lixel_midpoints = lixels.geometry.centroid.values
n_lixels = len(lixel_midpoints)

print(f"Calculating nearest perennial water distance for {n_lixels:,} lixels...")
chunk_size = 50000
distances = np.empty(n_lixels, dtype=np.float32)

for i in tqdm(range(0, n_lixels, chunk_size), desc="Perennial Distance"):
    chunk = lixel_midpoints[i : i + chunk_size]
    nearest_idx = tree.nearest(chunk)
    distances[i : i + len(chunk)] = shapely.distance(chunk, water_geoms[nearest_idx])

# 6. Save updated distance
lixels['dist_to_perennial_water_m'] = distances
output_path = 'montana_wvc_lixels_perennial_water_99.gpkg'
print(f"\nSaving to {output_path}...")
lixels.to_file(output_path, layer='lixels_perennial_metrics', driver='GPKG')
print("Complete! Recalculated against true year-round water.")