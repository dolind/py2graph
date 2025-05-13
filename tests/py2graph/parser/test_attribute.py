import ast

import pytest

from py2graph.parser.attribute import AttributeParser
from py2graph.parser.parser_interface import NodeType


@pytest.fixture
def parser():
    imports = {
        "CustomType": "my_module.CustomType",
        "int": "int"
    }
    return AttributeParser(imports)


def test_parse_annotated_attribute(parser):
    code = """
attr1: int
    """
    class_ast = ast.parse(code)
    ann_assign_node = class_ast.body[0]  # The annotated assignment node
    fqn = "my_module.MyClass.attr1"

    result, _ = parser.parse(ann_assign_node, fqn)

    assert result is not None
    assert result.fqn == "my_module.MyClass.attr1"
    assert result.name == "attr1"
    assert result.entity_type == NodeType.ATTRIBUTE
    assert (result.fqn, "int", "has_type") in result.relationships


def test_parse_regular_assignment(parser):
    code = """
class MyClass:
    attr1 = 42
    """
    class_ast = ast.parse(code).body[0]
    assign_node = class_ast.body[0]  # The assignment node
    fqn = "my_module.MyClass.attr1"

    result, _ = parser.parse(assign_node, fqn)

    assert result is not None
    assert result.fqn == "my_module.MyClass.attr1"
    assert result.name == "attr1"
    assert result.entity_type == NodeType.ATTRIBUTE
    assert (result.fqn, "int", "has_type") in result.relationships


def test_parse_imported_type(parser):
    code = """
class MyClass:
    attr1: CustomType
    """
    class_ast = ast.parse(code).body[0]
    ann_assign_node = class_ast.body[0]  # The annotated assignment node
    fqn = "my_module.MyClass.attr1"

    result, _ = parser.parse(ann_assign_node, fqn)

    assert result is not None
    assert result.fqn == "my_module.MyClass.attr1"
    assert result.name == "attr1"
    assert result.entity_type == NodeType.ATTRIBUTE
    assert (result.fqn, "my_module.CustomType", "has_type") in result.relationships


def test_parse_constructor_assignment_composition(parser):
    code = """
def __init__(self):
    self.attr: Value = Value()
    """
    class_ast = ast.parse(code).body[0]
    assign_node = class_ast.body[0]  # The assignment node
    fqn = "my_module.MyClass.__init__.attr"

    result, _ = parser.parse(assign_node, fqn)

    assert result is not None
    assert result.fqn == "my_module.MyClass.__init__.attr"
    assert result.name == "attr"
    assert result.entity_type == NodeType.ATTRIBUTE
    assert (result.fqn, "Value", "has_type") in result.relationships
    assert (result.fqn, "Value", "composition") in result.relationships

def test_parse_constructor_assignment_aggregation(parser):
    code = """
def __init__(self, value:Value):
    self.attr: Value = value
    """
    class_ast = ast.parse(code).body[0]
    assign_node = class_ast.body[0]  # The assignment node
    fqn = "my_module.MyClass.__init__.attr"

    result, _ = parser.parse(assign_node, fqn)

    assert result is not None
    assert result.fqn == "my_module.MyClass.__init__.attr"
    assert result.name == "attr"
    assert result.entity_type == NodeType.ATTRIBUTE
    assert (result.fqn, "Value", "has_type") in result.relationships
    assert (result.fqn, "Value", "aggregation") in result.relationships
def test_parse_constructor_assignment(parser):
    code = """
def __init__(self):
    self.attr: int = 2
    """
    class_ast = ast.parse(code).body[0]
    assign_node = class_ast.body[0]  # The assignment node
    fqn = "my_module.MyClass.__init__.attr"

    result, _ = parser.parse(assign_node, fqn)

    assert result is not None
    assert result.fqn == "my_module.MyClass.__init__.attr"
    assert result.name == "attr"
    assert result.entity_type == NodeType.ATTRIBUTE
    assert (result.fqn, "int", "has_type") in result.relationships


def test_parse_constructor_regular_assignment(parser):
    code = """
def __init__(self):
    self.attr2 = 2
    """
    class_ast = ast.parse(code).body[0]
    assign_node = class_ast.body[0]  # The assignment node

    fqn = "my_module.MyClass.__init__.attr2"

    result, _ = parser.parse(assign_node, fqn)

    assert result is not None
    assert result.fqn == "my_module.MyClass.__init__.attr2"
    assert result.name == "attr2"
    assert result.entity_type == NodeType.ATTRIBUTE
    assert (result.fqn, "int", "has_type") in result.relationships


def test_parse_regular_assignment_with_no_value(parser):
    code = """
class MyClass:
    attr1 = None
    """
    class_ast = ast.parse(code).body[0]
    assign_node = class_ast.body[0]  # The assignment node
    fqn = "my_module.MyClass.attr1"

    result, _ = parser.parse(assign_node, fqn)

    assert result is not None
    assert result.fqn == "my_module.MyClass.attr1"
    assert result.name == "attr1"
    assert result.entity_type == NodeType.ATTRIBUTE
    assert (result.fqn, "NoneType", "has_type") in result.relationships


def test_parse_enum(parser):
    code = """
  
class RelType(Enum):
    COMPOSITION = '*'   
    """
    class_ast = ast.parse(code).body[0]
    assign_node = class_ast.body[0]  # The assignment node
    fqn = "my_module.RelType.COMPOSITION"

    result, _ = parser.parse(assign_node, fqn)

    assert result is not None
    assert result.fqn == "my_module.RelType.COMPOSITION"
    assert result.name == "COMPOSITION"
    assert result.entity_type == NodeType.ATTRIBUTE
    assert (result.fqn, "str", "has_type") in result.relationships