import ast
import re

from py2graph.parser.helper import resolve_type
from py2graph.parser.parser_interface import IParser, ParsedEntity, NodeType


class AttributeParser(IParser):
    def __init__(self, imports):

        super().__init__(imports)

    def parse(self, ast_node, fqn):
        """
        Parse an attribute to detect its type and defer further processing if needed.
        """
        attr_name, attr_type, attr_fqn = None, None, None
        relationship_type = None  # New variable to store relationship type

        if isinstance(ast_node, ast.AnnAssign):
            # Annotated assignment
            target = ast_node.target
            if not isinstance(target, ast.Name) and target.value.id == "self":
                attr_name = ast_node.target.attr
                attr_fqn = fqn
            else:
                attr_name = target.id
                attr_fqn = fqn  # f"{fqn}.{attr_name}"
            attr_type = self.infer_type_from_annotation(ast_node.annotation)

            # Determine aggregation vs composition
            if isinstance(ast_node.value, ast.Call):  # Direct instantiation
                relationship_type = "composition"
            else:  # Passed externally
                relationship_type = "aggregation"

        elif isinstance(ast_node, ast.Assign):  # Regular assignment
            target = ast_node.targets[0]
            if not isinstance(target, ast.Name) and target.value.id == "self":
                attr_name = target.attr
                attr_fqn = fqn
            else:
                attr_name = target.id
                attr_fqn = fqn  # f"{fqn}.{attr_name}"
            attr_type = self.infer_type_from_value(ast_node.value)

            # Determine aggregation vs composition
            if isinstance(ast_node.value, ast.Call):  # Direct instantiation
                relationship_type = "composition"
            else:  # Passed externally
                relationship_type = "aggregation"
        # Resolve the base type
        attr_type = resolve_type(attr_type, self.imports)
        base_relationships = [(attr_fqn, attr_type, "has_type")]
        base_relationships.append((attr_fqn, attr_type, relationship_type))

        # Add relationships for subtypes in compound types
        compound_relationships = resolve_compound_relationships(attr_type, attr_fqn, self.imports)

        # Combine all relationships
        all_relationships = base_relationships + compound_relationships

        if attr_name:
            return ParsedEntity(
                fqn=attr_fqn,
                name=attr_name,
                entity_type=NodeType.ATTRIBUTE,
                relationships=all_relationships
            ), []

        return None, []


def parse_subtypes(compound_type):
    """
    Extract subtypes from compound types like List[Subtype] or Dict[KeyType, ValueType].
    """
    match = re.findall(r'\b\w+\b', compound_type)
    if len(match) > 1:
        # Exclude the main type (e.g., List, Dict) from the result
        return match[1:]
    return []


def resolve_compound_relationships(attr_type, attr_fqn, imports):
    """
    Resolve compound types and return relationships for subtypes.
    """
    if not attr_type or '[' not in attr_type:
        return []
    subtypes = parse_subtypes(attr_type)
    relationships = []

    for subtype in subtypes:
        resolved_subtype = resolve_type(subtype, imports)
        if resolved_subtype:
            relationships.append((attr_fqn, resolved_subtype, "has_compound_type"))

    return relationships
