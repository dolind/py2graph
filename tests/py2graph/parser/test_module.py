import ast

import pytest

from py2graph.parser.moduleparser import ModuleParser
from py2graph.parser.parser_interface import NodeType


@pytest.fixture
def module_code():
    return """
import os
from typing import List
from test_package.submodule import MyClass as AliasClass
from test_package.submodule2 import MyClass2
from test_package.xyz.subsubpackage import MyClass3
class MyClass:
    def __init__(self):
        pass

def my_function():
    pass
"""


# def test_package_double_import_parser(module_code):
#     code = """
# from abc import ABC, abstractmethod
#
#         """
#     ast_node = ast.parse(code)
#     module_fqn = "test_package.test_module"
#
#     parser = ModuleParser()
#     parsed_entities, deferred_parsing = parser.parse(ast_node, module_fqn)
#     import_relationships = [rel for rel in parsed_entities.relationships if rel[2] == "imports"]
#     assert len(import_relationships) == 2  # os, List, AliasClass
#     assert ("test_package.test_module", "test_package.submodule2.MyClass2", "imports") in import_relationships
#     assert ("test_package.test_module", "test_package.submodule.MyClass", "imports") in import_relationships
#

def test_package_parser(module_code):
    # Parse the module code to an AST
    module_ast = ast.parse(module_code)
    module_fqn = "test_package.test_module"

    # Initialize the parser
    parser = ModuleParser()

    # Parse the module
    parsed_entities, deferred_parsing = parser.parse(module_ast, module_fqn)

    # Assertions for parsed entities
    module_entity = parsed_entities
    assert module_entity.fqn == module_fqn
    assert module_entity.name == "test_module"
    assert module_entity.entity_type == NodeType.MODULE

    # Check relationships
    import_relationships = [rel for rel in module_entity.relationships if rel[2] == "imports"]
    contains_relationships = [rel for rel in module_entity.relationships if rel[2] == "contains"]

    assert len(import_relationships) == 5  # os, List, AliasClass
    assert ("test_package.test_module", "test_package.submodule2.MyClass2", "imports") in import_relationships
    assert ("test_package.test_module", "test_package.submodule.MyClass", "imports") in import_relationships

    assert len(contains_relationships) == 2  # MyClass and my_function
    assert ("test_package.test_module", "test_package.test_module.MyClass", "contains") in contains_relationships
    assert ("test_package.test_module", "test_package.test_module.my_function", "contains") in contains_relationships

    # Assertions for deferred parsing
    assert len(deferred_parsing) == 2
    class_deferred = next((dp for dp in deferred_parsing if dp.context == "class"), None)
    function_deferred = next((dp for dp in deferred_parsing if dp.context == "method"), None)

    assert class_deferred is not None
    assert class_deferred.fqn == "test_package.test_module.MyClass"
    assert isinstance(class_deferred.node, ast.ClassDef)

    assert function_deferred is not None
    assert function_deferred.fqn == "test_package.test_module.my_function"
    assert isinstance(function_deferred.node, ast.FunctionDef)

    # Verify imports are passed to deferred parsing expressions
    assert class_deferred.imported_fqn == {
        "AliasClass": "test_package.submodule.MyClass",
        "List": "typing.List",
        "MyClass2": "test_package.submodule2.MyClass2",
        "MyClass3": "test_package.xyz.subsubpackage.MyClass3",
        "os": "os",
    }
    assert function_deferred.imported_fqn == {
        "AliasClass": "test_package.submodule.MyClass",
        "List": "typing.List",
        "MyClass2": "test_package.submodule2.MyClass2",
        "MyClass3": "test_package.xyz.subsubpackage.MyClass3",
        "os": "os",
    }
