from shapely.geometry import Polygon, LineString
import geopandas as gpd

# Define the initial set of invalid geometries as a GeoDataFrame
invalid_geometries = gpd.GeoSeries([
    Polygon([(0, 0), (0, 2), (1, 1), (2, 2), (2, 0), (1, 1), (0, 0)]),
    Polygon([(0, 2), (0, 1), (2, 0), (0, 0), (0, 2)]),
    LineString([(0, 0), (1, 1), (1, 0)]),
], crs='EPSG:3857')
invalid_polygons_gdf = gpd.GeoDataFrame(geometry=invalid_geometries)

# Function to check geometry validity
def check_geom(geom):
    return geom.is_valid

# Function to check all geometries in a GeoDataFrame
def check_geodataframe_geom(geodataframe: gpd.GeoDataFrame) -> bool:
    valid_check = geodataframe.geometry.apply(check_geom)
    return valid_check.all()

# Function to repair geometries in a GeoDataFrame
def repair_geodataframe_geom(geodataframe: gpd.GeoDataFrame)-> dict:
    if not check_geodataframe_geom(geodataframe):
        print('Invalid geometries found, repairing...')
        geodataframe = geodataframe.make_valid()
    return {"repaired": True, "gdf": geodataframe}

# Function to buffer all geometries in a GeoDataFrame
def buffer_gdf(geodataframe: gpd.GeoDataFrame, distance: float) -> gpd.GeoDataFrame:
    print(f"Buffering geometries by {distance}...")
    # Check type of distance
    if not isinstance(distance, (int, float)):
        raise TypeError("Distance must be a number")
    
    # Applying a buffer to each geometry in the GeoDataFrame
    buffered_gdf = geodataframe.copy()
    buffered_gdf['geometry'] = buffered_gdf.geometry.buffer(distance)
    return {"message": "Geometries buffered successfully", "gdf": buffered_gdf}

# Function to get the bounding box of all geometries in a GeoDataFrame
def bounding_box_of_gdf(geodataframe: gpd.GeoDataFrame):
    # get bounding box of geodataframe 
    bbox = geodataframe.total_bounds
    return {"message": "Bounding box obtained successfully", "bbox": bbox}

# Main execution block
if __name__ == '__main__':
    print("Checking and repairing geometries...")
    repaired_polygons_gdf = repair_geodataframe_geom(invalid_polygons_gdf)
    
    all_geometries_valid = check_geodataframe_geom(repaired_polygons_gdf)
    print(f"All geometries valid: {all_geometries_valid}")
    
    # Example of buffering the geometries
    buffered_polygons_gdf = buffer_gdf(repaired_polygons_gdf, 0.1)
    
    # Getting the bounding box of the geometries
    bbox = bounding_box_of_gdf(buffered_polygons_gdf)
    print(f"Bounding box: {bbox}")
