import ast


from py2graph.parser.helper import split_and_resolve_type_name
from py2graph.parser.parser_interface import IParser, DeferredParsingExpression, ParsedEntity, NodeType


class MethodParser(IParser):
    def __init__(self, imports):
        super().__init__(imports)

    def parse(self, ast_node, fqn):
        arguments = []
        return_types = None

        # Parse arguments
        for arg in ast_node.args.args:
            if arg.annotation:
                type_name = self.infer_type_from_annotation(arg.annotation)
                resolved_types = split_and_resolve_type_name(type_name, self.imports)
                arguments.extend(resolved_types)  # Combine resolved types back

        # Parse return type
        if ast_node.returns:
            type_name = self.infer_type_from_annotation(ast_node.returns)
            resolved_types = split_and_resolve_type_name(type_name, self.imports)
            return_types = resolved_types

        # Defer body parsing
        context = "constructor" if isinstance(ast_node, ast.FunctionDef) and ast_node.name == "__init__" else "body"
        deferred_body = DeferredParsingExpression(fqn=fqn, node=ast_node, context=context, imported_fqn=self.imports)

        relationships = []
        for argument in arguments:
            relationships.append((fqn, argument, "has_argument"))
        if return_types:
            for return_type in return_types:
                relationships.append((fqn, return_type, "returns"))

        return ParsedEntity(
            fqn=fqn,
            name=fqn.split('.')[-1],
            entity_type=NodeType.METHOD,
            relationships=relationships
        ), [deferred_body]


