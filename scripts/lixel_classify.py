import geopandas as gpd
import numpy as np

print("Reading lixels...")
gdf = gpd.read_file('/home/ben/gds_data/project1/MT_wvc_network_lixels_160m.gpkg', layer='network_kde_160m')

# 1. Look ONLY at roads that actually have collisions/density
nonzero_density = gdf.loc[gdf['density'] > 0, 'density']

# 2. Compute percentiles (e.g., Top 50%, 75%, 90%, 95%, 99%)
p50, p75, p90, p95, p99 = np.percentile(nonzero_density, [50, 75, 90, 95, 99])

# 3. Bin the data into 6 clean classes (0 = No crashes, 5 = Extreme Hotspot)
conditions = [
    gdf['density'] == 0,
    (gdf['density'] > 0) & (gdf['density'] <= p50),
    (gdf['density'] > p50) & (gdf['density'] <= p75),
    (gdf['density'] > p75) & (gdf['density'] <= p90),
    (gdf['density'] > p90) & (gdf['density'] <= p99),
    gdf['density'] > p99
]

labels = [
    "0. No Collisions",
    "1. Low",
    "2. Moderate",
    "3. High",
    "4. Very High",
    "5. Critical Hotspot"
]

gdf['hazard_tier'] = np.select(conditions, labels, default="0. No Collisions")

print("Saving classified layer...")
gdf.to_file('/home/ben/gds_data/project1/MT_wvc_network_lixels_binned_99.gpkg', layer='network_kde_classified', driver='GPKG')
print("Done! Load into QGIS and use Categorized symbology.")