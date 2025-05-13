import ast

import pytest

from py2graph.parser.constructor import ConstructorParser
from py2graph.parser.parser_interface import NodeType, ParsedEntity


@pytest.fixture
def parser():
    imports = {
        "CustomType": "my_module.CustomType",
        "int": "int",
        "str": "str"
    }
    return ConstructorParser(imports)


def test_constructor_with_deferred_attributes(parser):
    """
    Test that attributes in the constructor are deferred for parsing.
    """
    constructor_code = """
class MyClass:
    def __init__(self, value: int):
        self.attr1 = value
        self.attr2: str = "default"
        some_function()
    """
    class_fqn = "my_package.my_module.MyClass"
    constructor_fqn = f"{class_fqn}.__init__"

    tree = ast.parse(constructor_code)
    constructor_ast = tree.body[0].body[0]  # Get the __init__ function

    parsed_entity, deferred = parser.parse(constructor_ast, constructor_fqn)

    # Verify ParsedEntity
    assert parsed_entity.fqn == constructor_fqn
    assert parsed_entity.entity_type == NodeType.CONSTRUCTOR
    assert ("my_package.my_module.MyClass.__init__", "my_package.my_module.MyClass.__init__.attr1",
            "defines") in parsed_entity.relationships

    # Verify deferred parsing
    assert len(deferred) == 2  # Two deferred attributes
    assert deferred[0].fqn == "my_package.my_module.MyClass.__init__.attr1"
    assert deferred[1].fqn == "my_package.my_module.MyClass.__init__.attr2"
    assert deferred[0].context == "attribute"
    assert deferred[1].context == "attribute"


def test_parse_constructor_with_attributes(parser):
    code = """
def __init__(self):
    self.attr1 = 42
    self.attr2: int = 7
    """
    constructor_ast = ast.parse(code).body[0]
    fqn = "my_module.MyClass.__init__"

    parsed_entity, deferred = parser.parse(constructor_ast, fqn)

    # Check deferred parsing for attributes
    assert len(deferred) == 2
    assert deferred[0].fqn == "my_module.MyClass.__init__.attr1"
    assert deferred[1].fqn == "my_module.MyClass.__init__.attr2"

    # Check relationships
    relationships = parsed_entity.relationships
    assert (fqn, "my_module.MyClass.__init__.attr1", "defines") in relationships
    assert (fqn, "my_module.MyClass.__init__.attr2", "defines") in relationships


def test_parse_constructor_with_usage(parser):
    code = """
def __init__(self):
    self.attr1 = CustomType()
    local_func()
    """
    constructor_ast = ast.parse(code).body[0]
    fqn = "my_module.MyClass.__init__"

    parsed_entity, deferred = parser.parse(constructor_ast, fqn)

    # Check relationships
    relationships = parsed_entity.relationships
    assert (fqn, "my_module.CustomType", "uses") in relationships
    assert (fqn, "my_module.local_func", "uses") in relationships


def test_parse_constructor_with_mixed_attributes_and_usage(parser):
    code = """
def __init__(self, price):
    self.attr1 = CustomType()
    self.attr2: int = 10
    another_func()
    self.price: int = price
    """
    constructor_ast = ast.parse(code).body[0]
    fqn = "my_module.MyClass.__init__"

    parsed_entity, deferred = parser.parse(constructor_ast, fqn)

    # Check deferred parsing for attributes
    assert len(deferred) == 3
    assert deferred[0].fqn == "my_module.MyClass.__init__.attr1"
    assert deferred[1].fqn == "my_module.MyClass.__init__.attr2"
    assert deferred[2].fqn == "my_module.MyClass.__init__.price"

    # Check relationships
    relationships = parsed_entity.relationships
    assert (fqn, "my_module.another_func", "uses") in relationships
    assert (fqn, "my_module.MyClass.__init__.attr1", "defines") in relationships


def test_parse_constructor_with_no_attributes_or_usage(parser):
    code = """
def __init__(self):
    pass
    """
    constructor_ast = ast.parse(code).body[0]
    fqn = "my_module.MyClass.__init__"

    parsed_entity, deferred = parser.parse(constructor_ast, fqn)

    # Check attributes and relationships
    assert len(deferred) == 0
    assert len(parsed_entity.relationships) == 0


def test_constructor_parser_attribute_function_call(parser):
    """
    Test the ConstructorParser with a constructor that calls an attribute-based function.
    """
    constructor_code = """
class MyClass:
    def __init__(self):
        obj.some_method()
    """
    module_fqn = "my_package.my_module"
    class_fqn = f"{module_fqn}.MyClass"
    constructor_fqn = f"{class_fqn}.__init__"

    # Parse the constructor
    tree = ast.parse(constructor_code)
    constructor_ast = tree.body[0].body[0]  # Get the __init__ function

    parsed_entity, deferred = parser.parse(constructor_ast, constructor_fqn)

    # Check relationships
    assert isinstance(parsed_entity, ParsedEntity)
    assert parsed_entity.fqn == constructor_fqn
    assert parsed_entity.entity_type == NodeType.CONSTRUCTOR

    # Check that the "uses" relationship is recorded for the method call
    expected_relationship = (constructor_fqn, "obj.some_method", "uses")
    assert expected_relationship in parsed_entity.relationships

    # Check attributes remain empty
    assert len(deferred) == 0
