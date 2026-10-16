import duckdb

con = duckdb.connect()
con.execute("INSTALL spatial; LOAD spatial;")

# Turn on the terminal progress bar
con.execute("PRAGMA enable_progress_bar;")

print("Processing multithreaded spatial intersection...")

query = """
    COPY (
        SELECT flowlines.* EXCLUDE (fid) 
        FROM st_read('/home/ben/gds_data/project1/US-water/3dhp_all_CONUS_20260112_GPKG.gpkg', layer='hydro_3dhp_all_flowline') AS flowlines
        JOIN st_read('/home/ben/gds_data/project1/MT-border.gdb', layer='StateofMontana') AS mt
        
        ON ST_Intersects(
            flowlines.shape, 
            ST_Transform(mt.SHAPE, 'EPSG:6514', 'EPSG:6350')
        )
        
    ) TO '/home/ben/gds_data/project1/MT_flowlines_duckdb.gpkg' 
    WITH (FORMAT GDAL, DRIVER 'GPKG');
"""

con.execute(query)
print("Finished! The flowlines have been clipped to Montana.")