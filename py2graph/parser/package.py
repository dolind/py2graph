import ast
import os
from pathlib import Path

from py2graph.parser.parser_interface import IParser, DeferredParsingExpression, ParsedEntity, NodeType


class PackageParser(IParser):
    def __init__(self, package_path):
        super().__init__({})
        self.package_path = package_path

    def parse(self, ast_node, package_fqn: str):
        """
        Parse the package structure to discover subpackages and modules.
        Creates deferred parsing expressions for modules and subpackages.
        Adds "contains" relationships for discovered subpackages and modules.
        """
        parsed_entities = []
        deferred_parsing = []
        for root, dirs, files in os.walk(self.package_path):
            # Determine the FQN of the current directory
            current_fqn = (
                package_fqn + '.' + Path(root).name
                if root != str(self.package_path)
                else package_fqn
            )
            relationships = []
            if current_fqn.endswith('__pycache__'):
                continue
            # Add deferred parsing expressions for each module in the directory
            for file in files:
                if file.endswith('.py') and file != '__init__.py':

                    module_fqn = f"{current_fqn}.{file[:-3]}"
                    relationships.append((current_fqn, module_fqn, "contains"))
                    with open(Path(root) / file, 'r') as f:
                        module_ast = ast.parse(f.read(), filename=file)
                    deferred_parsing.append(
                        DeferredParsingExpression(
                            fqn=module_fqn,
                            node=module_ast,
                            context="module",
                            imported_fqn={}
                        )
                    )

            # Add deferred parsing expressions for subdirectories
            for subdir in dirs:
                if subdir.endswith('__pycache__'):
                    continue
                relationships.append((current_fqn, f"{current_fqn}.{subdir}", "contains"))

            # Add a package node for directories with __init__.py
            if '__init__.py' in files:
                package_entity = ParsedEntity(
                    fqn=current_fqn,
                    name=Path(root).name,
                    entity_type=NodeType.PACKAGE,
                    relationships=relationships
                )
                parsed_entities.append(package_entity)

        return parsed_entities, deferred_parsing
