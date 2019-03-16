from queue import Queue
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
        ways_a, ways_b = {}, {}
        out = []
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
            raise KeyError(str(len(ways_a)) + ' were not connected')
        return out

    def multipolygon_to_wsps(self, multipolygon: Element):
        id = multipolygon.attrib['id']
        if id in self._cache_multipolygon_to_wsps:
            return self._cache_multipolygon_to_wsps[id]
        else:
            out = []
            try:
                type = tag_dict(multipolygon).get('type', None)
                if type == 'multipolygon':
                    out = geometry.polygons_to_wsps(self.multipolygon_to_polygons(multipolygon))
                else:
                    nulano_log('invalid multipolygon: {}[{}].type={}'
                               .format(multipolygon.tag, multipolygon.attrib['id'], type), level=2)
            except KeyError:
                from traceback import format_exc
                for line in format_exc(limit=2).splitlines():
                    nulano_log(line, level=1)
            self._cache_multipolygon_to_wsps[id] = out
            return out
