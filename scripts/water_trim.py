import duckdb

con = duckdb.connect()
con.execute("INSTALL spatial; LOAD spatial;")
con.execute("PRAGMA enable_progress_bar;")

print("Processing multithreaded spatial intersection for NHD Waterbodies...")

query = """
    COPY (
        SELECT nhd.* 
        FROM st_read('/home/ben/gds_data/project1/bad-water/NHDHv231_MT_gdb10_SPCNAD832011_20231227.gdb', layer='NHDWaterbody') AS nhd
        JOIN st_read('/home/ben/gds_data/project1/MT-border.gdb', layer='StateofMontana') AS mt
        
        -- Override the 3D compound CRS label so DuckDB knows it matches EPSG:6514
        ON ST_Intersects(
            ST_SetCRS(nhd.Shape, 'EPSG:6514'), 
            mt.SHAPE
        )
        
    ) TO '/home/ben/gds_data/project1/MT_NHD_waterbodies.gpkg' 
    WITH (FORMAT GDAL, DRIVER 'GPKG');
"""

con.execute(query)
print("Finished! NHD waterbodies clipped to Montana.")