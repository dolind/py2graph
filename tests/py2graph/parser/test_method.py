import ast

import pytest

from py2graph.parser.method import MethodParser
from py2graph.parser.parser_interface import NodeType


@pytest.fixture
def method_parser():
    # Example imports for resolving FQNs
    imports = {
        "CustomType": "my_package.types.CustomType",
        "Optional": "typing.Optional",
    }
    return MethodParser(imports)


def test_parse_method_with_arguments_and_return_type(method_parser):
    method_code = """
def my_method(param1: int, param2: CustomType) -> str:
    pass
    """
    method_ast = ast.parse(method_code).body[0]
    parsed_entity, deferred = method_parser.parse(method_ast, "my_package.module.MyClass.my_method")

    # Check parsed entity
    assert parsed_entity.fqn == "my_package.module.MyClass.my_method"
    assert parsed_entity.entity_type == NodeType.METHOD
    assert ("my_package.module.MyClass.my_method", "int", "has_argument") in parsed_entity.relationships
    assert ("my_package.module.MyClass.my_method", "my_package.types.CustomType",
            "has_argument") in parsed_entity.relationships
    assert ("my_package.module.MyClass.my_method", "str", "returns") in parsed_entity.relationships

    # Check deferred parsing
    assert len(deferred) == 1
    assert deferred[0].fqn == "my_package.module.MyClass.my_method"
    assert deferred[0].context == "body"


def test_parse_method_with_union_arguments_and_return_type_2(method_parser):
    method_code = """
def my_method(param1: int| CustomType, param2: CustomType) -> int| CustomType:
    pass
    """
    method_ast = ast.parse(method_code).body[0]
    parsed_entity, deferred = method_parser.parse(method_ast, "my_package.module.MyClass.my_method")

    # Check parsed entity
    assert parsed_entity.fqn == "my_package.module.MyClass.my_method"
    assert parsed_entity.entity_type == NodeType.METHOD
    assert ("my_package.module.MyClass.my_method", "int", "has_argument") in parsed_entity.relationships
    assert ("my_package.module.MyClass.my_method", "my_package.types.CustomType",
            "has_argument") in parsed_entity.relationships
    assert ("my_package.module.MyClass.my_method", "my_package.types.CustomType",
            "has_argument") in parsed_entity.relationships
    assert ("my_package.module.MyClass.my_method", "int", "returns") in parsed_entity.relationships
    assert ("my_package.module.MyClass.my_method", "my_package.types.CustomType",
            "returns") in parsed_entity.relationships

    # Check deferred parsing
    assert len(deferred) == 1
    assert deferred[0].fqn == "my_package.module.MyClass.my_method"
    assert deferred[0].context == "body"


def test_parse_constructor(method_parser):
    method_code = """
def __init__(self):
    pass
    """
    method_ast = ast.parse(method_code).body[0]
    parsed_entity, deferred = method_parser.parse(method_ast, "my_package.module.MyClass.__init__")

    # Check parsed entity
    assert parsed_entity.fqn == "my_package.module.MyClass.__init__"
    assert parsed_entity.entity_type == NodeType.METHOD
    assert len(parsed_entity.relationships) == 0  # No arguments or return type

    # Check deferred parsing
    assert len(deferred) == 1
    assert deferred[0].fqn == "my_package.module.MyClass.__init__"
    assert deferred[0].context == "constructor"


def test_parse_method_without_arguments_or_return_type(method_parser):
    method_code = """
def my_method():
    pass
    """
    method_ast = ast.parse(method_code).body[0]
    parsed_entity, deferred = method_parser.parse(method_ast, "my_package.module.MyClass.my_method")

    # Check parsed entity
    assert parsed_entity.fqn == "my_package.module.MyClass.my_method"
    assert parsed_entity.entity_type == NodeType.METHOD
    assert len(parsed_entity.relationships) == 0  # No arguments or return type

    # Check deferred parsing
    assert len(deferred) == 1
    assert deferred[0].fqn == "my_package.module.MyClass.my_method"
    assert deferred[0].context == "body"


def test_parse_method_with_optional_argument(method_parser):
    method_code = """
def my_method(param1: Optional[int]) -> None:
    pass
    """
    method_ast = ast.parse(method_code).body[0]
    parsed_entity, deferred = method_parser.parse(method_ast, "my_package.module.MyClass.my_method")

    # Check parsed entity
    assert parsed_entity.fqn == "my_package.module.MyClass.my_method"
    assert parsed_entity.entity_type == NodeType.METHOD
    assert ("my_package.module.MyClass.my_method", "Optional[int]", "has_argument") in parsed_entity.relationships
    assert ("my_package.module.MyClass.my_method", "None", "returns") in parsed_entity.relationships

    # Check deferred parsing
    assert len(deferred) == 1
    assert deferred[0].fqn == "my_package.module.MyClass.my_method"
    assert deferred[0].context == "body"


def test_parse_method_with_no_arguments_but_return_type(method_parser):
    method_code = """
def my_method() -> CustomType:
    pass
    """
    method_ast = ast.parse(method_code).body[0]
    parsed_entity, deferred = method_parser.parse(method_ast, "my_package.module.MyClass.my_method")

    # Check parsed entity
    assert parsed_entity.fqn == "my_package.module.MyClass.my_method"
    assert parsed_entity.entity_type == NodeType.METHOD
    assert ("my_package.module.MyClass.my_method", "my_package.types.CustomType",
            "returns") in parsed_entity.relationships

    # Check deferred parsing
    assert len(deferred) == 1
    assert deferred[0].fqn == "my_package.module.MyClass.my_method"
    assert deferred[0].context == "body"


def test_parse_method_with_unknown_argument_and_return_type(method_parser):
    method_code = """
def my_method(param1: UnknownType) -> AnotherUnknown:
    pass
    """
    method_ast = ast.parse(method_code).body[0]
    parsed_entity, deferred = method_parser.parse(method_ast, "my_package.module.MyClass.my_method")

    # Check parsed entity
    assert parsed_entity.fqn == "my_package.module.MyClass.my_method"
    assert parsed_entity.entity_type == NodeType.METHOD
    assert ("my_package.module.MyClass.my_method", "UnknownType", "has_argument") in parsed_entity.relationships
    assert ("my_package.module.MyClass.my_method", "AnotherUnknown", "returns") in parsed_entity.relationships

    # Check deferred parsing
    assert len(deferred) == 1
    assert deferred[0].fqn == "my_package.module.MyClass.my_method"
    assert deferred[0].context == "body"
