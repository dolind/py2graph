import networkx as nx
import pytest

from py2graph.graphcreator.graphcreator import GraphCreator, link_upwards
from py2graph.graphcreator.simplenode import SimpleNode
from py2graph.parser.parser_interface import DeferredParsingExpression, ParsedEntity, NodeType


@pytest.fixture
def mock_parsers():
    """
    Mock parsers for testing.
    """

    class MockParser:
        def __init__(self, imports):
            pass

        def parse(self, node, fqn):
            # Mock parse to return a simple ParsedEntity and no deferred parsing
            entity = ParsedEntity(
                fqn=fqn,
                name=fqn.split('.')[-1],
                entity_type=NodeType.CLASS,
                relationships=[]
            )
            return entity, []

    return {"class": MockParser, "function": MockParser, "attribute": MockParser}


@pytest.fixture
def example_graph():
    """
    Create an example graph.
    """
    graph = nx.DiGraph()
    graph.add_node(
        "example.package",
        data=SimpleNode(fqn="example.package", name="package", node_type=NodeType.PACKAGE)
    )
    return graph


@pytest.fixture
def orchestrator(example_graph, mock_parsers):
    """
    Create an Orchestrator instance for testing.
    """
    return GraphCreator(graph=example_graph, parser_to_use=mock_parsers)


#
# def test_parse_package(orchestrator):
#     """
#     Test the `parse_package` function.
#     """
#     # Mock the PackageParser to return example entities and deferred parsing
#     mock_parser = mocker.Mock()
#     mock_parser.parse.return_value = (
#         [
#             ParsedEntity(
#                 fqn="example.package.module",
#                 name="module",
#                 entity_type=NodeType.MODULE,
#                 relationships=[]
#             )
#         ],
#         [
#             DeferredParsingExpression(
#                 fqn="example.package.module.class",
#                 node=None,
#                 context="class",
#                 imported_fqn={}
#             )
#         ]
#     )
#     orchestrator.parser["package"] = mock_parser
#     orchestrator.parse_package("path/to/package", "example.package")
#
#     # Check that the graph was updated with the new module
#     assert "example.package.module" in orchestrator.graph
#     assert orchestrator.graph.nodes["example.package.module"]["data"].name == "module"
#
#     # Check deferred parsing
#     assert len(orchestrator.deferred) == 1
#     deferred = orchestrator.deferred[0]
#     assert deferred.fqn == "example.package.module.class"
#     assert deferred.context == "class"


def test_add_to_graph(orchestrator):
    """
    Test the `_add_to_graph` function.
    """
    entities = ParsedEntity(
        fqn="example.package.Class",
        name="Class",
        entity_type=NodeType.CLASS,
        relationships=[("example.package.Class", "example.package.OtherClass", "inherits")]
    )

    orchestrator._add_to_graph(entities)

    # Check that the class node is added
    assert "example.package.Class" in orchestrator.graph
    node = orchestrator.graph.nodes["example.package.Class"]["data"]
    assert node.name == "Class"
    assert node.node_type == NodeType.CLASS

    # Check that the edge is added
    assert ("example.package.Class", "example.package.OtherClass") in orchestrator.graph.edges


def test_parse_deferred(orchestrator):
    """
    Test the `_parse_deferred` function.
    """
    orchestrator.deferred = [
        DeferredParsingExpression(
            fqn="example.package.Class",
            node=None,
            context="class",
            imported_fqn={}
        )
    ]

    orchestrator._parse_deferred()

    # Check that deferred parsing is processed and the graph is updated
    assert "example.package.Class" in orchestrator.graph
    node = orchestrator.graph.nodes["example.package.Class"]["data"]
    assert node.name == "Class"
    assert node.node_type == NodeType.CLASS


def test_check_graph_consistency(orchestrator):
    """
    Test the `_check_graph_consistency` function.
    """
    orchestrator.graph.add_node(
        "example.placeholder",
        data=SimpleNode(fqn="example.placeholder", name="placeholder", node_type=NodeType.PLACEHOLDER)
    )

    inconsistent_nodes = orchestrator._check_graph_consistency()

    assert len(inconsistent_nodes) == 1
    assert inconsistent_nodes[0] == "example.placeholder"


def test_link_upwards(orchestrator):
    """
    Test the `link_upwards` function.
    """
    orchestrator.graph.add_node(
        "mypackage.mymodule.Class1.attr1",
        data=SimpleNode(fqn="mypackage.mymodule.Class1.attr1", name="attr1", node_type=NodeType.ATTRIBUTE)
    )
    orchestrator.graph.add_node(
        "mypackage.mymodule2.Class2",
        data=SimpleNode(fqn="mypackage.mymodule2.Class2", name="Class2", node_type=NodeType.CLASS)
    )
    orchestrator.graph.add_node(
        "mypackage.mymodule.Class1",
        data=SimpleNode(fqn="mypackage.mymodule.Class1", name="Class1", node_type=NodeType.CLASS)
    )
    orchestrator.graph.add_edge(
        "mypackage.mymodule.Class1.attr1", "mypackage.mymodule2.Class2", relation="has_type"
    )
    orchestrator.graph.add_edge(
        "mypackage.mymodule.Class1", "mypackage.mymodule.Class1.attr1", relation="defines"
    )
    newgraph = link_upwards(orchestrator.graph, "mypackage")

    # Check that the "defines" relationship is added

    edge_data = newgraph.get_edge_data("mypackage.mymodule.Class1", "mypackage.mymodule2.Class2")
    assert "has_attribute_with_type" in edge_data["relation"]
