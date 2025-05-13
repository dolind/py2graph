from typing import Dict, Type, List

import networkx as nx

from py2graph.graphcreator.simplenode import SimpleNode
from py2graph.parser.package import PackageParser
from py2graph.parser.parser_interface import IParser, NodeType


class GraphCreator:
    def __init__(self, graph: nx.DiGraph, parser_to_use: Dict[str, Type[IParser]]):
        self.graph = graph
        self.deferred = []
        self.parser = parser_to_use
        self.parser["package"] = PackageParser

    def parse_package(self, package_path: str, package_name: str) -> None:
        """
        Parse the given package and update the graph by adding entities and resolving deferred items.

        Args:
            package_path (str): The path to the package to be parsed.
            package_name (str): The name of the package to be parsed.

        Returns:
            None
        """
        parser = self.parser["package"](package_path)
        entities, deferred = parser.parse("", package_name)
        for entity in entities:
            self._add_to_graph(entity)
        self.deferred.extend(deferred)

        self._parse_deferred()

        self.graph = link_upwards(self.graph, package_name)
        inconsistent_nodes = self._check_graph_consistency(package_name)

        if inconsistent_nodes:
            print("Inconsistent nodes found (placeholders):")
            # TODO: need to check what kind of method is expected. what is the difference between int and sum().
            # currently int leads to int, whereas sum() leads to package.sum
            for node_fqn in inconsistent_nodes:
                print(f"- {node_fqn}")
        else:
            print("Graph is consistent. No placeholders remain.")

    def _parse_deferred(self):
        while self.deferred:
            deferred_expression = self.deferred.pop(0)
            next_parser = self.parser[deferred_expression.context](deferred_expression.imported_fqn)
            entity, more_deferred = next_parser.parse(deferred_expression.node, deferred_expression.fqn)
            self._add_to_graph(entity)
            self.deferred.extend(more_deferred)

    def _add_to_graph(self, entity):
        if entity.fqn in self.graph:
            existing_node = self.graph.nodes[entity.fqn]['data']
            if existing_node.node_type == NodeType.PLACEHOLDER:
                self.graph.nodes[entity.fqn]['data'] = SimpleNode(entity.fqn, entity.name, entity.entity_type)
        else:
            self.graph.add_node(entity.fqn, data=SimpleNode(entity.fqn, entity.name, entity.entity_type))

        for source, target, relation in entity.relationships:
            target = target or 'None'

            # Resolve target module if necessary
            # spaghetti code, we search for the module by brute force
            # first look in the same class, then module, then package
            if "." not in target:
                for i in range(1, 4):
                    source_module = '.'.join(source.split('.')[:-i])
                    real_target = f"{source_module}.{target}"
                    if real_target in self.graph:
                        target = real_target
                        break

            # Add placeholder node if target doesn't exist
            if target not in self.graph:
                self.graph.add_node(target, data=SimpleNode(target, target.split('.')[-1], NodeType.PLACEHOLDER))

            # Add or update edge
            if not self.graph.has_edge(source, target):
                self.graph.add_edge(source, target, relation=[relation])
            else:
                existing_data = self.graph.get_edge_data(source, target)['relation']
                existing_data.append(relation)
                self.graph.add_edge(source, target, relation=existing_data)

    def _check_graph_consistency(self, package_name: str = '') -> List[str]:
        inconsistent_nodes = []

        for node_fqn, node_data in self.graph.nodes(data=True):
            if node_data['data'].node_type == NodeType.PLACEHOLDER and package_name in node_fqn:
                inconsistent_nodes.append(node_fqn)
        return inconsistent_nodes


def link_upwards(graph, root_package_fqn):
    """
    Links attributes, methods, and method bodies upwards to their respective classes or packages.

    Args:
        graph (nx.DiGraph): The directed graph representing the codebase.
        root_package_fqn (str): Fully-qualified name of the root package to check for type containment.
    """
    for node_fqn, node_data in graph.nodes(data=True):
        node = node_data['data']
        # TODO: savely add the relation
        if node.node_type == NodeType.ATTRIBUTE:
            # Handle attributes: link to class with a "defines" relationship
            if "__init__" in node_fqn:
                class_fqn = '.'.join(node_fqn.split('.')[:-2])
            else:
                class_fqn = '.'.join(node_fqn.split('.')[:-1])
            for edge_target, edge_data in graph.succ[node_fqn].items():
                # only choose one
                if 'aggregation' in edge_data['relation'] :
                    graph.add_edge(class_fqn, edge_target, relation=["aggregation"])
                elif 'composition' in edge_data['relation']:
                    graph.add_edge(class_fqn, edge_target, relation=["composition"])
                elif ('has_type' in edge_data['relation'] or 'has_compound_type' in edge_data[
                    'relation']) and edge_target.startswith(root_package_fqn):
                    graph.add_edge(class_fqn, edge_target, relation=["has_attribute_with_type"])

    attribute_edges = ['composition', 'aggregation', 'has_attribute_with_type']

    # check that no duplicate edges are in the graph
    for node_fqn, node_data in graph.nodes(data=True):
        node = node_data['data']
        if node.node_type == NodeType.CLASS:
            # Dictionary to track if a word from attribute_edges is already added
            selected_edge = None

            # Iterate through successor edges
            for edge_target, edge_data in graph.succ[node_fqn].items():
                relations = edge_data['relation']  # Assuming relation is a list
                attribute_found = [word for word in relations if word in attribute_edges]

                if attribute_found:
                    # Choose the strongest relation from attribute_edges
                    if not selected_edge or attribute_edges.index(attribute_found[0]) < attribute_edges.index(
                            selected_edge):
                        selected_edge = attribute_found[0]

                    # Remove weaker attribute relations
                    edge_data['relation'] = [r for r in relations if r not in attribute_edges] + [selected_edge]
                else:
                    # Retain other non-attribute relations
                    edge_data['relation'] = relations
        #
        # elif node.node_type == NodeType.METHOD:
        #     # Handle class methods and their uses
        #     class_fqn = '.'.join(node_fqn.split('.')[:-1])
        #     for edge_target, edge_data in graph.succ[node_fqn].items():
        #         if "argument_of" in edge_data['relation'] or "returns" in edge_data['relation'] and edge_target.startswith(root_package_fqn):
        #             graph.add_edge(class_fqn, edge_target, relation=["has_method_argument_with_type"])
        #
        # elif node.node_type == NodeType.BODY:
        #     # For method bodies: inherit "uses" relationships
        #     class_fqn = '.'.join(node_fqn.split('.')[:-1])
        #     for edge_target, edge_data in graph.succ[node_fqn].items():
        #         if "uses" in edge_data['relation'] :
        #             graph.add_edge(class_fqn, edge_target, relation=["uses"])
        #
        # elif node.node_type == NodeType.CONSTRUCTOR:
        #     # Handle constructor methods
        #     class_fqn = '.'.join(node_fqn.split('.')[:-1])
        #     for edge_target, edge_data in graph.succ[node_fqn].items():
        #         if "defines" in edge_data['relation'] and edge_target.startswith(root_package_fqn):
        #             graph.add_edge(class_fqn, edge_target, relation=["defines"])
        #         elif "argument_of" in edge_data['relation'] or "returns" in edge_data['relation'] and edge_target.startswith(root_package_fqn):
        #             graph.add_edge(class_fqn, edge_target, relation=["uses"])
        #
        #     # Constructor body "uses" relationships
        #     for edge_source, edge_data in graph.pred[node_fqn].items():
        #         if "uses" in edge_data['relation']:
        #             graph.add_edge(class_fqn, edge_source, relation=["uses"])

    return graph
