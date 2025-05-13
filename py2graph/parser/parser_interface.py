import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict

from py2graph.parser.helper import infer_type_from_value, infer_type_from_annotation, infer_fqn_from_base


class IParser(ABC):
    def __init__(self, imports):
        self.imports = imports

    def infer_fqn_from_base(self, base, module_fqn):
        return infer_fqn_from_base(base, module_fqn, self.imports)

    def infer_type_from_annotation(self, annotation):
        return infer_type_from_annotation(annotation)

    def infer_type_from_value(self, value):
        return infer_type_from_value(value)

    @abstractmethod
    def parse(self, ast_node, fqn):
        pass


class NodeType(Enum):
    PACKAGE = "package"
    MODULE = "module"
    CLASS = "class"
    METHOD = "method"
    CONSTRUCTOR = "constructor",
    BODY = "body",
    ATTRIBUTE = "attribute"
    PLACEHOLDER = "placeholder"
    TYPE = "type"


@dataclass
class ParsedEntity:
    fqn: str
    name: str
    entity_type: NodeType
    attributes: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    base_classes: List[str] = field(default_factory=list)
    relationships: List[tuple] = field(default_factory=list)  # e.g., (source, target, relation)


@dataclass
class DeferredParsingExpression:
    fqn: str
    node: ast.AST
    context: str  # e.g., 'module', 'class'
    imported_fqn: Dict[str, str]
