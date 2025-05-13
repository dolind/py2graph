import pytest

from py2graph.graphcreator.simplenode import NodeType, SimpleNode  # Replace `your_module` with the actual module name.


### Tests for NodeType Enum ###

def test_node_type_enum_values():
    """
    Test that NodeType enum contains the correct values.
    """
    assert NodeType.PACKAGE.value == "package"
    assert NodeType.MODULE.value == "module"
    assert NodeType.CLASS.value == "class"
    assert NodeType.METHOD.value == "method"
    assert NodeType.ATTRIBUTE.value == "attribute"
    assert NodeType.PLACEHOLDER.value == "placeholder"
    assert NodeType.TYPE.value == "type"


def test_node_type_enum_members():
    """
    Test that NodeType enum has the correct members.
    """
    members = [member for member in NodeType]
    assert NodeType.PACKAGE in members
    assert NodeType.MODULE in members
    assert NodeType.CLASS in members
    assert NodeType.METHOD in members
    assert NodeType.ATTRIBUTE in members
    assert NodeType.PLACEHOLDER in members
    assert NodeType.TYPE in members


### Tests for SimpleNode Class ###

def test_simple_node_creation():
    """
    Test the creation of a SimpleNode instance.
    """
    node = SimpleNode(fqn="module.Class", name="Class", node_type=NodeType.CLASS)
    assert node.fqn == "module.Class"
    assert node.name == "Class"
    assert node.node_type == NodeType.CLASS


def test_simple_node_hash():
    """
    Test the hash functionality of SimpleNode.
    """
    node1 = SimpleNode(fqn="module.Class", name="Class", node_type=NodeType.CLASS)
    node2 = SimpleNode(fqn="module.Class", name="Class", node_type=NodeType.CLASS)
    assert hash(node1) == hash(node2)


def test_simple_node_equality():
    """
    Test the equality of two SimpleNode instances.
    """
    node1 = SimpleNode(fqn="module.Class", name="Class", node_type=NodeType.CLASS)
    node2 = SimpleNode(fqn="module.Class", name="Class", node_type=NodeType.CLASS)
    node3 = SimpleNode(fqn="module.OtherClass", name="OtherClass", node_type=NodeType.CLASS)
    assert node1 == node2
    assert node1 != node3


def test_simple_node_repr():
    """
    Test the string representation (__repr__) of SimpleNode.
    """
    node = SimpleNode(fqn="module.Class", name="Class", node_type=NodeType.CLASS)
    assert repr(node) == "ClassNode(Class)"


def test_simple_node_type_safety():
    """
    Test that creating a SimpleNode with an invalid node_type raises an error.
    """
    with pytest.raises(ValueError):
        SimpleNode(fqn="module.Class", name="Class", node_type="invalid_type")
