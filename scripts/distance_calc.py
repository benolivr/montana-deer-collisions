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
lixels = gpd.read_file('/home/ben/gds_data/project1/MT_wvc_network_lixels_binned.gpkg', layer='network_kde_classified')
flowlines = gpd.read_file('/home/ben/gds_data/project1/MT_flowlines_duckdb.gpkg')
waterbodies = gpd.read_file('/home/ben/gds_data/project1/MT_NHD_waterbodies.gpkg')

# 2. Harmonize all layers to EPSG:6514
print("Harmonizing projections to EPSG:6514...")
if lixels.crs != TARGET_CRS:
    lixels = lixels.to_crs(TARGET_CRS)

if flowlines.crs != TARGET_CRS:
    print("  -> Reprojecting flowlines...")
    flowlines = flowlines.to_crs(TARGET_CRS)

if waterbodies.crs != TARGET_CRS:
    print("  -> Reprojecting waterbodies...")
    waterbodies = waterbodies.to_crs(TARGET_CRS)

# 3. Combine water features
print("Combining water features...")
water_combined = pd.concat([
    flowlines[['geometry']], 
    waterbodies[['geometry']]
], ignore_index=True)

# Clean up empty or invalid geometries
water_combined = water_combined[~water_combined.geometry.is_empty & water_combined.geometry.is_valid]
water_geoms = water_combined.geometry.values

print(f"Building spatial index for {len(water_geoms):,} water features...")
tree = STRtree(water_geoms)

# 4. Extract lixel midpoints
lixel_midpoints = lixels.geometry.centroid.values
n_lixels = len(lixel_midpoints)

# 5. Calculate distances in chunks with tqdm
print(f"Calculating nearest water distance for {n_lixels:,} lixels...")
chunk_size = 50000
distances = np.empty(n_lixels, dtype=np.float32)

for i in tqdm(range(0, n_lixels, chunk_size), desc="Distance to Water"):
    chunk = lixel_midpoints[i : i + chunk_size]
    
    # tree.nearest() returns a clean 1D array of indices
    nearest_idx = tree.nearest(chunk)
    
    # Calculate exact distance from midpoint to nearest water line/polygon
    chunk_dists = shapely.distance(chunk, water_geoms[nearest_idx])
    distances[i : i + len(chunk)] = chunk_dists

# 6. Assign distance back to lixels
lixels['dist_to_water_m'] = distances

# 7. Save output
output_path = '/home/ben/gds_data/project1/MT_wvc_lixels_with_water.gpkg'
print(f"Saving to {output_path}...")
lixels.to_file(output_path, layer='lixels_water_metrics', driver='GPKG')
print("Complete! Water proximity analysis dataset is ready.")