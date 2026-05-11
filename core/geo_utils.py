# converts coords from British National Grid (EPSG:27700) to WGS84 (EPSG:4326)
from pyproj import Transformer

_transformer = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)

def bng_to_wgs84(easting: float, northing: float):
    """Returns (lon, lat) tuple. Returns (None, None) on failure."""
    try:
        lon, lat = _transformer.transform(easting, northing)
        return round(lat, 7), round(lon, 7)
    except Exception:
        return None, None
    
# pyproj library converts BNG to EPSG:4326 with a error of less than 10 mm

