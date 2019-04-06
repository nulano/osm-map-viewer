from queue import Queue
from weakref import WeakKeyDictionary
from xml.etree.ElementTree import ElementTree, Element

import geometry


# fallback for incompatible gui implementations
def nulano_log(*msg, level=0):
    print(*msg)


def tag_dict(element: Element):
    out = {}
    for el in element:
        if el.tag == 'tag':
            out[el.attrib['k']] = el.attrib['v']
    return out


def _memoize(func):
    def memoized(osm_helper, element: Element, cache=WeakKeyDictionary()):
        try:
            return cache[element]
        except KeyError:
            cache[element] = out = func(osm_helper, element)
            return out

    return memoized


class OsmHelper:
    def __init__(self, element_tree: ElementTree):
        self.element_tree = element_tree
        self.nodes = {}
        for nd in element_tree.getroot():
            if nd.tag == 'node':
                self.nodes[nd.attrib['id']] = nd
        self.ways = {}
        for way in element_tree.getroot():
            if way.tag == 'way':
                self.ways[way.attrib['id']] = way

    @_memoize
    def way_node_ids(self, way: Element):
        out = []
        for el in way:
            if el.tag == 'nd':
                out.append(el.attrib['ref'])
        return out

    def way_nodes_for_ids(self, way: list):
        return [self.nodes[n] for n in way]

    def way_nodes(self, way: Element):
        return self.way_nodes_for_ids(self.way_node_ids(way))

    def way_coordinates_for_nodes(self, way: list):
        return [(float(nd.attrib['lat']), float(nd.attrib['lon'])) for nd in way]

    def way_coordinates_for_ids(self, way: list):
        return self.way_coordinates_for_nodes(self.way_nodes_for_ids(way))

    @_memoize
    def way_coordinates(self, way: Element):
        return self.way_coordinates_for_nodes(self.way_nodes(way))

    @_memoize
    def multipolygon_to_polygons(self, multipolygon: Element):
        out = []
        try:
            type = tag_dict(multipolygon).get('type', None)
            if type != 'multipolygon':
                raise ValueError('invalid multipolygon: {}[{}].type={}'
                                 .format(multipolygon.tag, multipolygon.attrib['id'], type), level=2)
            ways = Queue()
            for el in multipolygon:
                if el.tag == 'member' and el.attrib['type'] == 'way':
                    way = self.ways.get(el.attrib['ref'])
                    if way is None:
                        nulano_log('multipolygon {} is missing way {}'
                                   .format(multipolygon.attrib['id'], el.attrib['ref']), level=1)
                    else:
                        ways.put(self.way_node_ids(way))
            ways_a, ways_b = {}, {}
            while not ways.empty():
                way = ways.get(block=False)
                if way[0] == way[-1]:
                    out.append(self.way_coordinates_for_ids(way[:-1]))
                else:
                    if way[-1] < way[0]:
                        way.reverse()
                    a, b = way[0], way[-1]
                    if a in ways_b:
                        other = ways_b.pop(a)
                        ways_a.pop(other[0])
                        ways.put(other + way[1:])
                    elif a in ways_a:
                        other = ways_a.pop(a)
                        ways_b.pop(other[-1])
                        ways.put(other[::-1] + way[1:])
                    elif b in ways_a:
                        other = ways_a.pop(b)
                        ways_b.pop(other[-1])
                        ways.put(way + other[1:])
                    elif b in ways_b:
                        other = ways_b.pop(b)
                        ways_a.pop(other[0])
                        ways.put(way[:-1] + other[::-1])
                    else:
                        ways_a[a] = way
                        ways_b[b] = way
            if len(ways_a) is not 0:
                nulano_log('multipolygon {} has {} unconnected way(s)'
                           .format(multipolygon.attrib['id'], len(ways_a)), level=1)
        except (KeyError, ValueError):
            from traceback import format_exc
            for line in format_exc(limit=2).splitlines():
                nulano_log(line, level=2)
            out = []
        return out

    @_memoize
    def multipolygon_to_wsps(self, multipolygon: Element):
        return geometry.polygons_to_wsps(self.multipolygon_to_polygons(multipolygon))
