# make_master_lixels.py
import geopandas as gpd

print("Loading perennial lixels...")
lixels = gpd.read_file('/home/ben/gds_data/project1/montana_wvc_lixels_perennial_water_99.gpkg', layer='lixels_perennial_metrics')
if lixels.crs is None:
    raise ValueError("Lixels dataset is missing a CRS!")

print("Loading road classifications...")
roads = gpd.read_file(
    '/home/ben/gds_data/project1/MT-roads/TransportationFramework.gdb', 
    layer='RoadCenterLine',
    columns=['RoadClass', 'SpeedLimit', 'geometry']
).to_crs(lixels.crs)

print("Attaching RoadClass and SpeedLimit to lixels...")
lixel_pts = lixels[['lixel_id', 'geometry']].copy()
lixel_pts['geometry'] = lixel_pts.geometry.centroid

joined = gpd.sjoin_nearest(
    lixel_pts, 
    roads[['RoadClass', 'SpeedLimit', 'geometry']], 
    how='left',
    max_distance=50
).drop_duplicates(subset=['lixel_id'])

lixels['RoadClass'] = joined['RoadClass'].values
lixels['SpeedLimit'] = joined['SpeedLimit'].values

output_master = '/home/ben/gds_data/project1/MT_wvc_lixels_master_99.gpkg'
print(f"Saving permanent master dataset to {output_master}...")
lixels.to_file(output_master, layer='lixels_master', driver='GPKG')
print("Complete! Now you have RoadClass, SpeedLimit, density, and perennial water distance in one place.")