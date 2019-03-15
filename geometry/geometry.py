from collections import namedtuple

import numpy as np


def distance(a, b):
    a, b = np.array(a), np.array(b)
    return np.linalg.norm(b - a)


def _polygon_raw_area(polygon: np.ndarray):
    return np.dot(polygon[:-1, 0], polygon[1:, 1]) + np.dot(polygon[-1, 0], polygon[0, 1]) \
        - (np.dot(polygon[:-1, 1], polygon[1:, 0]) + np.dot(polygon[-1, 1], polygon[0, 0]))


def polygon_area(polygon):
    return 0.5 * np.abs(_polygon_raw_area(np.array(polygon)))


def _ray_trace(point: np.ndarray, polygon: np.ndarray):
    poly = polygon - point
    hits = []
    for i, (a, b) in enumerate(zip(poly, np.roll(poly, 1, axis=0))):
        # ensure Ay <= By
        if a[1] > b[1]:
            b, a = a, b
        # 0 <= Ax - Ay * (Bx - Ax) / (By - Ay)  <==>  0 <= Ax * (By - Ay) - Ay * (Bx - Ax)
        x_over_dy = np.cross(a, b - a)
        if a[1] <= 0 < b[1] and 0 <= x_over_dy:
            hit = np.array([x_over_dy / (b - a)[1], 0]) + point
            hits.append(namedtuple('Hit', ['point', 'a', 'b'])(hit, i - 1, i))
    return hits


def point_in_polygon(point, polygon):
    return len(_ray_trace(np.array(point), np.array(polygon))) % 2 == 1


def polygons_to_wsps(polygons):
    polys = []
    for poly in polygons:
        poly = np.array(poly)
        # ensure points are CCW:
        if _polygon_raw_area(poly) < 0:
            poly = np.flip(poly, axis=0)
        # ensure right-most point is first:
        poly = np.roll(poly, -poly[:, 0].argmax(), axis=0)
        polys.append(poly)
    out = []
    for poly in sorted(polys, key=lambda p: p[0, 0], reverse=True):
        best_hit, best_hit_poly = None, None
        for poly_out_index, poly_out in enumerate(out):
            for hit in _ray_trace(poly[0], poly_out):
                if best_hit is None or hit.point[0] < best_hit.point[0]:
                    best_hit, best_hit_poly = hit, poly_out_index
        if best_hit is not None and out[best_hit_poly][best_hit.a][1] < out[best_hit_poly][best_hit.b][1]:
            out[best_hit_poly] = np.concatenate([
                out[best_hit_poly][:best_hit.a + 1, ],
                [best_hit.point, poly[0]],
                poly[::-1, ],
                [best_hit.point],
                out[best_hit_poly][best_hit.b:, ]
            ], axis=0)
        else:
            out.append(poly)
    return out
