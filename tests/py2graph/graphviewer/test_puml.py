import networkx as nx
import pytest

from py2graph.graphcreator.simplenode import SimpleNode
from py2graph.graphviewer.puml import PumlGenerator
from py2graph.parser.parser_interface import NodeType


@pytest.fixture
def mock_class_graph():
    """
    Creates a mock graph for testing the PUML generation.
    """
    graph = nx.DiGraph()

    # Add classes
    graph.add_node("my_package.my_module.MyClass",
                   data=SimpleNode("my_package.my_module.MyClass", "MyClass", NodeType.CLASS))
    graph.add_node("my_package.my_module.MyClass.attr",
                   data=SimpleNode("my_package.my_module.MyClass.attr", "attr", NodeType.ATTRIBUTE))
    graph.add_node("my_package.my_module.MyClass.method",
                   data=SimpleNode("my_package.my_module.MyClass.method", "method", NodeType.METHOD))
    graph.add_node("abc.ABC", data=SimpleNode("abc.ABC", "ABC", NodeType.PLACEHOLDER))

    # Add relationships for attributes and methods
    graph.add_edge("my_package.my_module.MyClass", "my_package.my_module.MyClass.attr", relation=["defines"])
    graph.add_edge("my_package.my_module.MyClass", "my_package.my_module.MyClass.method", relation=["defines"])
    graph.add_edge("my_package.my_module.MyClass.attr", "int", relation=["has_type"])
    graph.add_edge("my_package.my_module.MyClass.method", "str", relation=["returns", "has_argument"])

    # Add inheritance relationship
    graph.add_edge("my_package.my_module.MyClass", "abc.ABC", relation=["inherits"])

    graph.add_node("my_package.my_module", data=SimpleNode("my_package.my_module", "my_module", NodeType.MODULE))
    graph.add_edge("my_package.my_module", "my_package.my_module.MyClass", relation=["contains"])
    return graph


@pytest.fixture
def mock_method_graph():
    """
    Creates a mock graph for testing the PUML generation.
    """
    graph = nx.DiGraph()

    # Add a module and free methods
    graph.add_node("my_package.my_module", data=SimpleNode("my_package.my_module", "my_module", NodeType.MODULE))
    graph.add_node("my_package.my_module.free_func",
                   data=SimpleNode("my_package.my_module.free_func", "free_func", NodeType.METHOD))

    # Add relationships for the module
    graph.add_edge("my_package.my_module", "my_package.my_module.free_func", relation=["contains"])
    graph.add_edge("my_package.my_module.free_func", "my_package.my_module.MyClass", relation=["uses"])

    return graph


@pytest.fixture
def mock_full_graph():
    """
    Creates a mock graph for testing the PUML generation.
    """
    graph = nx.DiGraph()

    # Add classes
    graph.add_node("my_package.my_module.MyClass",
                   data=SimpleNode("my_package.my_module.MyClass", "MyClass", NodeType.CLASS))
    graph.add_node("my_package.my_module.MyClass.attr",
                   data=SimpleNode("my_package.my_module.MyClass.attr", "attr", NodeType.ATTRIBUTE))
    graph.add_node("my_package.my_module.MyClass.method",
                   data=SimpleNode("my_package.my_module.MyClass.method", "method", NodeType.METHOD))
    graph.add_node("abc.ABC", data=SimpleNode("abc.ABC", "ABC", NodeType.PLACEHOLDER))
    graph.add_node("int", data=SimpleNode("int", "int", NodeType.PLACEHOLDER))
    graph.add_node("str", data=SimpleNode("str", "str", NodeType.PLACEHOLDER))

    # Add relationships for attributes and methods
    graph.add_edge("my_package.my_module.MyClass", "my_package.my_module.MyClass.attr", relation=["defines"])
    graph.add_edge("my_package.my_module.MyClass", "my_package.my_module.MyClass.method", relation=["defines"])
    graph.add_edge("my_package.my_module.MyClass.attr", "int", relation=["has_type"])
    graph.add_edge("my_package.my_module.MyClass.method", "str", relation=["returns", "has_argument"])

    # Add a module and free methods
    graph.add_node("my_package.my_module", data=SimpleNode("my_package.my_module", "my_module", NodeType.MODULE))
    graph.add_node("my_package.my_module.free_func",
                   data=SimpleNode("my_package.my_module.free_func", "free_func", NodeType.METHOD))

    # Add relationships for the module
    graph.add_edge("my_package.my_module", "my_package.my_module.free_func", relation=["contains"])
    graph.add_edge("my_package.my_module", "my_package.my_module.MyClass", relation=["contains"])
    graph.add_edge("my_package.my_module.free_func", "my_package.my_module.MyClass", relation=["uses"])

    # Add inheritance relationship
    graph.add_edge("my_package.my_module.MyClass", "abc.ABC", relation=["inherits"])

    return graph


def test_generate_puml_classes(mock_class_graph):
    """
    Test that the PUML output includes classes with attributes and methods.
    """
    generator = PumlGenerator(mock_class_graph, "TestDiagram")
    puml_content = generator.generate()
    print(puml_content)
    assert "abstract class my_package.my_module.MyClass {" in puml_content
    assert "attr: int" in puml_content
    assert "method(str) -> str" in puml_content


def test_generate_puml_free_methods(mock_method_graph):
    """
    Test that the PUML output includes free methods in module annotations.
    """
    generator = PumlGenerator(mock_method_graph, "TestDiagram")
    puml_content = generator.generate()
    assert "annotation my_package.my_module.Methods {" in puml_content
    assert "free_func() -> None" in puml_content


def test_generate_puml_relationships(mock_full_graph):
    """
    Test that the PUML output includes relationships between nodes.
    """
    generator = PumlGenerator(mock_full_graph, "TestDiagram")
    puml_content = generator.generate()
    assert "my_package.my_module.Methods --> my_package.my_module.MyClass: used by free_func" in puml_content


def test_generate_puml_structure(mock_full_graph):
    """
    Test that the PUML output includes proper file structure with start and end tags.
    """
    generator = PumlGenerator(mock_full_graph, "TestDiagram")
    puml_content = generator.generate()
    assert puml_content.startswith("@startuml TestDiagram")
    assert "footer Generated by //CodebaseGraph//" in puml_content
    assert puml_content.endswith("@enduml")


def test_generate_puml_empty_graph():
    """
    Test that the PUML output handles an empty graph.
    """
    empty_graph = nx.DiGraph()
    generator = PumlGenerator(empty_graph, "EmptyDiagram")
    puml_content = generator.generate()
    assert puml_content == "@startuml EmptyDiagram\n!pragma useIntermediatePackages false\nskinparam linetype ortho\n\nfooter Generated by //CodebaseGraph//\n@enduml"
