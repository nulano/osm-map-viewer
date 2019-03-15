from location_filter import Rectangle
import numpy as np

MAX_ZOOM_LEVEL = 15

_EARTH_CIRCUMFERENCE_M = 40000000
_TYPICAL_WINDOW_WIDTH = 800


def get_typical_view_size(zoom_level: int):
    width_m = _TYPICAL_WINDOW_WIDTH * 20 / (1.5 ** zoom_level)
    return 360 * (width_m / _EARTH_CIRCUMFERENCE_M)


class Camera:
    def __init__(self, latitude: float = 0, longitude: float = 0,
                 zoom_level: int = 0, dimensions: (int, int) = (10, 10)):
        self.zoom_level = zoom_level
        self.dimensions = np.array(dimensions)
        self.center = np.array((latitude, longitude))

    @property
    def px_width(self): return self.dimensions[0]

    @px_width.setter
    def px_width(self, val: int): self.dimensions[0] = val

    @property
    def px_height(self): return self.dimensions[0]

    @px_height.setter
    def px_height(self, val: int): self.dimensions[0] = val

    def center_at(self, new_lat: float, new_lon: float):
        self.center = np.array((new_lat, new_lon))

    def px_per_meter(self):
        return 1.5 ** self.zoom_level / 20

    def deg_per_px(self):
        return 360 / _EARTH_CIRCUMFERENCE_M / self.px_per_meter()

    def _px_to_deg_matrix(self):
        deg_per_px = self.deg_per_px()
        return np.array(((0, deg_per_px), (-deg_per_px, 0)))
    
    def px_to_gps(self, px_point: (int, int)):
        dist_px = np.array(px_point) - (self.dimensions / 2)
        dist_deg = dist_px @ self._px_to_deg_matrix()
        return self.center + dist_deg
    
    def gps_to_px(self, gps_point: (float, float)):
        dist_deg = np.array(gps_point) - self.center
        dist_px = dist_deg @ np.linalg.inv(self._px_to_deg_matrix())
        return (self.dimensions / 2) + dist_px

    def get_rect(self):
        a, b = self.px_to_gps((0, 0)), self.px_to_gps(self.dimensions)
        return Rectangle(b[0], a[1], a[0], b[1])

    def move_point_to_pixel(self, gps_point: (float, float), pixel: (int, int)):
        dist_deg, dist_deg_desired = self.px_to_gps(pixel) - self.center, gps_point - self.center
        new_center = self.center - (dist_deg - dist_deg_desired)
        self.center_at(new_center[0], new_center[1])

    def zoom_in(self, px_towards: (int, int)):
        old_point = self.px_to_gps(px_towards)
        self.zoom_level = min(MAX_ZOOM_LEVEL, self.zoom_level + 1)
        self.move_point_to_pixel(old_point, px_towards)
    
    def zoom_out(self, px_from: (int, int)):
        old_point = self.px_to_gps(px_from)
        self.zoom_level = max(0, self.zoom_level - 1)
        self.move_point_to_pixel(old_point, px_from)
