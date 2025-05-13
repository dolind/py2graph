import ast

import pytest

from py2graph.parser.methodbody import MethodBodyParser
from py2graph.parser.parser_interface import NodeType


@pytest.fixture
def parser():
    imports = {
        "helper_func": "utils.helper_func",
        "SomeClass": "other_module.SomeClass"
    }
    return MethodBodyParser(imports)


def test_parse_method_body_local_function(parser):
    code = """
def test_method():
    local_func()
    """
    ast_node = ast.parse(code).body[0]
    fqn = "my_module.test_method"
    result, _ = parser.parse(ast_node, fqn)

    assert result.fqn == fqn
    assert result.name == "test_method"
    assert result.entity_type == NodeType.BODY
    assert ("my_module.test_method", "local_func", "uses") in result.relationships


def test_parse_method_body_imported_function(parser):
    code = """
def test_method():
    helper_func()
    """
    ast_node = ast.parse(code).body[0]
    fqn = "my_module.test_method"
    result, defered = parser.parse(ast_node, fqn)

    assert result.fqn == fqn
    assert result.name == "test_method"
    assert result.entity_type == NodeType.BODY
    assert ("my_module.test_method", "utils.helper_func", "uses") in result.relationships


def test_parse_method_body_class_instantiation(parser):
    code = """
def test_method():
    instance = SomeClass()
    """
    ast_node = ast.parse(code).body[0]
    fqn = "my_module.test_method"
    result, _ = parser.parse(ast_node, fqn)

    assert result.fqn == fqn
    assert result.name == "test_method"
    assert result.entity_type == NodeType.BODY
    assert ("my_module.test_method", "other_module.SomeClass", "uses") in result.relationships


def test_parse_method_body_attribute_call(parser):
    code = """
def test_method():
    obj.some_method()
    """
    ast_node = ast.parse(code).body[0]
    fqn = "my_module.test_method"
    result, deferred = parser.parse(ast_node, fqn)

    assert result.fqn == fqn
    assert result.name == "test_method"
    assert result.entity_type == NodeType.BODY
    assert ("my_module.test_method", "obj.some_method", "uses") not in result.relationships


def test_parse_method_body_mixed_calls(parser):
    code = """
def test_method():
    local_func()
    helper_func()
    obj.some_method()
    instance = SomeClass()
    """
    ast_node = ast.parse(code).body[0]
    fqn = "my_module.test_method"
    result, _ = parser.parse(ast_node, fqn)

    assert result.fqn == fqn
    assert result.name == "test_method"
    assert result.entity_type == NodeType.BODY

    expected_relationships = [
        ("my_module.test_method", "local_func", "uses"),
        ("my_module.test_method", "utils.helper_func", "uses"),
        ("my_module.test_method", "other_module.SomeClass", "uses"),
    ]

    for relationship in expected_relationships:
        assert relationship in result.relationships


def test_parse_method_body_no_calls(parser):
    code = """
def test_method():
    x = 42
    """
    ast_node = ast.parse(code).body[0]
    fqn = "my_module.test_method"
    result, _ = parser.parse(ast_node, fqn)

    assert result.fqn == fqn
    assert result.name == "test_method"
    assert result.entity_type == NodeType.BODY
    assert result.relationships == []
