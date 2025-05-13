import networkx as nx
import pytest

from py2graph.graphcreator.graphcreator import GraphCreator
from py2graph.graphviewer.puml import PumlGenerator
from py2graph.parser.attribute import AttributeParser
from py2graph.parser.classparser import ClassParser
from py2graph.parser.constructor import ConstructorParser
from py2graph.parser.method import MethodParser
from py2graph.parser.methodbody import MethodBodyParser
from py2graph.parser.moduleparser import ModuleParser
from py2graph.parser.package import PackageParser
from py2graph.parser.parser_interface import NodeType





@pytest.fixture
def mock_package_structure(tmp_path):
    """
    Creates a mock package structure for testing.
    """
    base_dir = tmp_path / "productworld"
    base_dir.mkdir()

    # Create subpackages
    base_package = base_dir / "base"
    base_package.mkdir()
    product_package = base_dir / "product"
    product_package.mkdir()

    # Add __init__.py to subpackages
    (base_package / "__init__.py").write_text("")
    (product_package / "__init__.py").write_text("")

    # Add base.py
    (base_package / "base.py").write_text("""
from abc import ABC, abstractmethod

class Product(ABC):
    def __init__(self, product_id:int, name):
        self.product_id :int = product_id
        self.name = name

    @abstractmethod
    def get_price(self):
        pass


class NewOrder:
    def __init__(self, order_id, product: Product, quantity):
        self.order_id = order_id
        self.product:Product = product
        self.quantity = quantity

    def calculate_total(self)->int:
        return self.product.price * self.quantity

class Order:
    def __init__(self, order_id, product: Product, quantity):
        self.order_id = order_id
        self.product = product
        self.quantity = quantity

    def calculate_total(self)->int:
        return self.product.price * self.quantity

def fancyFunc(order: Order)->int:
    return 42

def funkyFunc()->int:
    return 42
""")

    # Add customer.py
    (base_package / "customer.py").write_text("""
from typing import List

from productworld.base.base import Order,fancyFunc, NewOrder

class Customer:
    def __init__(self, customer_id, name):
        self.customer_id = customer_id
        self.name = name
        self.orders = []

    def add_order(self, order: Order):
        self.orders.append(order)
        self.orders.append(NewOrder())
        fancyFunc(order)

    def get_total_spent(self)-> int:
        return sum(order.calculate_total() for order in self.orders)
""")

    # Add product.py
    (product_package / "product.py").write_text("""
from productworld.base.base import Product
from productworld.base.base import funkyFunc

class PhysicalProduct(Product):
    def __init__(self, product_id, name, price):
        super().__init__(product_id, name)
        self.price : int = price

    def get_price(self) -> int:
        return self.price

class DigitalProduct(Product):
    def __init__(self, product_id, name, price, discount):
        super().__init__(product_id, name)
        self.price = price
        self.discount = discount
        funkyFunc()

    def get_price(self)->int:
        return self.price * (1 - self.discount)

class Productfactory():
    def create_product(self,pid:str)->PhysicalProduct|DigitalProduct:
        return PhysicalProduct()

def create_product2(self,pid:str)->PhysicalProduct|DigitalProduct:
        return PhysicalProduct()
""")

    return base_dir


@pytest.fixture
def orchestrator():
    """
    Provides an Orchestrator instance with initialized parsers.
    """
    graph = nx.DiGraph()  # Directed graph for all entities
    parser = {
        "package": PackageParser,
        "module": ModuleParser,
        "class": ClassParser,
        "method": MethodParser,
        "attribute": AttributeParser,
        "body": MethodBodyParser,
        "constructor": ConstructorParser
    }
    return GraphCreator(graph, parser)


def test_orchestrator_parse_package(orchestrator, mock_package_structure):
    """
    Test the orchestrator's ability to parse a package and build a graph.
    """
    package_fqn = "productworld"
    orchestrator.parse_package(mock_package_structure, package_fqn)

    graph = orchestrator.graph
    # visualize_graph(graph, output_file="graph_visualization.png")
    #
    # Verify package nodes
    base_package = graph.nodes["productworld.base"]["data"]
    product_package = graph.nodes["productworld.product"]["data"]
    assert base_package.node_type == NodeType.PACKAGE
    assert product_package.node_type == NodeType.PACKAGE

    # Verify module nodes
    base_module = graph.nodes["productworld.base.base"]["data"]
    customer_module = graph.nodes["productworld.base.customer"]["data"]
    product_module = graph.nodes["productworld.product.product"]["data"]
    assert base_module.node_type == NodeType.MODULE
    assert customer_module.node_type == NodeType.MODULE
    assert product_module.node_type == NodeType.MODULE
    #
    # Verify class nodes
    product_class = graph.nodes["productworld.base.base.Product"]["data"]
    new_order_class = graph.nodes["productworld.base.base.NewOrder"]["data"]
    physical_product_class = graph.nodes["productworld.product.product.PhysicalProduct"]["data"]
    assert product_class.node_type == NodeType.CLASS
    assert new_order_class.node_type == NodeType.CLASS
    assert physical_product_class.node_type == NodeType.CLASS
    #
    # # Verify function nodes
    fancy_func = graph.nodes["productworld.base.base.fancyFunc"]["data"]
    funky_func = graph.nodes["productworld.base.base.funkyFunc"]["data"]
    assert fancy_func.node_type == NodeType.METHOD
    assert funky_func.node_type == NodeType.METHOD

    # Verify relationships
    edges = list(graph.edges(data=True))

    # Check that the base package contains its modules
    assert ("productworld.base", "productworld.base.base") in [(src, tgt) for src, tgt, _ in edges]
    assert ("productworld.base", "productworld.base.customer") in [(src, tgt) for src, tgt, _ in edges]

    # Check inheritance relationships
    assert ("productworld.product.product.PhysicalProduct", "productworld.base.base.Product") in [
        (src, tgt) for src, tgt, data in edges if data["relation"] == ["inherits"]
    ]

    # Check method definitions
    assert ("productworld.base.base.NewOrder", "productworld.base.base.NewOrder.calculate_total") in [
        (src, tgt) for src, tgt, data in edges if data["relation"] == ["defines"]
    ]
    #
    # # Check uses relationships
    assert ("productworld.base.customer.Customer.add_order", "productworld.base.base.fancyFunc") in [
        (src, tgt) for src, tgt, data in edges if data["relation"] == ["uses"]
    ]
    assert ("productworld.product.product.DigitalProduct.__init__", "productworld.base.base.funkyFunc") in [
        (src, tgt) for src, tgt, data in edges if data["relation"] == ["uses"]
    ]


def test_orchestrator_generate_uml(orchestrator, mock_package_structure):
    # Generate PUML and validate output
    package_fqn = "productworld"
    orchestrator.parse_package(mock_package_structure, package_fqn)

    graph = orchestrator.graph
    generator = PumlGenerator(graph)
    puml_content = generator.generate()
    print(puml_content)
    # Expected PUML content lines
    expected_lines = [
        "@startuml ",
        "!pragma useIntermediatePackages false",
        "skinparam linetype ortho",
        "annotation productworld.product.product.Methods {",
        "  create_product2(str) -> PhysicalProduct | DigitalProduct",
        "}",
        "class productworld.product.product.Productfactory {",
        "  create_product(str) -> PhysicalProduct | DigitalProduct",
        "}",
        "class productworld.product.product.DigitalProduct {",
        "  price: None",
        "  discount: None",
        "  DigitalProduct() -> None",
        "  get_price() -> int",
        "}",
        "class productworld.product.product.PhysicalProduct {",
        "  price: int",
        "  PhysicalProduct() -> None",
        "  get_price() -> int",
        "}",
        "class productworld.base.customer.Customer {",
        "  customer_id: None",
        "  name: None",
        "  orders: list",
        "  Customer() -> None",
        "  add_order(Order) -> None",
        "  get_total_spent() -> int",
        "}",
        "annotation productworld.base.base.Methods {",
        "  fancyFunc(Order) -> int",
        "  funkyFunc() -> int",
        "}",
        "class productworld.base.base.Order {",
        "  order_id: None",
        "  product: Product",
        "  quantity: None",
        "  Order(Product) -> None",
        "  calculate_total() -> int",
        "}",
        "class productworld.base.base.NewOrder {",
        "  order_id: None",
        "  product: Product",
        "  quantity: None",
        "  NewOrder(Product) -> None",
        "  calculate_total() -> int",
        "}",
        "abstract class productworld.base.base.Product {",
        "  product_id: int",
        "  name: None",
        "  Product(int) -> None",
        "  get_price() -> None",
        "}",
        "productworld.product.product.PhysicalProduct --|> productworld.base.base.Product",
        "productworld.product.product.DigitalProduct --|> productworld.base.base.Product",
        "productworld.product.product.Methods --> productworld.product.product.PhysicalProduct: used by create_product2",
        "productworld.product.product.Methods --> productworld.product.product.DigitalProduct: used by create_product2",
        "productworld.base.base.Methods --> productworld.base.base.Order: used by fancyFunc",
        "productworld.base.base.NewOrder *-- productworld.base.base.Product",
        "productworld.product.product.DigitalProduct --> productworld.base.base.Methods: used by __init__ use of funkyFunc",
        "productworld.product.product.Productfactory --> productworld.product.product.PhysicalProduct: used by create_product",
        "productworld.product.product.Productfactory --> productworld.product.product.DigitalProduct: used by create_product",
        "productworld.base.customer.Customer --> productworld.base.base.Order: used by add_order",
        "productworld.base.customer.Customer --> productworld.base.base.Methods: used by add_order use of fancyFunc",
        "productworld.base.customer.Customer --> productworld.base.base.NewOrder: used by add_order",
        "productworld.base.base.Order --> productworld.base.base.Product: used by __init__",
        "footer Generated by //CodebaseGraph//",
        "@enduml",
    ]

    # Split generated PUML content into lines
    generated_lines = puml_content.strip().split("\n")

    # # Assert line count matches
    assert len(generated_lines) == len(expected_lines) +1 , (
        f"Line count mismatch.\nGenerated lines: {len(generated_lines)}\nExpected lines: {len(expected_lines)}"
    )

    # Assert each line exists in generated output
    for expected_line in expected_lines:
        assert expected_line in generated_lines, f"Expected line not found: {expected_line}"


@pytest.fixture
def mock_package_enum(tmp_path):
    """
    Creates a mock package structure for testing.
    """
    base_dir = tmp_path / "domain"
    base_dir.mkdir()

    # Add __init__.py to subpackages
    (base_dir / "__init__.py").write_text("")

    # Add base.py

    (base_dir / "umlrelation.py").write_text("""
from enum import Enum, unique


@unique
class RelType(Enum):
    COMPOSITION = '*'
    INHERITANCE = '<|'
    DEPENDENCY = '<'
  """)
    return base_dir


def test_orchestrator_parse_enum(orchestrator, mock_package_enum):
    package_fqn = "domain"
    orchestrator.parse_package(mock_package_enum, package_fqn)

    graph = orchestrator.graph
    generator = PumlGenerator(graph)
    puml_content = generator.generate()
    print(puml_content)

    assert "class domain.umlrelation.RelType {" in puml_content
    assert "COMPOSITION: str" in puml_content
    assert "INHERITANCE: str" in puml_content
    assert "DEPENDENCY: str" in puml_content
