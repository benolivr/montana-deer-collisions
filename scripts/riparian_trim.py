# import geopandas as gpd
# from shapely.geometry import box

# # Your validated bounding box
# bbox = box(100000, 10000, 1100000, 560000)
# gdb_path = '/home/ben/gds_data/project1/Montana_WetlandRiparian_20251022.gdb'
# output_gpkg = '/home/ben/gds_data/project1/all-riparian.gpkg'

# print("Extracting Sun River corridor features...")
# corridor_df = gpd.read_file(gdb_path, layer='MT_WetlandRiparian_2025', bbox=bbox)

# # 1. River Channel Polygons (787 features)
# river_channel = corridor_df[corridor_df['SYSTEM'] == 'R'].copy()

# # 2. Riparian Habitat Polygons (635 features)
# riparian_canopy = corridor_df[corridor_df['SYSTEM'] == 'Rp'].copy()

# print(f"Saving {len(river_channel)} river channel polygons...")
# river_channel.to_file(output_gpkg, layer='sun_river_channel', driver='GPKG')

# print(f"Saving {len(riparian_canopy)} riparian vegetation polygons...")
# riparian_canopy.to_file(output_gpkg, layer='sun_river_riparian_canopy', driver='GPKG')

# print("Complete! Re-load layers in QGIS.")


import duckdb

con = duckdb.connect()
con.execute("INSTALL spatial; LOAD spatial;")
con.execute("PRAGMA enable_progress_bar;")

gdb_path = '/home/ben/gds_data/project1/Montana_WetlandRiparian_20251022.gdb'
output_gpkg = '/home/ben/gds_data/project1/all-riparian.gpkg'

print("Extracting statewide riparian vegetation via DuckDB...")

query = f"""
    COPY (
        SELECT * EXCLUDE (OBJECTID)
        FROM st_read('{gdb_path}', layer='MT_WetlandRiparian_2025')
        WHERE SYSTEM = 'Rp'
    ) TO '{output_gpkg}' WITH (FORMAT GDAL, DRIVER 'GPKG');
"""

con.execute(query)
print(f"Finished! Created {output_gpkg}")