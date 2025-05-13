import ast
import re


def infer_type_from_annotation(annotation: ast.AST):
    """
    Infer the type from an annotation (e.g., int, List[str]).
    """
    if isinstance(annotation, ast.Name):
        # Simple type (e.g., int, str)
        return annotation.id
    elif isinstance(annotation, ast.Attribute):
        # Attribute type (e.g., typing.List)
        value_id = infer_value_id(annotation.value)
        if value_id:
            return f"{value_id}.{annotation.attr}"
    elif isinstance(annotation, ast.Subscript):
        # Subscripted types (e.g., List[int], Dict[str, int])
        value_id = infer_type_from_annotation(annotation.value)
        if isinstance(annotation.slice, ast.Tuple):  # Handle multiple subscript elements
            slice_parts = [infer_type_from_annotation(el) for el in annotation.slice.elts]
            slice_id = ", ".join(part for part in slice_parts if part is not None)

        else:  # Single subscript element
            slice_id = infer_type_from_annotation(annotation.slice)
        if value_id and slice_id:
            return f"{value_id}[{slice_id}]"
    elif isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
        # Handle the union operator (|) for Python 3.10+
        left_type = infer_type_from_annotation(annotation.left)
        right_type = infer_type_from_annotation(annotation.right)
        return f"Union[{left_type}, {right_type}]"
    elif isinstance(annotation, ast.Tuple):
        # Handle Tuple type annotations
        elements = [infer_type_from_annotation(el) for el in annotation.elts]
        return ", ".join(elements)
    elif isinstance(annotation, ast.Constant):
        # For string-based annotations (e.g., "int" in older forward refs)
        return annotation.value
    return None


def infer_type_from_value(value_node: ast.AST):
    """
    Infer the type of a value (e.g., 42 -> int).
    """
    if isinstance(value_node, ast.Constant):
        return type(value_node.value).__name__
    elif isinstance(value_node, ast.List):
        return "list"
    elif isinstance(value_node, ast.Dict):
        return "dict"
    elif isinstance(value_node, ast.Call):  # Constructor calls
        if isinstance(value_node.func, ast.Name):
            return value_node.func.id
        elif isinstance(value_node.func, ast.Attribute):
            return f"{value_node.func.value.id}.{value_node.func.attr}"
    return None


def resolve_type(type_name, imports):
    # Check if the type is in imports to resolve to FQN
    return imports.get(type_name, type_name)



def resolve_nested_attribute(attribute_node):
    """
    Resolve the fully qualified name of a nested attribute.

    Args:
        attribute_node (ast.Attribute): The attribute node to resolve.

    Returns:
        str: The fully qualified name of the attribute.
    """
    parts = []
    current = attribute_node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value

    if isinstance(current, ast.Name):  # Base case: resolve the root name
        parts.append(current.id)

    # Reverse parts to form the fully qualified name
    return ".".join(reversed(parts))


def identify_root_package(node):
    return resolve_nested_attribute(node.func).split(".")[0]


# Core utility functions
def infer_type(annotation_or_value, imports=None):
    if isinstance(annotation_or_value, ast.AST):
        if isinstance(annotation_or_value, ast.Name):
            return annotation_or_value.id
        elif isinstance(annotation_or_value, ast.Attribute):
            return resolve_nested_attribute(annotation_or_value)
        elif isinstance(annotation_or_value, ast.Subscript):
            value_id = infer_type(annotation_or_value.value)
            slice_id = infer_type(annotation_or_value.slice) if not isinstance(annotation_or_value.slice, ast.Index) else None
            return f"{value_id}[{slice_id}]" if value_id and slice_id else value_id
        elif isinstance(annotation_or_value, ast.BinOp) and isinstance(annotation_or_value.op, ast.BitOr):
            left = infer_type(annotation_or_value.left)
            right = infer_type(annotation_or_value.right)
            return f"Union[{left}, {right}]"
        elif isinstance(annotation_or_value, ast.Constant):
            return type(annotation_or_value.value).__name__ if hasattr(annotation_or_value, 'value') else annotation_or_value.value
        elif isinstance(annotation_or_value, ast.List):
            return "list"
        elif isinstance(annotation_or_value, ast.Dict):
            return "dict"
        elif isinstance(annotation_or_value, ast.Call):
            return resolve_nested_attribute(annotation_or_value.func)
    return None



def resolve_fqn(node, module_fqn, imports):
    if isinstance(node, ast.Name):
        return imports.get(node.id, f"{module_fqn}.{node.id}")
    elif isinstance(node, ast.Attribute):
        base_fqn = resolve_fqn(node.value, module_fqn, imports)
        return f"{base_fqn}.{node.attr}" if base_fqn else node.attr
    return None

def parse_union_type(type_name, imports):
    if not type_name:
        return ['None']
    cleaned_type = type_name.replace("Union[", "").strip("]") if "Union" in type_name else type_name
    return [resolve_type(part.strip(), imports) for part in re.split(r"[|,]", cleaned_type)]


def infer_value_id(value):
    return resolve_nested_attribute(value)

def infer_fqn_from_base(base, module_fqn, imports={}):
    return resolve_fqn(base, module_fqn, imports)
#
def split_and_resolve_type_name(type_name, imports):
    return parse_union_type(type_name, imports)

