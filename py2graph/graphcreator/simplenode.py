from py2graph.parser.parser_interface import NodeType


class SimpleNode:
    def __init__(self, fqn: str, name: str, node_type: NodeType):
        if not isinstance(node_type, NodeType):
            raise ValueError(f"Invalid node_type: {node_type}. Expected a NodeType enum value.")

        self.fqn = fqn
        self.name = name
        self.node_type = node_type

    def __hash__(self):
        # Hash based on essential attributes
        return hash((self.fqn, self.name, self.node_type))

    def __eq__(self, other):
        if not isinstance(other, SimpleNode):
            return False
        return self.fqn == other.fqn and self.name == other.name and self.node_type == other.node_type

    def __repr__(self):
        return f"{self.node_type.value.capitalize()}Node({self.name})"
