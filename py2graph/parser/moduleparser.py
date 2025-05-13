import ast

from py2graph.parser.parser_interface import IParser, DeferredParsingExpression, ParsedEntity, NodeType


class ModuleParser(IParser):
    def __init__(self, imported_fqn={}):
        super().__init__({})

    def parse(self, ast_node, fqn):

        root_package_prefix = fqn.split('.')[0]
        for node in ast_node.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module_imports = self._parse_import(node)
                self.imports.update(module_imports)

                #     {
                #     local_name: imported_fqn
                #     for local_name, imported_fqn in module_imports.items()
                #     if imported_fqn.startswith(root_package_prefix)
                # })

        relationships = [(fqn, imported_fqn, "imports") for imported_fqn in self.imports.values()]

        deferred_parsing = []
        for node in ast_node.body:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                context = "class" if isinstance(node, ast.ClassDef) else "method" if isinstance(node,
                                                                                                ast.FunctionDef) else ""
                deferred_fqn = f"{fqn}.{node.name}"
                relationships.append((fqn, deferred_fqn, "contains"))
                deferred_parsing.append(DeferredParsingExpression(fqn=deferred_fqn, node=node, context=context,
                                                                  imported_fqn=self.imports))


        return  ParsedEntity(fqn=fqn, name=fqn.split('.')[-1], entity_type=NodeType.MODULE,
                                       relationships=relationships), deferred_parsing

    def _parse_import(self, node):
        base_fqn = getattr(node, 'module', "") if isinstance(node, ast.ImportFrom) else ""
        return {
            (alias.asname or alias.name): (f"{base_fqn}.{alias.name}" if base_fqn else alias.name)
            for alias in node.names
        }
