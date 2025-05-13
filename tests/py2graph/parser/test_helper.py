import ast

import pytest

from py2graph.parser.helper import (
    infer_type_from_annotation,
    infer_value_id,
    infer_fqn_from_base,
    infer_type_from_value,
)


### Test infer_type_from_annotation ###

@pytest.mark.parametrize("annotation_code, expected_type", [
    ("int", "int"),  # Simple type
    ("str", "str"),  # Simple type
    ("List[int]", "List[int]"),  # Subscripted type
    ("Dict[str, int]", "Dict[str, int]"),  # Subscripted type with multiple arguments
    ("Optional[str]", "Optional[str]"),  # Subscripted type with a single argument
    ("typing.List", "typing.List"),  # Attribute type
    ("CustomType", "CustomType"),  # Custom type
    ("Tuple[str, int]", "Tuple[str, int]"),  # Tuple type
    ("Union[str, int]", "Union[str, int]"),  # Union type
    ("str | int", "Union[str, int]"),  # Union type
    ("ForwardRef", "ForwardRef"),  # Forward reference
])
def test_infer_type_from_annotation(annotation_code, expected_type):
    annotation = ast.parse(annotation_code, mode="eval").body
    inferred_type = infer_type_from_annotation(annotation)
    assert inferred_type == expected_type


@pytest.mark.parametrize("annotation_code", [
    "InvalidType[",  # Incomplete type
    "SomeUnknownType<str>",  # Invalid syntax
])
def test_infer_type_from_annotation_invalid(annotation_code):
    try:
        annotation = ast.parse(annotation_code, mode="eval").body
    except SyntaxError:
        annotation = None  # Simulate an invalid AST node

    inferred_type = infer_type_from_annotation(annotation)
    assert inferred_type is None


### Test infer_value_id ###

@pytest.mark.parametrize("value_code, expected_value", [
    ("variable", "variable"),
    ("module.variable", "module.variable"),
    ("package.module.variable", "package.module.variable"),
])
def test_infer_value_id(value_code, expected_value):
    value = ast.parse(value_code, mode="eval").body
    inferred_value = infer_value_id(value)
    assert inferred_value == expected_value


def test_infer_value_id_invalid():
    value = ast.parse("invalid[42]", mode="eval").body
    inferred_value = infer_value_id(value)
    assert inferred_value is ''


### Test infer_fqn_from_base ###

@pytest.mark.parametrize("base_code, module_fqn, expected_fqn", [
    ("BaseClass", "my_module", "my_module.BaseClass"),
    ("BaseModule.BaseClass", "my_module", "my_module.BaseModule.BaseClass"),
    ("package.my_module.BaseClass", "my_module", "my_module.package.my_module.BaseClass"),
])
def test_infer_fqn_from_base(base_code, module_fqn, expected_fqn):
    base = ast.parse(base_code, mode="eval").body
    inferred_fqn = infer_fqn_from_base(base, module_fqn)
    assert inferred_fqn == expected_fqn


def test_infer_fqn_from_base_invalid():
    base = ast.parse("[BaseClass]", mode="eval").body
    inferred_fqn = infer_fqn_from_base(base, "my_module")
    assert inferred_fqn is None


### Test infer_type_from_value ###

@pytest.mark.parametrize("value_code, expected_type", [
    ("42", "int"),
    ("'hello'", "str"),
    ("[1, 2, 3]", "list"),
    ("{'key': 'value'}", "dict"),
    ("CustomType()", "CustomType"),
    ("module.CustomType()", "module.CustomType"),
])
def test_infer_type_from_value(value_code, expected_type):
    value_node = ast.parse(value_code, mode="eval").body
    inferred_type = infer_type_from_value(value_node)
    assert inferred_type == expected_type


def test_infer_type_from_annotation_none():
    assert infer_type_from_annotation(None) is None


def test_infer_value_id_none():
    assert infer_value_id(None) is ''


def test_infer_fqn_from_base_none():
    assert infer_fqn_from_base(None, "module") is None


def test_infer_type_from_value_none():
    assert infer_type_from_value(None) is None
