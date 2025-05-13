import pytest

from py2graph.parser.package import PackageParser
from py2graph.parser.parser_interface import NodeType


@pytest.fixture
def mock_package_structure(tmp_path):
    """
    Create a mock package structure for testing.
    """

    root = tmp_path / "package"
    root.mkdir()
    (root / "__init__.py").touch()
    (root / "module1.py").touch()
    (root / "module2.py").touch()
    subpackage = root / "subpackage"
    subpackage.mkdir()
    (subpackage / "__init__.py").touch()
    (subpackage / "submodule.py").touch()
    return tmp_path


def test_package_parser_with_relationships(mock_package_structure):
    package_path = mock_package_structure / "package"
    package_fqn = "mock.package"
    parser = PackageParser(package_path)
    parsed_entities, deferred_parsing = parser.parse("", package_fqn)

    # Verify package entity
    package_entity = next(
        entity for entity in parsed_entities if entity.fqn == "mock.package"
    )
    assert package_entity.entity_type == NodeType.PACKAGE

    # Verify contains relationships for modules
    assert ("mock.package", "mock.package.module1", "contains") in package_entity.relationships
    assert ("mock.package", "mock.package.module2", "contains") in package_entity.relationships

    # Verify contains relationships for subpackages
    assert ("mock.package", "mock.package.subpackage", "contains") in package_entity.relationships

    # Verify deferred parsing for modules
    assert any(
        expr.fqn == "mock.package.module1" and expr.context == "module"
        for expr in deferred_parsing
    )
    assert any(
        expr.fqn == "mock.package.module2" and expr.context == "module"
        for expr in deferred_parsing
    )
