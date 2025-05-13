import ast

from py2graph.parser.helper import resolve_nested_attribute, resolve_type, identify_root_package
from py2graph.parser.parser_interface import IParser, ParsedEntity, NodeType


class MethodBodyParser(IParser):
    def __init__(self, imports):
        super().__init__(imports)

    def parse(self, ast_node, fqn):
        """
        Parse a method body to detect usage of classes, functions, or other entities.
        """
        relationships = []
        for node in ast.walk(ast_node):
            if isinstance(node, ast.Call):  # Handle calls to methods or constructors
                if isinstance(node.func, ast.Name):  # Local function or class
                    target_fqn = resolve_type(node.func.id, self.imports)
                    relationships.append((fqn, target_fqn, "uses"))

                elif isinstance(node.func, ast.Attribute):  # Object or module attribute
                    # Skip normal object calls that don't match imports
                    root_name = identify_root_package(node)
                    if root_name not in self.imports:
                        continue  # Ignore non-imported object calls

                    # Resolve nested attributes
                    target_fqn = resolve_nested_attribute(node.func)
                    relationships.append((fqn, target_fqn, "uses"))

        return ParsedEntity(
            fqn=fqn,
            name=fqn.split('.')[-1],
            entity_type=NodeType.BODY,
            relationships=relationships
        ), []
