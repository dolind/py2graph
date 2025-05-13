import ast

from py2graph.parser.parser_interface import IParser, DeferredParsingExpression, ParsedEntity, NodeType


class ConstructorParser(IParser):
    def __init__(self, imports):
        super().__init__(imports)

    def parse(self, ast_node, fqn):
        """
        Parse a constructor (__init__) to detect attributes, usage of other entities,
        and method calls, deferring attributes to the AttributeParser.
        """
        relationships = []
        deferred_parsing = []

        for node in ast.walk(ast_node):
            # Handle attributes assigned to `self`
            if isinstance(node, (ast.Assign, ast.AnnAssign)):  # Handle self-attributes
                target = node.target if isinstance(node, ast.AnnAssign) else node.targets[0]
                if isinstance(target, ast.Attribute) and isinstance(target.value,
                                                                    ast.Name) and target.value.id == "self":
                    attr_fqn = f"{fqn}.{target.attr}"
                    deferred_parsing.append(
                        DeferredParsingExpression(fqn=attr_fqn, node=node, context="attribute",
                                                  imported_fqn=self.imports)
                    )
                    relationships.append((fqn, attr_fqn, "defines"))
                    relationships.append((".".join(fqn.split(".")[:-1]), attr_fqn, "defines"))


            elif isinstance(node, ast.Call):  # Handle entity usage
                func = node.func
                if isinstance(func, ast.Name) and func.id != "super":
                    target_fqn = self.imports.get(func.id, f"{fqn.split('.')[0]}.{func.id}")
                    relationships.append((fqn, target_fqn, "uses"))
                elif isinstance(func, ast.Attribute) and not (
                        isinstance(func.value, ast.Call) and isinstance(func.value.func,
                                                                        ast.Name) and func.value.func.id == "super"):
                    target_fqn = f"{func.value.id}.{func.attr}" if isinstance(func.value, ast.Name) else func.attr
                    relationships.append((fqn, target_fqn, "uses"))

        # Return a ParsedEntity for the constructor and deferred parsing for attributes
        return ParsedEntity(
            fqn=fqn,
            name="__init__",
            entity_type=NodeType.CONSTRUCTOR,
            relationships=relationships
        ), deferred_parsing
