import time
from typing import Iterable

import networkx as nx

from py2graph.graphcreator.graphcreator import GraphCreator
from py2graph.graphviewer.puml import PumlGenerator
from py2graph.parser.attribute import AttributeParser
from py2graph.parser.classparser import ClassParser
from py2graph.parser.constructor import ConstructorParser
from py2graph.parser.method import MethodParser
from py2graph.parser.methodbody import MethodBodyParser
from py2graph.parser.moduleparser import ModuleParser
from py2graph.parser.package import PackageParser


def py2graph(domain_path: str, domain_module: str) -> Iterable[str]:
    start_time = time.time()
    graph = nx.DiGraph()  # Directed graph for all entities

    parser = {"package": PackageParser,
              "module": ModuleParser,
              "class": ClassParser,
              "method": MethodParser,
              "attribute": AttributeParser,
              "body": MethodBodyParser,
              "constructor": ConstructorParser}
    orchestrator = GraphCreator(graph, parser)

    orchestrator.parse_package(domain_path, domain_module)

    generator = PumlGenerator(graph, "")
    result = generator.generate()
    end_time = time.time()

    print(f"Execution time: {end_time - start_time} seconds")

    return result
