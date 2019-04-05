import math

from location_filter import Rectangle
import numpy as np

MAX_ZOOM_LEVEL = 15

_EARTH_CIRCUMFERENCE_M = 40000000
_TYPICAL_WINDOW_WIDTH = 800


def get_typical_view_size(zoom_level: int):
    width_m = _TYPICAL_WINDOW_WIDTH * 200 / (1.5 ** zoom_level)
    return 360 * (width_m / _EARTH_CIRCUMFERENCE_M)


class Camera:
    def __init__(self, latitude: float = 0, longitude: float = 0,
                 zoom_level: int = 10, dimensions: (int, int) = (10, 10)):
        self.dimensions = np.array(dimensions)
        self.zoom_level = zoom_level
        self.center_at(latitude, longitude)

    # noinspection PyAttributeOutsideInit
    def center_at(self, new_lat: float, new_lon: float):
        self._center = np.array((new_lat, new_lon))
        self._center_point = self.gps_to_point(new_lat, new_lon)

    @property
    def px_width(self): return self.dimensions[0]

    @px_width.setter
    def px_width(self, val: int): self.dimensions[0] = val

    @property
    def px_height(self): return self.dimensions[1]

    @px_height.setter
    def px_height(self, val: int): self.dimensions[1] = val

    @property
    def zoom_level(self): return self._zoom_level

    # noinspection PyAttributeOutsideInit
    @zoom_level.setter
    def zoom_level(self, val: int):
        self._zoom_level = np.clip(val, 0, MAX_ZOOM_LEVEL)
        self._ppm = 1.5 ** self._zoom_level / 200

    def px_per_meter(self): return self._ppm

    @staticmethod
    def gps_to_point(lat: float, lon: float):
        return lon / 360, -math.log(math.tan(math.radians(lat / 2 + 45))) / math.tau

    @staticmethod
    def point_to_gps(x: float, y: float):
        return math.degrees(math.atan(math.exp(-y * math.tau))) * 2 - 90, x * 360

    def gps_to_px(self, gps_point: (float, float)):
        x, y = self.gps_to_point(*gps_point)
        dist = np.array((x, y)) - self._center_point
        dist_px = dist * _EARTH_CIRCUMFERENCE_M * self._ppm
        return tuple((self.dimensions / 2) + dist_px)
    
    def px_to_gps(self, px_point: (int, int)):
        dist_px = np.array(px_point) - (self.dimensions / 2)
        dist = dist_px / _EARTH_CIRCUMFERENCE_M / self._ppm
        x, y = dist + self._center_point
        return self.point_to_gps(x, y)

    def get_rect(self):
        a, b = self.px_to_gps((0, 0)), self.px_to_gps(self.dimensions)
        return Rectangle(b[0], a[1], a[0], b[1])

    def move_point_to_pixel(self, gps_point: (float, float), pixel: (int, int)):
        dist_deg, dist_deg_desired = self.px_to_gps(pixel) - self._center, np.array(gps_point) - self._center
        new_center = self._center - (dist_deg - dist_deg_desired)
        self.center_at(new_center[0], new_center[1])

    def zoom_in(self, px_towards: (int, int)):
        old_point = self.px_to_gps(px_towards)
        self.zoom_level = min(MAX_ZOOM_LEVEL, self.zoom_level + 1)
        self.move_point_to_pixel(old_point, px_towards)
    
    def zoom_out(self, px_from: (int, int)):
        old_point = self.px_to_gps(px_from)
        self.zoom_level = max(0, self.zoom_level - 1)
        self.move_point_to_pixel(old_point, px_from)
