import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import from_origin
from scipy.ndimage import gaussian_filter

# 1. Load the Montana collision points (EPSG:32100)
gdf = gpd.read_file('/home/ben/gds_data/project1/montana_deer_collisions_trimmed.gpkg', layer='individual_crashes')

# 2. Define raster parameters (in meters)
pixel_size = 160        # 160m grid resolution (~0.1 mile markers)
search_radius = 5000     # 5km search radius for deer corridor smoothing

# Standard deviation for Gaussian kernel: radius roughly covers ~2 standard deviations
sigma_pixels = (search_radius / pixel_size) / 2.0

# 3. Determine grid extent with padding
minx, miny, maxx, maxy = gdf.total_bounds
padding = search_radius * 1.5
minx, miny = minx - padding, miny - padding
maxx, maxy = maxx + padding, maxy + padding

# Calculate raster dimensions
cols = int(np.ceil((maxx - minx) / pixel_size))
rows = int(np.ceil((maxy - miny) / pixel_size))

# 4. Bin point data into a 2D grid (point count per pixel)
x_coords = np.asarray(gdf.geometry.x, dtype=np.float64)
y_coords = np.asarray(gdf.geometry.y, dtype=np.float64)

# Transform coordinates to pixel row/col indices
col_idx = np.floor((x_coords - float(minx)) / float(pixel_size)).astype(int)
row_idx = np.floor((maxy - y_coords) / pixel_size).astype(int)

# Create 2D grid and accumulate point counts
grid = np.zeros((rows, cols), dtype=np.float32)
np.add.at(grid, (row_idx, col_idx), 1.0)

# 5. Apply Gaussian Kernel Density smoothing
print("Calculating Kernel Density Estimation across Montana...")
heatmap = gaussian_filter(grid, sigma=sigma_pixels, mode='constant', cval=0.0)

# 6. Build the affine transformation matrix
# from_origin(west_x, north_y, x_pixel_width, y_pixel_height)
transform = from_origin(minx, maxy, pixel_size, pixel_size)

# 7. Write to GeoTIFF
output_tif = '/home/ben/gds_data/project1/MT_wvc_heatmap_160m.tif'
with rasterio.open(
    output_tif,
    'w',
    driver='GTiff',
    height=rows,
    width=cols,
    count=1,
    dtype='float32',
    crs=gdf.crs,
    transform=transform,
    nodata=0.0,
    compress='lzw'  # Keeps file size tiny (~10-15 MB)
) as dst:
    dst.write(heatmap, 1)

print(f"Heatmap successfully created at {output_tif}!")