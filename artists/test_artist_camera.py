class BoxCamera:
    """A mock implementation of camera. For testing purposes only."""
    def __init__(self, bounds, dimensions):
        self.zoom_level = 0
        self.px_width, self.px_height = dimensions
        self.max_lat = bounds.max_lat
        self.min_lon = bounds.min_lon
        self.lat_height = bounds.max_lat - bounds.min_lat
        self.lon_width = bounds.max_lon - bounds.min_lon
    
    def px_to_gps(self, px_point):
        x, y = px_point
        lon = self.min_lon + x / self.px_width * self.lon_width
        lat = self.max_lat - y / self.px_height * self.lat_height
        return lat, lon
    
    def gps_to_px(self, gps_point):
        lat, lon = gps_point
        y = (self.max_lat - lat) / self.lat_height * self.px_height
        x = (lon - self.min_lon) / self.lon_width * self.px_width
        return x, y
