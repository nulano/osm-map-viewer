from collections import namedtuple
from typing import List, Tuple

import numpy as np


_Point = Tuple[float, float]
_Polygon = List[_Point]


def _norm_polygon(polygon: _Polygon):
    if len(polygon) < 3:
        polygon = []
    if polygon[0] != polygon[-1]:
        polygon = polygon + [polygon[0]]
    return np.array(polygon)


def distance(a: _Point, b: _Point):
    a, b = np.array(a), np.array(b)
    return np.linalg.norm(b - a)


def _polygon_raw_area(polygon: np.ndarray):
    return np.dot(polygon[:-1, 0], polygon[1:, 1]) - np.dot(polygon[:-1, 1], polygon[1:, 0])


def polygon_area(polygon: List[_Point]):
    return 0.5 * np.abs(_polygon_raw_area(_norm_polygon(polygon)))


def _ray_trace(point: np.ndarray, polygon: np.ndarray):
    poly = polygon - point
    hits = []
    for i, (a, b) in enumerate(zip(poly[:-1], poly[1:])):
        # ensure Ay <= By
        if a[1] > b[1]:
            b, a = a, b
        # 0 <= Ax - Ay * (Bx - Ax) / (By - Ay)  <==>  0 <= Ax * (By - Ay) - Ay * (Bx - Ax)
        x_over_dy = np.cross(a, b - a)
        if a[1] <= 0 < b[1] and 0 <= x_over_dy:
            hit = np.array([x_over_dy / (b - a)[1], 0]) + point
            hits.append(namedtuple('Hit', ['point', 'a', 'b'])(hit, i, i + 1))
    return hits


def point_in_polygon(point: _Point, polygon: List[_Point]):
    return len(_ray_trace(np.array(point), _norm_polygon(polygon))) % 2 == 1


def polygons_to_wsps(multipolygon: List[List[_Point]]):
    polygons = []
    for polygon in multipolygon:
        polygon = _norm_polygon(polygon)
        # ensure points are CCW:
        if _polygon_raw_area(polygon) < 0:
            polygon = np.flip(polygon, axis=0)
        # ensure right-most point is first:
        polygon = np.roll(polygon[:-1], -polygon[:-1, 0].argmax(), axis=0)
        polygons.append(np.concatenate([polygon, [polygon[0]]]))
    out = []
    for polygon in sorted(polygons, key=lambda p: p[0, 0], reverse=True):
        best_hit, best_hit_poly = None, None
        for poly_out_index, poly_out in enumerate(out):
            for hit in _ray_trace(polygon[0], poly_out):
                if best_hit is None or hit.point[0] < best_hit.point[0]:
                    best_hit, best_hit_poly = hit, poly_out_index
        if best_hit is not None and out[best_hit_poly][best_hit.a][1] < out[best_hit_poly][best_hit.b][1]:
            out[best_hit_poly] = np.concatenate([
                out[best_hit_poly][:best_hit.a + 1, ],
                [best_hit.point],
                polygon[::-1, ],
                [best_hit.point],
                out[best_hit_poly][best_hit.b:, ]
            ], axis=0)
        else:
            out.append(polygon)
    return [[(x, y) for x, y in polygon] for polygon in out]
