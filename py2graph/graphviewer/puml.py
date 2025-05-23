import networkx as nx

from py2graph.parser.parser_interface import NodeType

PUML_FILE_START = """@startuml {diagram_name}
!pragma useIntermediatePackages false
skinparam linetype ortho
"""

PUML_FILE_FOOTER = """footer Generated by //CodebaseGraph//"""

PUML_FILE_END = """@enduml"""

PUML_ITEM_START_TPL = """{item_type} {item_name} {{"""

PUML_ATTR_TPL = """  {attr_name}: {attr_type}{staticity}"""

PUML_METHOD_TPL = """  {method_signature}"""

PUML_ITEM_END = """}"""

PUML_RELATION_TPL = """{source} {relation} {target}"""

FEATURE_STATIC = ' {static}'
FEATURE_INSTANCE = ''


class PumlGenerator:
    def __init__(self, graph: nx.DiGraph, diagram_name: str = ""):
        self.graph = graph
        self.diagram_name = diagram_name
        self.puml_lines = []
        self.visited = set()

    def generate(self) -> str:
        """
        Generate a PlantUML file content from the graph using stack-based DFS.
        """
        self.puml_lines = [self._puml_file_start()]

        # Start DFS from top-level nodes (e.g., packages or modules)
        for node_fqn, node_data in self.graph.nodes(data=True):
            if len(node_data) > 0:
                node = node_data['data']
                if node.node_type in {NodeType.MODULE} and node_fqn not in self.visited:
                    self._dfs_stack(node_fqn)

        existing_connections = {}
        # Generate relationships
        for source, target, edge_data in self.graph.edges(data=True):

            if (self.graph.nodes[source]['data'].node_type in {NodeType.CLASS, NodeType.METHOD}) and \
                    target in self.graph.nodes and 'data' in self.graph.nodes[target] and \
                    (self.graph.nodes[target]['data'].node_type in {NodeType.CLASS, NodeType.METHOD}):
                targetisMethod = self.graph.nodes[target]['data'].node_type in {NodeType.METHOD}
                sourceisMethod = self.graph.nodes[source]['data'].node_type in {NodeType.METHOD}
                outputSource = source
                outputTarget = target
                extra = ''
                if 'abc.ABC' in target:
                    continue
                # avoid classes defining their methods
                # this issue steams from the fact that i use methods and functions both with NodeTYpe.METHOD
                # alternatively introduce Function for free functions

                targetParent = ".".join(target.split(".")[:-1])
                sourceParent = ".".join(source.split(".")[:-1])

                if sourceisMethod:
                    outputSource = ".".join(source.split(".")[:-1])
                    if self.graph.nodes[sourceParent]['data'].node_type is NodeType.MODULE:
                        outputSource += ".Methods"
                    extra = ": " + "".join(["used by ", source.split(".")[-1]])

                if targetisMethod:
                    outputTarget = ".".join(target.split(".")[:-1])
                    if self.graph.nodes[targetParent]['data'].node_type is NodeType.MODULE:
                        outputTarget += ".Methods"
                    if extra == "":
                        extra = ":"
                    extra += "".join([" use of ", target.split(".")[-1]])
                if outputTarget == outputSource:
                    continue
                target_root_package_prefix = target.split('.')[0]
                source_root_package_prefix = source.split('.')[0]
                if target_root_package_prefix != source_root_package_prefix:
                    continue

                # ugly fix to prevent multiple connections in diagram
                sourceParentisClass = self.graph.nodes[sourceParent]['data'].node_type in {NodeType.CLASS}
                parentRelations = []
                if sourceisMethod and sourceParentisClass:

                    attribute_edges = ['composition', 'aggregation', 'has_attribute_with_type']
                    if self.graph.has_edge(sourceParent, target):
                        parentRelations = self.graph[sourceParent][target].values()
                        parentRelations = parentRelations
                        parentRelations = [word for word in parentRelations if word not in attribute_edges]
                if len(parentRelations) > 0:
                    continue

                for relation in edge_data['relation']:
                    # skip if we already identified a relation between the two for the parent, often the class

                    relation_output = _map_relation_type(relation)

                    if relation_output is not None:
                        # Check for duplicate connections with the same relation_output
                        connection_key = (outputSource, outputTarget)
                        if connection_key not in existing_connections:
                            existing_connections[connection_key] = set()

                        if relation_output not in existing_connections[connection_key]:
                            existing_connections[connection_key].add(relation_output)
                            self.puml_lines.append(f"{outputSource} {relation_output} {outputTarget}{extra}")

        self.puml_lines.append(self._puml_file_footer())
        self.puml_lines.append(self._puml_file_end())
        return '\n'.join(self.puml_lines)

    def _dfs_stack(self, start_node_fqn):
        """
        Perform DFS using a stack to process nodes and relationships.
        """
        stack = [start_node_fqn]

        while stack:
            current_fqn = stack.pop()
            if current_fqn in self.visited:
                continue

            self.visited.add(current_fqn)
            current_node = self.graph.nodes[current_fqn]['data']

            if current_node.node_type == NodeType.CLASS:
                self._process_class(current_fqn)
            elif current_node.node_type == NodeType.MODULE:
                pass
                self._process_module(current_fqn)

            # Push successors to the stack
            for successor in self.graph.successors(current_fqn):
                for key, edge_data in self.graph[current_fqn][successor].items():
                    if edge_data == ["contains"] and successor not in self.visited:
                        stack.append(successor)

    def _process_class(self, class_fqn):
        """
        Process a class node, gathering its methods, attributes, and relationships.
        """
        class_node = self.graph.nodes[class_fqn]['data']
        class_data = {
            'attributes': [],
            'methods': [],
            'is_abstract': self._is_abstract(class_fqn),
            'relationships': []
        }

        # Collect attributes and methods
        for source, target, edge_data in self.graph.out_edges(class_fqn, data=True):
            if 'inherits' in edge_data['relation']:
                continue
            successor_node = self.graph.nodes[target]['data']

            if successor_node.node_type == NodeType.ATTRIBUTE and 'defines' in edge_data['relation']:

                attr_type = self._get_node_type(successor_node.fqn)
                class_data['attributes'].append((successor_node.name, attr_type))
            elif successor_node.node_type == NodeType.METHOD and 'defines' in edge_data['relation']:
                method_signature = self._build_method_signature(successor_node.fqn)
                # look for body and constructor in the successors
                if "__init__" in successor_node.name:
                    classname = successor_node.fqn.split(".")[-2]
                    method_signature = method_signature.replace("__init__", classname)
                class_data['methods'].append(method_signature)

        # Generate PUML for the class
        item_type = 'abstract class' if class_data['is_abstract'] else 'class'

        self.puml_lines.append(f"{item_type} {class_fqn} {{")
        for attr_name, attr_type in class_data['attributes']:
            self.puml_lines.append(f"  {attr_name}: {attr_type}")
        for method_signature in class_data['methods']:
            self.puml_lines.append(f"  {method_signature}")
        self.puml_lines.append("}")

    def _process_module(self, module_fqn):
        """
        Process a package or module node.
        """
        module_node = self.graph.nodes[module_fqn]['data']

        module_data = {
            'methods': [],
            'relationships': []
        }

        # Collect attributes and methods
        for source, target, edge_data in self.graph.out_edges(module_fqn, data=True):
            successor_node = self.graph.nodes[target]['data']
            if successor_node.node_type == NodeType.METHOD and edge_data['relation'] == ['contains']:
                method_signature = self._build_method_signature(successor_node.fqn)
                # look for body and constructor in the successors

                # extract relationships

                module_data['methods'].append(method_signature)
        if len(module_data['methods']) > 0:
            item_type = 'annotation'
            self.puml_lines.append(f"{item_type} {module_fqn}.Methods {{")
            for method_signature in module_data['methods']:
                self.puml_lines.append(f"  {method_signature}")
            self.puml_lines.append("}")

    def _is_abstract(self, class_fqn):
        """
        Determine if a class is abstract by checking inheritance from `abc.ABC`.
        """
        for source, target, edge_data in self.graph.out_edges(data=True):
            if edge_data['relation'] == ['inherits'] and source == class_fqn and target == 'abc.ABC':
                return True
        return False

    def _build_method_signature(self, method_fqn):
        """
        Build a method signature string for PlantUML.
        """
        arguments = []
        return_type = []

        # Collect return type
        for edge_target, edge_data in self.graph.succ[method_fqn].items():
            if edge_data['relation'] is not None:
                if 'returns' in edge_data['relation']:
                    return_type.append(edge_target.split('.')[-1])
                if 'has_argument' in edge_data['relation']:
                    arguments.append(edge_target.split('.')[-1])

        # Collect arguments
        # for edge_target, edge_data in self.graph.pred[method_fqn].items():
        #     if edge_data['relation'] == 'has_argument':
        #         arguments.append(edge_target.split('.')[-1])

        method_node = self.graph.nodes[method_fqn]['data']
        if not return_type:
            return_type.append('None')
        return f"{method_node.name}({', '.join(arguments)}) -> {' | '.join(return_type)}"

    def _get_node_type(self, node_fqn):
        """
        Retrieve the type of a node based on its relationships in the graph.
        """
        types = []
        for edge_target, edge_data in self.graph.succ[node_fqn].items():
            if 'has_type' in edge_data['relation']:
                types.append(edge_target.split(".")[-1])

        return "|".join(types)

    def _puml_file_start(self):
        return PUML_FILE_START.format(diagram_name=self.diagram_name)

    def _puml_file_footer(self):
        return PUML_FILE_FOOTER

    def _puml_file_end(self):
        return PUML_FILE_END


def _map_relation_type(relation_type: str) -> str:
    """
    Map relation type to PlantUML syntax.
    """
    return {
        'inherits': '--|>',
        'uses': '-->',
        'defines': '*--',
        'has_attribute_with_type': '*--',
        'has_argument': '-->',
        'returns': '-->',
        'dependency': '-->',
        'aggregation': '*--',
        'composition': 'o--'
    }.get(relation_type)
