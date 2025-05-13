import networkx as nx

from py2graph.graphcreator.simplenode import SimpleNode
from py2graph.graphviewer.matplotlib import visualize_graph
from py2graph.parser.parser_interface import NodeType

# Example: Create a graph with dummy nodes and edges
graph = nx.DiGraph()

# Adding nodes
graph.add_node("module1", data=SimpleNode(fqn="module1", name="Module1", node_type=NodeType.MODULE))
graph.add_node("class1", data=SimpleNode(fqn="class1", name="Class1", node_type=NodeType.CLASS))
graph.add_node("method1", data=SimpleNode(fqn="method1", name="Method1", node_type=NodeType.METHOD))

# Adding edges
graph.add_edge("module1", "class1", relation="contains")
graph.add_edge("class1", "method1", relation="defines")

# Visualize the graph
visualize_graph(graph, output_file="graph_visualization.png")
