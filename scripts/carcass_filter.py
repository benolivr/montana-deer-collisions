import pandas as pd
import geopandas as gpd

TARGET_CRS = "EPSG:32100"

# 1. Read your Excel file
file_path = '/home/ben/gds_data/project1/CarcassData2016-2025.xlsx'
df = pd.read_excel(file_path)

# 2. Clean the coordinate columns
# Strip commas and convert to float (in case Excel loaded them as text)
for col in ['SMS_X_CORD', 'SMS_Y_CORD']:
    if df[col].dtype == 'object':
        df[col] = df[col].astype(str).str.replace(',', '').astype(float)

# Drop any rows where coordinates are completely empty
df = df.dropna(subset=['SMS_X_CORD', 'SMS_Y_CORD'])

# 3. Filter out "INVALID COORDINATE"
# We keep rows where COMMENT_STR is empty/NaN, OR doesn't contain 'INVALID COORDINATE'
valid_coords = df['COMMENT_STR'].isna() | (
    ~df['COMMENT_STR'].astype(str).str.upper().str.contains('INVALID COORDINATE')
)
df = df[valid_coords]

# 4. Filter for ONLY Mule Deer and Whitetail Deer
# We use .str.contains to safely capture them even with prefixes like "5." or "6."
deer_filter = df['Animal Type'].astype(str).str.upper().str.contains('WHITETAIL DEER|MULE DEER')
df = df[deer_filter]

# (Optional Data Cleanup): Remove the leading numbers like "5. " so your legends look clean
df['Animal Type'] = df['Animal Type'].str.replace(r'^\d+\.\s*', '', regex=True)

# 5. Convert to GeoDataFrame
# We assign EPSG:32100 (Montana State Plane, Meters)
gdf = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df['SMS_X_CORD'], df['SMS_Y_CORD']),
    crs=TARGET_CRS
)

# 1. Load the Montana border
mt_border = gpd.read_file('/home/ben/gds_data/project1/MT-border.gdb', layer='StateofMontana')

# 2. Ensure both layers have the exact same projection.
# Some File Geodatabases do not preserve the CRS in the layer metadata.
if mt_border.crs is None:
    mt_border = mt_border.set_crs(TARGET_CRS)
else:
    mt_border = mt_border.to_crs(TARGET_CRS)

# 3. Clip the points to the state boundary
# This automatically deletes any points landing in Idaho, Wyoming, Canada, etc.
gdf_montana = gpd.clip(gdf, mt_border)

print(f"Removed {len(gdf) - len(gdf_montana)} points outside of Montana.")

# Group by location / route / milepost and calculate summary statistics
milepost_crashes = gdf_montana.groupby(['Route Name', 'Milepost', 'geometry']).agg(
    total_crashes=('Quantity', 'sum'),
    whitetail_count=('Animal Type', lambda x: (x == 'WHITETAIL DEER').sum()),
    mule_deer_count=('Animal Type', lambda x: (x == 'MULE DEER').sum())
).reset_index()

# Convert back into a GeoDataFrame
gdf_mileposts = gpd.GeoDataFrame(milepost_crashes, geometry='geometry', crs=gdf_montana.crs)

# Export both datasets to the same GeoPackage!
output_path = '/home/ben/gds_data/project1/montana_deer_collisions_trimmed.gpkg'
gdf_montana.to_file(output_path, layer='individual_crashes', driver='GPKG')
gdf_mileposts.to_file(output_path, layer='milepost_hotspots', driver='GPKG')

