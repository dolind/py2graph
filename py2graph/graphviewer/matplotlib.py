import matplotlib.pyplot as plt
import networkx as nx


def visualize_graph(graph, output_file=None):
    """
    Visualize the graph with different shapes for NodeType and colors for edge relationships.

    Args:
        graph (nx.DiGraph): The directed graph to visualize.
        output_file (str): Path to save the visualization as an image. If None, show it interactively.
    """
    # Define node shapes by NodeType
    node_shapes = {
        "MODULE": "s",  # Square
        "CLASS": "o",  # Circle
        "METHOD": "d",  # Diamond
        "ATTRIBUTE": "^",  # Triangle up
        "FUNCTION": "h",  # Hexagon
        "PACKAGE": "p",  # Pentagon
        "PLACEHOLDER": "x"  # Cross
    }

    # Define edge colors by relationship type
    edge_colors = {
        "inherits": "blue",
        "uses": "green",
        "defines": "red",
        "has_type": "orange",
        "imports": "purple",
    }
    plt.figure(figsize=(30, 30))  # Adjust as needed

    pos = nx.spring_layout(graph, k=1, scale=100)  # Positioning of nodes
    color_map = []
    shape_map = {}

    # Separate nodes by shape
    for node_fqn, node_data in graph.nodes(data=True):
        node_type = node_data['data'].node_type.name
        shape = node_shapes.get(node_type, "o")  # Default to circle if not defined
        shape_map.setdefault(shape, []).append(node_fqn)

    # Draw nodes
    for shape, nodes in shape_map.items():
        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=nodes,
            node_shape=shape,
            node_color="skyblue",
            label=shape
        )

    # Draw edges
    edge_color_values = [
        edge_colors.get(data['relation'], "black")  # Default to black if type not defined
        for _, _, data in graph.edges(data=True)
    ]
    nx.draw_networkx_edges(graph, pos, edge_color=edge_color_values)

    # Draw labels
    nx.draw_networkx_labels(graph, pos)

    # Add a legend for edge colors
    legend_elements = [
        plt.Line2D([0], [0], color=color, lw=2, label=relation)
        for relation, color in edge_colors.items()
    ]
    plt.legend(handles=legend_elements, loc="upper left", title="Edge Types")

    if output_file:
        plt.savefig(output_file)
    else:
        plt.show()
