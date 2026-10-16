import geopandas as gpd
import numpy as np
import fiona
from shapely.ops import substring
from shapely.geometry import LineString
from scipy.spatial import KDTree
from tqdm import tqdm
import shapely
from shapely.geometry import LineString
import warnings

warnings.filterwarnings("ignore")

# ==========================================
# 1. CONFIGURATION & FILE PATHS
# ==========================================
ROADS_GDB_PATH = '/home/ben/gds_data/project1/MT-roads/TransportationFramework.gdb'
CRASHES_GPKG_PATH = '/home/ben/gds_data/project1/montana_deer_collisions_trimmed.gpkg'
OUTPUT_GPKG_PATH = '/home/ben/gds_data/project1/montana_wvc_network_lixels_160m.gpkg'

LIXEL_SIZE = 160.0        # 160 meters (~0.1 mile)
BANDWIDTH = 5000.0        # 5 km search bandwidth for deer movement
SIGMA = BANDWIDTH / 2.0   # Gaussian standard deviation
MAX_SNAP_DIST = 500.0     # Max distance (meters) to snap a crash to a road

# ==========================================
# 2. LOAD & HARMONIZE PROJECTIONS
# ==========================================
print("Loading road network...")
# Read first layer of GDB if layer name isn't specified
road_layers = fiona.listlayers(ROADS_GDB_PATH)
roads_gdf = gpd.read_file(ROADS_GDB_PATH, layer=road_layers[0])

print("Loading collision records...")
crashes_gdf = gpd.read_file(CRASHES_GPKG_PATH, layer='individual_crashes')

# Tell the type checker that roads_gdf definitely has a valid CRS
assert roads_gdf.crs is not None, "Roads dataset is missing a CRS!"

if crashes_gdf.crs != roads_gdf.crs:
    print(f"Reprojecting crashes to {roads_gdf.crs}...")
    crashes_gdf = crashes_gdf.to_crs(roads_gdf.crs)

target_crs = roads_gdf.crs

# Explode multipart lines into individual continuous LineStrings
print("Standardizing road geometries...")
roads_gdf = roads_gdf.explode(index_parts=False)
roads_gdf = roads_gdf[roads_gdf.geometry.geom_type == 'LineString']

# ==========================================
# 3. DISCRETIZE ROADS INTO 160M LIXELS
# ==========================================
print(f"\nSlicing roads into {LIXEL_SIZE}m lixels...")
lixel_geoms = []
lixel_midpoints = []

# Make sure LineString is imported from shapely.geometry
from shapely.geometry import LineString

# ==========================================
# 3. DISCRETIZE ROADS INTO 160M LIXELS
# ==========================================
print(f"\nSlicing roads into {LIXEL_SIZE}m lixels...")
lixel_geoms = []
lixel_midpoints = []

for geom in tqdm(roads_gdf.geometry, desc="Generating Lixels"):
    # Type-narrowing check for Pylance:
    if not isinstance(geom, LineString):
        continue
    
    total_len = geom.length
    if total_len <= 0:
        continue
    
    if total_len < LIXEL_SIZE:
        # Keep short road connectors as-is
        lixel_geoms.append(geom)
        mid_pt = geom.interpolate(total_len / 2.0)
        lixel_midpoints.append((mid_pt.x, mid_pt.y))
    else:
        # Slice into uniform 160m increments
        distances = np.arange(0, total_len, LIXEL_SIZE)
        for start_dist in distances:
            end_dist = min(start_dist + LIXEL_SIZE, total_len)
            segment = substring(geom, start_dist, end_dist)
            
            if not segment.is_empty:
                lixel_geoms.append(segment)
                mid_pt = geom.interpolate((start_dist + end_dist) / 2.0)
                lixel_midpoints.append((mid_pt.x, mid_pt.y))

n_lixels = len(lixel_geoms)
lixel_midpoints = np.array(lixel_midpoints, dtype=np.float32)
print(f"Created {n_lixels:,} lixels across Montana.")

# ==========================================
# 4. SPATIAL SNAP CRASHES VIA KD-TREE
# ==========================================
print("\nBuilding KD-Tree for spatial snapping...")
lixel_tree = KDTree(lixel_midpoints)

# Directly extracts an (N, 2) NumPy array of [[x, y], [x, y], ...]
crash_coords = shapely.get_coordinates(crashes_gdf.geometry).astype(np.float32)

print(f"Snapping {len(crash_coords):,} crashes to nearest lixels...")
distances, nearest_lixel_idx = lixel_tree.query(crash_coords)

# Filter out crashes that are too far from any mapped road (GPS/Milepost errors)
valid_mask = distances <= MAX_SNAP_DIST
valid_snaps = nearest_lixel_idx[valid_mask]
dropped = len(crash_coords) - np.sum(valid_mask)
print(f"Successfully snapped {len(valid_snaps):,} crashes ({dropped} dropped > {MAX_SNAP_DIST}m away).")

# Count how many carcasses landed on each lixel
crash_counts = np.bincount(valid_snaps, minlength=n_lixels)

# Identify "hot" lixels that actually have crashes on them
active_lixel_indices = np.where(crash_counts > 0)[0]
active_coords = lixel_midpoints[active_lixel_indices]
active_weights = crash_counts[active_lixel_indices].astype(np.float32)

print(f"{len(active_lixel_indices):,} lixels directly contain carcass pickups.")

# ==========================================
# 5. CALCULATE 1D NETWORK GAUSSIAN KDE
# ==========================================
print(f"\nEvaluating Network KDE (Bandwidth = {BANDWIDTH}m, Sigma = {SIGMA}m)...")
# Build KD-tree of only crash locations for rapid radius queries
active_tree = KDTree(active_coords)

# Find all crash clusters within 5km of each lixel
neighbor_groups = active_tree.query_ball_point(lixel_midpoints, r=BANDWIDTH)

densities = np.zeros(n_lixels, dtype=np.float32)
norm_factor = 1.0 / (SIGMA * np.sqrt(2.0 * np.pi))

for i, neighbors in enumerate(tqdm(neighbor_groups, desc="Calculating NetKDE")):
    if len(neighbors) > 0:
        # Distance from this lixel midpoint to all neighboring crash-bearing lixels
        dists = np.linalg.norm(lixel_midpoints[i] - active_coords[neighbors], axis=1)
        weights = active_weights[neighbors]
        
        # 1D Gaussian kernel summation
        kernel_vals = weights * np.exp(-0.5 * (dists / SIGMA) ** 2) * norm_factor
        densities[i] = np.sum(kernel_vals)

# ==========================================
# 6. EXPORT TO GEOPACKAGE
# ==========================================
print("\nAssembling GeoDataFrame...")
lixel_gdf = gpd.GeoDataFrame({
    'lixel_id': np.arange(n_lixels, dtype=np.int32),
    'crash_count': crash_counts.astype(np.int16),
    'density': densities,
    'geometry': lixel_geoms
}, crs=target_crs)

print(f"Writing to {OUTPUT_GPKG_PATH}...")
lixel_gdf.to_file(OUTPUT_GPKG_PATH, layer='network_kde_160m', driver='GPKG')
print("Complete! Clean vector network KDE generated.")