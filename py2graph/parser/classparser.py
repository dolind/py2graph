import ast

from py2graph.parser.parser_interface import IParser, DeferredParsingExpression, ParsedEntity, NodeType


class ClassParser(IParser):
    def __init__(self, imports):
        super().__init__(imports)

    def parse(self, ast_node, fqn):

        # Handle inheritance
        base_classes = []
        for base in ast_node.bases:
            base_class = self.infer_fqn_from_base(base, fqn.split('.')[-1])
            base_classes.append(base_class)


            # TODO: ugly, instead allow ABC in imports to correctly resolve it

        root_package_prefix = fqn.split('.')[0]
        root_package_classes = [
            base_class for base_class in base_classes if base_class.startswith(root_package_prefix)
        ]
        if 'abc.ABC' in base_classes:
            root_package_classes.append('abc.ABC')
        # Create relationships only for classes belonging to the root package
        relationships = [(fqn, base_class, "inherits") for base_class in root_package_classes]


        # relationships = [(fqn, base_class, "inherits") for base_class in base_classes]

        #     {
        #     local_name: imported_fqn
        #     for local_name, imported_fqn in module_imports.items()
        #     if imported_fqn.startswith(root_package_prefix)
        # })
        # Handle class definitions
        deferred_parsing = []
        for node in ast_node.body:
            if isinstance(node, ast.FunctionDef):
                context = "method"
                name = node.name
            elif isinstance(node, (ast.AnnAssign)):
                context = "attribute"
                name = node.target.id
            elif isinstance(node, (ast.Assign)):
                context = "attribute"
                name = node.targets[0].id
            else:
                continue

            relationships.append((fqn, f"{fqn}.{name}", "defines"))
            deferred_parsing.append(
                DeferredParsingExpression(fqn=f"{fqn}.{name}", node=node, context=context, imported_fqn=self.imports))

        return ParsedEntity(
            fqn=fqn,
            name=fqn.split('.')[-1],
            entity_type=NodeType.CLASS,
            relationships=relationships
        ), deferred_parsing
