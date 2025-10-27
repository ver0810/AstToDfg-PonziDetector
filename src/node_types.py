"""
节点类型定义模块
定义AST和DFG中使用的节点类型和枚举
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


class NodeType(Enum):
    """AST节点类型枚举"""
    # 合约相关
    CONTRACT_DECLARATION = "contract_declaration"
    INTERFACE_DECLARATION = "interface_declaration"
    LIBRARY_DECLARATION = "library_declaration"
    
    # 函数相关
    FUNCTION_DEFINITION = "function_definition"
    CONSTRUCTOR_DEFINITION = "constructor_definition"
    FALLBACK_RECEIVE_DEFINITION = "fallback_receive_definition"
    MODIFIER_DEFINITION = "modifier_definition"
    
    # 变量相关
    STATE_VARIABLE_DECLARATION = "state_variable_declaration"
    VARIABLE_DECLARATION = "variable_declaration"
    PARAMETER = "parameter"
    
    # 语句相关
    EXPRESSION_STATEMENT = "expression_statement"
    IF_STATEMENT = "if_statement"
    FOR_STATEMENT = "for_statement"
    WHILE_STATEMENT = "while_statement"
    RETURN_STATEMENT = "return_statement"
    BLOCK = "block"
    
    # 表达式相关
    BINARY_EXPRESSION = "binary_expression"
    UNARY_EXPRESSION = "unary_expression"
    ASSIGNMENT_EXPRESSION = "assignment_expression"
    CALL_EXPRESSION = "call_expression"
    MEMBER_EXPRESSION = "member_expression"
    IDENTIFIER = "identifier"
    NUMBER_LITERAL = "number_literal"
    STRING_LITERAL = "string_literal"
    BOOLEAN_LITERAL = "boolean_literal"
    
    # 类型相关
    TYPE_NAME = "type_name"
    PRIMITIVE_TYPE = "primitive_type"
    USER_DEFINED_TYPE = "user_defined_type"
    MAPPING_TYPE = "mapping_type"
    ARRAY_TYPE = "array_type"
    
    # 其他
    PRAGMA_DIRECTIVE = "pragma_directive"
    IMPORT_DIRECTIVE = "import_directive"
    EVENT_DEFINITION = "event_definition"
    STRUCT_DECLARATION = "struct_declaration"
    ENUM_DECLARATION = "enum_declaration"


class EdgeType(Enum):
    """DFG边类型枚举"""
    DATA_DEPENDENCY = "data_dependency"  # 数据依赖
    CONTROL_DEPENDENCY = "control_dependency"  # 控制依赖
    FUNCTION_CALL = "function_call"  # 函数调用
    DEFINITION = "definition"  # 定义关系
    USAGE = "usage"  # 使用关系
    MODIFIES = "modifies"  # 修改关系


class Visibility(Enum):
    """可见性枚举"""
    PUBLIC = "public"
    PRIVATE = "private"
    INTERNAL = "internal"
    EXTERNAL = "external"


class StateMutability(Enum):
    """状态可变性枚举"""
    PURE = "pure"
    VIEW = "view"
    PAYABLE = "payable"
    CONSTANT = "constant"  # 0.4.x特有
    NONPAYABLE = "nonpayable"


@dataclass
class SourceLocation:
    """源码位置信息"""
    line: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None


@dataclass
class ASTNode:
    """AST节点基类"""
    node_id: str
    node_type: NodeType
    name: Optional[str] = None
    source_location: Optional[SourceLocation] = None
    children: Optional[List['ASTNode']] = None
    parent: Optional['ASTNode'] = None
    text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ContractNode(ASTNode):
    """合约节点"""
    base_contracts: Optional[List[str]] = None
    
    def __post_init__(self):
        super().__post_init__()
        if self.base_contracts is None:
            self.base_contracts = []


@dataclass
class FunctionNode(ASTNode):
    """函数节点"""
    parameters: Optional[List[Dict[str, Any]]] = None
    return_parameters: Optional[List[Dict[str, Any]]] = None
    visibility: Optional[Visibility] = None
    state_mutability: Optional[StateMutability] = None
    modifiers: Optional[List[str]] = None
    is_constructor: bool = False
    is_fallback: bool = False
    is_receive: bool = False
    
    def __post_init__(self):
        super().__post_init__()
        if self.parameters is None:
            self.parameters = []
        if self.return_parameters is None:
            self.return_parameters = []
        if self.modifiers is None:
            self.modifiers = []


@dataclass
class VariableNode(ASTNode):
    """变量节点"""
    data_type: Optional[str] = None
    is_constant: bool = False
    is_state_variable: bool = False
    is_immutable: bool = False
    visibility: Optional[Visibility] = None
    initial_value: Optional[str] = None


@dataclass
class ExpressionNode(ASTNode):
    """表达式节点"""
    operator: Optional[str] = None
    left_operand: Optional['ASTNode'] = None
    right_operand: Optional['ASTNode'] = None
    arguments: Optional[List['ASTNode']] = None
    
    def __post_init__(self):
        super().__post_init__()
        if self.arguments is None:
            self.arguments = []


@dataclass
class DFGNode:
    """DFG节点"""
    node_id: str
    ast_node: ASTNode
    node_type: str
    name: Optional[str] = None
    data_type: Optional[str] = None
    scope: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


@dataclass
class DFGEdge:
    """DFG边"""
    edge_id: str
    source_node_id: str
    target_node_id: str
    edge_type: EdgeType
    label: Optional[str] = None
    weight: int = 1
    properties: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


@dataclass
class DFG:
    """数据流图"""
    contract_name: str
    solidity_version: str
    nodes: Dict[str, DFGNode]
    edges: Dict[str, DFGEdge]
    entry_node_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def add_node(self, node: DFGNode):
        """添加节点"""
        self.nodes[node.node_id] = node
    
    def add_edge(self, edge: DFGEdge):
        """添加边"""
        self.edges[edge.edge_id] = edge
    
    def get_node(self, node_id: str) -> Optional[DFGNode]:
        """获取节点"""
        return self.nodes.get(node_id)
    
    def get_edge(self, edge_id: str) -> Optional[DFGEdge]:
        """获取边"""
        return self.edges.get(edge_id)
    
    def get_outgoing_edges(self, node_id: str) -> List[DFGEdge]:
        """获取节点的出边"""
        return [edge for edge in self.edges.values() if edge.source_node_id == node_id]
    
    def get_incoming_edges(self, node_id: str) -> List[DFGEdge]:
        """获取节点的入边"""
        return [edge for edge in self.edges.values() if edge.target_node_id == node_id]