import ast

import pytest

from py2graph.parser.classparser import ClassParser
from py2graph.parser.parser_interface import NodeType


@pytest.fixture
def class_parser():
    # Example imports for resolving FQNs
    imports = {
        "BaseClass": "my_package.base.BaseClass",
        "OtherClass": "my_package.utils.OtherClass"
    }
    return ClassParser(imports)


def test_parse_class_inheritance(class_parser):
    class_code = """
class MyClass(BaseClass):
    pass
    """
    class_ast = ast.parse(class_code).body[0]
    parsed_entity, deferred = class_parser.parse(class_ast, "my_package.module.MyClass")

    # Check parsed entity
    assert parsed_entity.fqn == "my_package.module.MyClass"
    assert parsed_entity.entity_type == NodeType.CLASS
    assert ("my_package.module.MyClass", "my_package.base.BaseClass", "inherits") in parsed_entity.relationships

    # Check no deferred parsing
    assert len(deferred) == 0


def test_parse_class_with_methods_and_attributes(class_parser):
    class_code = """
class MyClass:
    def __init__(self, param):
        self.attr = param
    def method(self):
        pass
    """
    class_ast = ast.parse(class_code).body[0]
    parsed_entity, deferred = class_parser.parse(class_ast, "my_package.module.MyClass")

    # Check parsed entity
    assert parsed_entity.fqn == "my_package.module.MyClass"
    assert parsed_entity.entity_type == NodeType.CLASS
    assert len(parsed_entity.relationships) == 2
    assert ("my_package.module.MyClass", "my_package.module.MyClass.__init__", "defines") in parsed_entity.relationships
    assert ("my_package.module.MyClass", "my_package.module.MyClass.method", "defines") in parsed_entity.relationships

    # Check deferred parsing
    assert len(deferred) == 2
    assert deferred[0].fqn == "my_package.module.MyClass.__init__"
    assert deferred[0].context == "method"
    assert deferred[1].fqn == "my_package.module.MyClass.method"
    assert deferred[1].context == "method"


def test_parse_class_with_multiple_bases(class_parser):
    class_code = """
class MyClass(BaseClass, OtherClass):
    pass
    """
    class_ast = ast.parse(class_code).body[0]
    parsed_entity, deferred = class_parser.parse(class_ast, "my_package.module.MyClass")

    # Check parsed entity
    assert parsed_entity.fqn == "my_package.module.MyClass"
    assert parsed_entity.entity_type == NodeType.CLASS
    assert ("my_package.module.MyClass", "my_package.base.BaseClass", "inherits") in parsed_entity.relationships
    assert ("my_package.module.MyClass", "my_package.utils.OtherClass", "inherits") in parsed_entity.relationships

    # Check no deferred parsing
    assert len(deferred) == 0


def test_parse_class_with_attributes(class_parser):
    class_code = """
class MyClass:
    attr1: int
    def __init__(self):
        self.attr2 = 42
    """
    class_ast = ast.parse(class_code).body[0]
    parsed_entity, deferred = class_parser.parse(class_ast, "my_package.module.MyClass")

    # Check parsed entity
    assert parsed_entity.fqn == "my_package.module.MyClass"
    assert parsed_entity.entity_type == NodeType.CLASS
    assert ("my_package.module.MyClass", "my_package.module.MyClass.attr1", "defines") in parsed_entity.relationships
    assert ("my_package.module.MyClass", "my_package.module.MyClass.__init__", "defines") in parsed_entity.relationships

    # Check deferred parsing
    assert len(deferred) == 2
    assert deferred[0].fqn == "my_package.module.MyClass.attr1"
    assert deferred[0].context == "attribute"
    assert deferred[1].fqn == "my_package.module.MyClass.__init__"
    assert deferred[1].context == "method"


def test_parse_class_with_no_bases_or_members(class_parser):
    class_code = """
class EmptyClass:
    pass
    """
    class_ast = ast.parse(class_code).body[0]
    parsed_entity, deferred = class_parser.parse(class_ast, "my_package.module.EmptyClass")

    # Check parsed entity
    assert parsed_entity.fqn == "my_package.module.EmptyClass"
    assert parsed_entity.entity_type == NodeType.CLASS
    assert parsed_entity.base_classes == []
    assert parsed_entity.relationships == []

    # Check no deferred parsing
    assert len(deferred) == 0
