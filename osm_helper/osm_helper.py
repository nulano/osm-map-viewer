from queue import Queue
from xml.etree.ElementTree import ElementTree, Element

import geometry


def tag_dict(element: Element):
    out = {}
    for el in element:
        if el.tag == 'tag':
            out[el.attrib['k']] = el.attrib['v']
    return out


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
        self._cache_way_node_ids = {}
        self._cache_multipolygon_to_wsps = {}

    # cached
    def way_node_ids(self, way: Element):
        id = way.attrib['id']
        if id in self._cache_way_node_ids:
            return self._cache_way_node_ids[id]
        else:
            out = []
            for el in way:
                if el.tag == 'nd':
                    out.append(el.attrib['ref'])
            self._cache_way_node_ids[id] = out
            return out

    def way_nodes_for_ids(self, way: list):
        return [self.nodes[n] for n in way]

    # TODO cache?
    def way_nodes(self, way: Element):
        return self.way_nodes_for_ids(self.way_node_ids(way))

    def way_coordinates_for_nodes(self, way: list):
        return [(float(nd.attrib['lat']), float(nd.attrib['lon'])) for nd in way]

    def way_coordinates_for_ids(self, way: list):
        return self.way_coordinates_for_nodes(self.way_nodes_for_ids(way))

    # TODO cache?
    def way_coordinates(self, way: Element):
        return self.way_coordinates_for_nodes(self.way_nodes(way))

    # TODO cache?
    def multipolygon_to_polygons(self, multipolygon: Element):
        ways = Queue()
        for el in multipolygon:
            if el.tag == 'member' and el.attrib['type'] == 'way':
                ways.put(self.way_node_ids(self.ways[el.attrib['ref']]))
        ways_from_a, ways_from_b = {}, {}
        out = []
        while not ways.empty():
            way = ways.get(block=False)
            a, b = min(way[0], way[-1]), max(way[0], way[-1])
            if a == b:
                out.append(self.way_coordinates_for_ids(way))
            elif a in ways_from_a:
                ways.put(ways_from_a.pop(a)[::-1] + way[1:])
            elif b in ways_from_b:
                ways.put(way + ways_from_b.pop(b)[1:])
            else:
                raise KeyError
        return out

    def multipolygon_to_wsps(self, multipolygon: Element):
        id = multipolygon.attrib['id']
        if id in self._cache_multipolygon_to_wsps:
            return self._cache_multipolygon_to_wsps[id]
        else:
            out = []
            try:
                out = geometry.polygons_to_wsps(self.multipolygon_to_polygons(multipolygon))
            except KeyError as err:
                print('multipolygon', multipolygon.attrib['id'], 'is missing a way:', str(err))
            self._cache_multipolygon_to_wsps[id] = out
            return out
