from collections import namedtuple
from queue import PriorityQueue

import numpy as np


# based on: https://blog.mapbox.com/a-new-algorithm-for-finding-a-visual-center-of-a-polygon-7c77e6492fbc
# ported from JS: https://github.com/mapbox/polylabel/blob/master/polylabel.js

# FIXME multipolygon should be represented as list of innner and outer polygons
from geometry import point_in_polygon


def create_cell(x, y, size_half, multipolygon):
    center = np.array((x, y))

    # distance from points
    dist_center = np.sqrt(np.min([np.min(np.sum(np.square(polygon - center), axis=1)) for polygon in multipolygon]))

    # distance to each segment
    for polygon in multipolygon:
        for a, b in zip(polygon, np.roll(polygon, -1, axis=0)):
            if np.dot(center - a, b - a) > 0 and np.dot(center - b, a - b) > 0:
                dist_center = min(dist_center, abs(np.cross(a - center, b - center) / np.linalg.norm(b - a)))

    # inside?
    for polygon in multipolygon:
        if point_in_polygon(center, polygon):
            dist_center *= -1
    dist_center *= -1

    dist_max = size_half * (2 ** 0.5) + dist_center

    return namedtuple('Cell', 'dist_max_neg dist_max dist_center size_half x y') \
        (-dist_max, dist_max, dist_center, size_half, x, y)


def polylabel(multipolygon: list):
    precision = 1.0

    multipolygon = [np.array(polygon) for polygon in multipolygon]
    minx, miny = np.min([np.min(polygon, axis=0) for polygon in multipolygon], axis=0)
    maxx, maxy = np.max([np.max(polygon, axis=0) for polygon in multipolygon], axis=0)
    width, height = maxx - minx, maxy - miny
    cellSize = min(width, height)
    if cellSize < precision:
        return (minx + maxx) / 2, (miny + maxy) / 2

    queue = PriorityQueue()

    h = cellSize / 2
    for y in np.arange(miny, maxy, cellSize):
        for x in np.arange(minx, maxx, cellSize):
            queue.put(create_cell(x + h, y + h, h, multipolygon))

    # centroid = create_cell_centroid(multipolygon)
    bbox = create_cell((minx + maxx) / 2, (miny + maxy) / 2, 0, multipolygon)
    # best = centroid if centroid.dist_center > bbox.dist_center else bbox
    best = bbox

    while not queue.empty():
        cell = queue.get()
        if cell.dist_center > best.dist_center:
            best = cell
        if cell.dist_max - best.dist_center <= precision:
            continue
        h = cell.size_half / 2
        x, y = cell.x, cell.y
        queue.put(create_cell(x - h, y - h, h, multipolygon))
        queue.put(create_cell(x - h, y + h, h, multipolygon))
        queue.put(create_cell(x + h, y - h, h, multipolygon))
        queue.put(create_cell(x + h, y + h, h, multipolygon))

    return best.x, best.y