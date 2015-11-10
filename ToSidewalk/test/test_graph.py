import unittest

from ToSidewalk.graph import GeometricGraph
from ToSidewalk.edge import Edge


class TestGeometricGraphMethods(unittest.TestCase):

    def setUp(self):
        self.graph = GeometricGraph()

    def test_remove_node(self):
        node = self.graph.create_node(0., 0.)
        self.graph.remove_node(node.id)
        self.assertEqual(len(self.graph.nodes.values()), 0.)

    def test_get_adjacent_nodes(self):
        n0 = self.graph.create_node(0., 0.)
        n1 = self.graph.create_node(1., 0.)
        n2 = self.graph.create_node(0., 1.)
        n3 = self.graph.create_node(-1., 0.)
        n4 = self.graph.create_node(0., -1.)

        p1 = self.graph.create_path(nodes=[n0, n1])
        p2 = self.graph.create_path(nodes=[n0, n2])
        p3 = self.graph.create_path(nodes=[n0, n3])
        p4 = self.graph.create_path(nodes=[n0, n4])

        self.assertEqual(len(self.graph.get_adjacent_nodes(n0)), 4)

    def test_get_degrees(self):
        n0 = self.graph.create_node(0., 0.)
        n1 = self.graph.create_node(1., 0.)
        n2 = self.graph.create_node(0., 1.)
        n3 = self.graph.create_node(-1., 0.)
        n4 = self.graph.create_node(0., -1.)

        p1 = self.graph.create_path(nodes=[n0, n1])
        p2 = self.graph.create_path(nodes=[n0, n2])
        p3 = self.graph.create_path(nodes=[n0, n3])
        p4 = self.graph.create_path(nodes=[n0, n4])

        self.assertEqual(self.graph.get_degrees()[0][0], 4)

    def test_remove_node(self):
        nodes =[self.graph.create_node(float(i), float(i) * 10) for i in range(5)]
        path = self.graph.create_path(nodes=nodes)

        self.graph.remove_node(2)

        self.assertEqual(len(path.edges), 3)
        self.assertEqual(path.edges[1].xy[0][0], 1.)
        self.assertEqual(path.edges[1].xy[0][1], 3.)
        self.assertEqual(path.edges[1].xy[1][0], 10.)
        self.assertEqual(path.edges[1].xy[1][1], 30.)

    def test_remove_path(self):
        nodes1 = [self.graph.create_node(float(i), 0.) for i in range(5)]
        nodes2 = [self.graph.create_node(float(i), 1.) for i in range(2)] + [nodes1[2]]
        path1 = self.graph.create_path(nodes=nodes1)
        path2 = self.graph.create_path(nodes=nodes2)

        node = nodes1[2]
        self.assertEqual(len(node.edges), 3)
        self.graph.remove_path(path1.id)
        self.assertEqual(len(node.edges), 1)

    def test_merge_edges_1(self):
        nodes1 = [self.graph.create_node(-76.9955 + 0.001 * i, 38.8954) for i in range(6)]
        nodes2 = [self.graph.create_node(-76.996 + 0.001 * i, 38.8964) for i in range(6)]
        nodes2 = nodes2[::-1]
        path1 = self.graph.create_path(nodes=nodes1)
        path2 = self.graph.create_path(nodes=nodes2)

        e1, e2 = path1.edges[2], path2.edges[2]
        p1, p2 = e1.path, e2.path

        new_edge, old_to_new = self.graph.merged_edges(e1, e2)
        self.graph.create_path(edges=[new_edge])

        # Keep edges
        edge_index_1 = path1.edges.index(e1)
        edge_index_2 = path2.edges.index(e2)
        p1_1 = [e.copy() for e in path1.edges[:edge_index_1]]
        p1_2 = [e.copy() for e in path1.edges[edge_index_1 + 1:]]
        p2_1 = [e.copy() for e in path2.edges[:edge_index_2]]
        p2_2 = [e.copy() for e in path2.edges[edge_index_2 + 1:]]
        new_edge_lists = [p1_1, p1_2, p2_1, p2_2]

        # Remove old paths
        self.graph.remove_path(p1.id)
        self.graph.remove_path(p2.id)

        # Create new paths
        for new_edge_list in new_edge_lists:
            p = self.graph.create_path(edges=new_edge_list)
            node_to_swap = list(set(p.get_nodes()) & set(old_to_new.keys()))
            assert len(node_to_swap) == 1
            node_to_swap = node_to_swap[0]

            edge_to_swap = list(set(p.edges) & set(node_to_swap.edges))
            assert len(edge_to_swap) == 1
            edge_to_swap = edge_to_swap[0]
            self.graph.swap_edge_node(edge_to_swap, node_to_swap, old_to_new[node_to_swap])

        self.assertEqual(len(self.graph.get_paths()), 5)

    def test_merge_edges_2(self):
        # Init a graph
        nodes1 = [self.graph.create_node(float(i), 0.) for i in range(6)]
        nodes2 = [self.graph.create_node(float(i) + .5, 1.) for i in range(6)]
        path1 = self.graph.create_path(nodes=nodes1)
        path2 = self.graph.create_path(nodes=nodes2)

        # Choose edges to merge
        e1, e2 = path1.edges[1], path2.edges[0]
        p1, p2 = e1.path, e2.path

        # Compute new edges
        new_edge, old_to_new = self.graph.merge_edges(e1, e2)
        self.graph.create_path(edges=[new_edge])

        # Keep edges (Create copies of edges so nodes won't get deleted when I delete paths.)
        edge_index_1 = path1.edges.index(e1)
        edge_index_2 = path2.edges.index(e2)
        edges_1_1, edges_1_2 = path1.split_edges(edge_index_1)
        edges_2_1, edges_2_2 = path2.split_edges(edge_index_2)
        edge_lists = [edges_1_1, edges_1_2, edges_2_1, edges_2_2]
        new_edge_lists = [[e.copy() for e in edges] for edges in edge_lists]
        new_edge_lists = filter(lambda e: e, new_edge_lists)  # remove empty lists

        # Remove old paths
        self.graph.remove_path(p1.id)
        self.graph.remove_path(p2.id)

        # Create new paths
        for new_edge_list in new_edge_lists:
            try:
                p = self.graph.create_path(edges=new_edge_list)
                node_to_swap = list(set(p.get_nodes()) & set(old_to_new.keys()))
                assert len(node_to_swap) == 1
                node_to_swap = node_to_swap[0]
            except:
                raise

            try:
                edge_to_swap = list(set(p.edges) & set(node_to_swap.edges))
                assert len(edge_to_swap) == 1
                edge_to_swap = edge_to_swap[0]
            except:
                raise
            self.graph.swap_edge_node(edge_to_swap, node_to_swap, old_to_new[node_to_swap])
        self.graph.visualize(padding=1)
        self.assertEqual(len(self.graph.get_paths()), 4)

    def test_merge_edges_3(self):
        # Init a graph
        nodes1 = [self.graph.create_node(float(i), 0.) for i in range(6)]
        nodes2 = [self.graph.create_node(float(i) + .5, 1.) for i in range(6)]
        path1 = self.graph.create_path(nodes=nodes1)
        path2 = self.graph.create_path(nodes=nodes2)

        # Choose edges to merge
        e1, e2 = path1.edges[0], path2.edges[0]
        p1, p2 = e1.path, e2.path

        # Identify which
        affected = {edge for node in {e1.source, e1.target, e2.source, e2.target} for edge in node.edges}
        affected -= {e1, e2}

        new_edge, old_to_new = self.graph.merge_edges(e1, e2)
        self.graph.create_path(edges=[new_edge])

        # Keep edges (Create copies of edges so nodes won't get deleted when I delete paths.)
        edge_index_1 = path1.edges.index(e1)
        edge_index_2 = path2.edges.index(e2)
        edges_1_1, edges_1_2 = path1.split_edges(edge_index_1)
        edges_2_1, edges_2_2 = path2.split_edges(edge_index_2)
        edge_lists = [edges_1_1, edges_1_2, edges_2_1, edges_2_2]
        new_edge_lists = [[e.copy() for e in edges] for edges in edge_lists]
        new_edge_lists = filter(lambda e: e, new_edge_lists)  # remove empty lists

        # Remove old paths
        self.graph.remove_path(p1.id)
        self.graph.remove_path(p2.id)

        # Create new paths
        for new_edge_list in new_edge_lists:
            p = self.graph.create_path(edges=new_edge_list)
            node_to_swap = list(set(p.get_nodes()) & set(old_to_new.keys()))
            assert len(node_to_swap) == 1
            node_to_swap = node_to_swap[0]

            edge_to_swap = list(set(p.edges) & set(node_to_swap.edges))
            assert len(edge_to_swap) == 1
            edge_to_swap = edge_to_swap[0]

            self.graph.swap_edge_node(edge_to_swap, node_to_swap, old_to_new[node_to_swap])

        self.assertEqual(len(self.graph.get_paths()), 3)

    def test_merge_edges_4(self):
        # Init a graph
        nodes1 = [self.graph.create_node(float(i), 0.) for i in range(6)]
        nodes2 = [self.graph.create_node(float(i) + .5, 1.) for i in range(6)]
        nodes3 = [nodes2[1]] + [self.graph.create_node(1., 2. + i) for i in range(6)]
        nodes4 = [nodes1[0]] + [self.graph.create_node(1., -1. - i) for i in range(6)]
        path1 = self.graph.create_path(nodes=nodes1)
        path2 = self.graph.create_path(nodes=nodes2)
        path3 = self.graph.create_path(nodes=nodes3)
        path4 = self.graph.create_path(nodes=nodes4)

        self.graph.visualize(padding=1)

        # Choose edges to merge
        e1, e2 = path1.edges[0], path2.edges[0]
        p1, p2 = e1.path, e2.path

        # Identify which
        affected = {edge for node in {e1.source, e1.target, e2.source, e2.target} for edge in node.edges}
        affected -= set(p1.edges)  # Exclude the edges in p1
        affected -= set(p2.edges)  # Exclude the edges in p2

        new_edge, old_to_new = self.graph.merge_edges(e1, e2)
        self.graph.create_path(edges=[new_edge])

        # Keep edges (Create copies of edges so nodes won't get deleted when I delete paths.)
        edge_index_1 = path1.edges.index(e1)
        edge_index_2 = path2.edges.index(e2)
        edges_1_1, edges_1_2 = path1.split_edges(edge_index_1)
        edges_2_1, edges_2_2 = path2.split_edges(edge_index_2)
        edge_lists = [edges_1_1, edges_1_2, edges_2_1, edges_2_2]
        new_edge_lists = [[e.copy() for e in edges] for edges in edge_lists]
        new_edge_lists = filter(lambda e: e, new_edge_lists)  # remove empty lists

        # Remove old paths
        self.graph.remove_path(p1.id)
        self.graph.remove_path(p2.id)

        # Create new paths
        for new_edge_list in new_edge_lists:
            p = self.graph.create_path(edges=new_edge_list)
            node_to_swap = list(set(p.get_nodes()) & set(old_to_new.keys()))
            assert len(node_to_swap) == 1
            node_to_swap = node_to_swap[0]

            edge_to_swap = list(set(p.edges) & set(node_to_swap.edges))
            assert len(edge_to_swap) == 1
            edge_to_swap = edge_to_swap[0]

            self.graph.swap_edge_node(edge_to_swap, node_to_swap, old_to_new[node_to_swap])

        # Update affectede edges
        for affected_edge in affected:
            node_to_swap = list({affected_edge.source, affected_edge.target} & set(old_to_new.keys()))
            assert len(node_to_swap) == 1
            node_to_swap = node_to_swap[0]
            self.graph.swap_edge_node(affected_edge, node_to_swap, old_to_new[node_to_swap])

        self.graph.visualize(padding=1)
        self.assertEqual(len(self.graph.get_paths()), 5)

    def test_merge_edges_5(self):
        # Init a graph
        nodes1 = [self.graph.create_node(float(i), 0.) for i in range(6)]
        nodes2 = [nodes1[0]] + [self.graph.create_node(float(i) + .5, 1.) for i in range(1, 6)]
        nodes3 = [nodes2[1]] + [self.graph.create_node(1., 2. + i) for i in range(6)]
        nodes4 = [nodes1[0]] + [self.graph.create_node(1., -1. - i) for i in range(6)]
        path1 = self.graph.create_path(nodes=nodes1)
        path2 = self.graph.create_path(nodes=nodes2)
        path3 = self.graph.create_path(nodes=nodes3)
        path4 = self.graph.create_path(nodes=nodes4)

        self.graph.visualize(padding=1)

        # Choose edges to merge
        e1, e2 = path1.edges[0], path2.edges[0]
        p1, p2 = e1.path, e2.path

        # Identify which
        affected = {edge for node in {e1.source, e1.target, e2.source, e2.target} for edge in node.edges}
        affected -= set(p1.edges)  # Exclude the edges in p1
        affected -= set(p2.edges)  # Exclude the edges in p2

        try:
            new_edge, old_to_new = self.graph.merge_edges(e1, e2)
        except AssertionError:
            pass
        self.graph.create_path(edges=[new_edge])

        # Keep edges (Create copies of edges so nodes won't get deleted when I delete paths.)
        edge_index_1 = path1.edges.index(e1)
        edge_index_2 = path2.edges.index(e2)
        edges_1_1, edges_1_2 = path1.split_edges(edge_index_1)
        edges_2_1, edges_2_2 = path2.split_edges(edge_index_2)
        edge_lists = [edges_1_1, edges_1_2, edges_2_1, edges_2_2]
        new_edge_lists = [[e.copy() for e in edges] for edges in edge_lists]
        new_edge_lists = filter(lambda e: e, new_edge_lists)  # remove empty lists

        # Remove old paths
        self.graph.remove_path(p1.id)
        self.graph.remove_path(p2.id)

        # Create new paths
        for new_edge_list in new_edge_lists:
            p = self.graph.create_path(edges=new_edge_list)
            node_to_swap = list(set(p.get_nodes()) & set(old_to_new.keys()))
            assert len(node_to_swap) == 1
            node_to_swap = node_to_swap[0]

            edge_to_swap = list(set(p.edges) & set(node_to_swap.edges))
            assert len(edge_to_swap) == 1
            edge_to_swap = edge_to_swap[0]

            self.graph.swap_edge_node(edge_to_swap, node_to_swap, old_to_new[node_to_swap])

        # Update affectede edges
        for affected_edge in affected:
            try:
                node_to_swap = list({affected_edge.source, affected_edge.target} & set(old_to_new.keys()))
                assert len(node_to_swap) == 1
                node_to_swap = node_to_swap[0]
                self.graph.swap_edge_node(affected_edge, node_to_swap, old_to_new[node_to_swap])
            except AssertionError:
                raise

        self.graph.visualize(padding=1)
        self.assertEqual(len(self.graph.get_paths()), 5)

    def test_merge_edges_6(self):
        # Init a graph
        nodes1 = [self.graph.create_node(p[0], p[1]) for p in [(-2., 0.), (-1., 0.)]]
        nodes2 = [self.graph.create_node(p[0], p[1]) for p in [(0., 2.), (0., 1.)]]
        nodes3 = [self.graph.create_node(p[0], p[1]) for p in [(2., 0.), (1., 0.)]]
        nodes4 = [self.graph.create_node(p[0], p[1]) for p in [(0., -2.), (0., -1.)]]
        # nodes5 = [self.graph.create_node(p[0], p[1]) for p in [(-1., 0.), (0., 1.)]]
        # nodes6 = [self.graph.create_node(p[0], p[1]) for p in [(0., 1.), (1., 0.)]]
        # nodes7 = [self.graph.create_node(p[0], p[1]) for p in [(1., 0.), (0., -1.)]]
        # nodes8 = [self.graph.create_node(p[0], p[1]) for p in [(0., -1.), (-1., 0.)]]
        nodes5 = [nodes1[1], nodes2[1]]
        nodes6 = [nodes2[1], nodes3[1]]
        nodes7 = [nodes3[1], nodes4[1]]
        nodes8 = [nodes4[1], nodes1[1]]

        path1 = self.graph.create_path(nodes=nodes1)
        path2 = self.graph.create_path(nodes=nodes2)
        path3 = self.graph.create_path(nodes=nodes3)
        path4 = self.graph.create_path(nodes=nodes4)
        path5 = self.graph.create_path(nodes=nodes5)
        path6 = self.graph.create_path(nodes=nodes6)
        path7 = self.graph.create_path(nodes=nodes7)
        path8 = self.graph.create_path(nodes=nodes8)

        # Choose edges to merge
        e1, e2 = path5.edges[0], path8.edges[0]
        p1, p2 = e1.path, e2.path

        # Identify which
        affected = {edge for node in {e1.source, e1.target, e2.source, e2.target} for edge in node.edges}
        affected -= set(p1.edges)  # Exclude the edges in p1
        affected -= set(p2.edges)  # Exclude the edges in p2
        affected_paths = set()

        try:
            new_edge, old_to_new = self.graph.merge_edges(e1, e2)
        except AssertionError:
            pass
        p = self.graph.create_path(edges=[new_edge])
        affected_paths.add(p)

        # Keep edges (Create copies of edges so nodes won't get deleted when I delete paths.)
        edge_index_1 = p1.edges.index(e1)
        edge_index_2 = p2.edges.index(e2)
        edges_1_1, edges_1_2 = path1.split_edges(edge_index_1)
        edges_2_1, edges_2_2 = path2.split_edges(edge_index_2)
        edge_lists = [edges_1_1, edges_1_2, edges_2_1, edges_2_2]
        new_edge_lists = [[e.copy() for e in edges] for edges in edge_lists]
        new_edge_lists = filter(lambda e: e, new_edge_lists)  # remove empty lists

        # Remove old paths
        self.graph.remove_path(p1.id)
        self.graph.remove_path(p2.id)

        # Create new paths
        for new_edge_list in new_edge_lists:
            p = self.graph.create_path(edges=new_edge_list)
            affected_paths.add(p)
            node_to_swap = list(set(p.get_nodes()) & set(old_to_new.keys()))
            assert len(node_to_swap) == 1
            node_to_swap = node_to_swap[0]

            edge_to_swap = list(set(p.edges) & set(node_to_swap.edges))
            assert len(edge_to_swap) == 1
            edge_to_swap = edge_to_swap[0]

            self.graph.swap_edge_node(edge_to_swap, node_to_swap, old_to_new[node_to_swap])

        # Update affectede edges
        new_edges = []
        for affected_edge in affected:
            try:
                node_from = list({affected_edge.source, affected_edge.target} & set(old_to_new.keys()))
                assert len(node_from) == 1
                node_from = node_from[0]
                node_to = old_to_new[node_from]
                other = affected_edge.source if affected_edge.target == node_from else affected_edge.target

                # Make sure you don't make duplicate paths
                if not {node_to, other} in new_edges:
                    self.graph.swap_edge_node(affected_edge, node_from, node_to)
                    new_edges.append({node_to, other})
                    affected_paths.add(affected_edge.path)
                else:
                    self.graph.remove_path(affected_edge.path.id)
            except AssertionError:
                raise

        # Resolve edge segmentation
        affected_paths = list(affected_paths)
        while affected_paths:
            p = affected_paths.pop()
            nodes = p.get_nodes()
            for node in [nodes[0], nodes[-1]]:
                if len(node.edges) == 2:
                    path1, path2 = node.edges[0].path, node.edges[1].path
                    if path1 == path2:
                        continue
                    new_path = self.graph.merge_path(path1, path2)
                    if path1 in affected_paths:
                        affected_paths.remove(path1)
                    if path2 in affected_paths:
                        affected_paths.remove(path2)

                    affected_paths.append(new_path)
        self.graph.visualize(padding=1)
        self.assertEqual(len(self.graph.get_paths()), 4)

if __name__ == '__main__':
    unittest.main()
