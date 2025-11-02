"""
DFG构建配置模块
定义节点过滤、边过滤和输出选项
"""

from dataclasses import dataclass, field
from typing import Set, List, Optional
from enum import Enum


class OutputMode(Enum):
    """输出模式"""
    COMPACT = "compact"      # 精简模式：仅核心节点
    STANDARD = "standard"    # 标准模式：核心+部分辅助节点（默认）
    VERBOSE = "verbose"      # 详细模式：所有节点
    CUSTOM = "custom"        # 自定义模式


class NodePriority(Enum):
    """节点优先级"""
    CRITICAL = "critical"    # 核心节点：必须保留
    IMPORTANT = "important"  # 重要节点：默认保留
    AUXILIARY = "auxiliary"  # 辅助节点：可选保留
    DISCARD = "discard"      # 丢弃节点：不保留


class EdgePriority(Enum):
    """边优先级"""
    HIGH = "high"        # 高优先级：必须保留
    MEDIUM = "medium"    # 中优先级：默认保留
    LOW = "low"          # 低优先级：可选保留


@dataclass
class DFGConfig:
    """DFG构建配置"""
    
    # ==================== 输出模式 ====================
    output_mode: OutputMode = OutputMode.STANDARD
    
    # ==================== 节点过滤配置 ====================
    # 跳过的节点类型（精确匹配）
    skip_node_types: Set[str] = field(default_factory=set)
    
    # 保留的节点类型（如果设置，仅保留这些类型）
    include_node_types: Set[str] = field(default_factory=set)
    
    # 节点过滤选项
    skip_keywords: bool = True              # 跳过关键字节点（pragma, public, etc.）
    skip_type_names: bool = True            # 跳过类型名称节点（uint, address, etc.）
    skip_operators: bool = True             # 跳过操作符节点（+, -, *, etc.）
    skip_punctuation: bool = True           # 跳过标点符号节点
    merge_simple_expressions: bool = True   # 合并简单表达式
    skip_literal_nodes: bool = False        # 跳过字面量节点（可选）
    
    # 节点优先级阈值（低于此优先级的节点将被过滤）
    min_node_priority: NodePriority = NodePriority.IMPORTANT
    
    # ==================== 边过滤配置 ====================
    skip_sequential_control: bool = True    # 跳过顺序执行的控制依赖
    skip_redundant_edges: bool = True       # 跳过冗余边
    merge_parallel_edges: bool = True       # 合并相同类型的平行边
    
    # 边优先级阈值
    min_edge_priority: EdgePriority = EdgePriority.MEDIUM
    
    # ==================== 文本存储配置 ====================
    include_node_text: bool = False         # 是否包含节点文本
    text_max_length: int = 100              # 文本最大长度（超过则截断）
    store_source_location: bool = True      # 存储源码位置
    include_ast_metadata: bool = False      # 包含完整AST元数据
    
    # ==================== 性能配置 ====================
    enable_caching: bool = True             # 启用缓存
    max_nodes: int = 10000                  # 最大节点数限制
    max_edges: int = 20000                  # 最大边数限制
    
    def __post_init__(self):
        """初始化默认值"""
        # 根据输出模式设置默认配置
        self._apply_mode_defaults()
    
    def _apply_mode_defaults(self):
        """根据输出模式应用默认配置"""
        if self.output_mode == OutputMode.COMPACT:
            # 精简模式：最小化输出
            self.skip_keywords = True
            self.skip_type_names = True
            self.skip_operators = True
            self.skip_punctuation = True
            self.merge_simple_expressions = True
            self.skip_literal_nodes = True
            self.min_node_priority = NodePriority.CRITICAL
            self.skip_sequential_control = True
            self.skip_redundant_edges = True
            self.include_node_text = False
            self.include_ast_metadata = False
            
        elif self.output_mode == OutputMode.STANDARD:
            # 标准模式：平衡输出（默认设置）
            self.skip_keywords = True
            self.skip_type_names = True
            self.skip_operators = True
            self.skip_punctuation = True
            self.merge_simple_expressions = True
            self.skip_literal_nodes = False
            self.min_node_priority = NodePriority.IMPORTANT
            self.skip_sequential_control = True
            self.skip_redundant_edges = True
            self.include_node_text = False
            self.include_ast_metadata = False
            
        elif self.output_mode == OutputMode.VERBOSE:
            # 详细模式：完整输出
            self.skip_keywords = False
            self.skip_type_names = False
            self.skip_operators = False
            self.skip_punctuation = False
            self.merge_simple_expressions = False
            self.skip_literal_nodes = False
            self.min_node_priority = NodePriority.DISCARD
            self.skip_sequential_control = False
            self.skip_redundant_edges = False
            self.include_node_text = True
            self.include_ast_metadata = True
    
    @classmethod
    def compact(cls) -> 'DFGConfig':
        """创建精简模式配置"""
        return cls(output_mode=OutputMode.COMPACT)
    
    @classmethod
    def standard(cls) -> 'DFGConfig':
        """创建标准模式配置"""
        return cls(output_mode=OutputMode.STANDARD)
    
    @classmethod
    def verbose(cls) -> 'DFGConfig':
        """创建详细模式配置"""
        return cls(output_mode=OutputMode.VERBOSE)


# ==================== 节点分类定义 ====================

# 核心节点类型（必须保留）
CRITICAL_NODE_TYPES = {
    "contract",
    "interface",
    "library",
    "function",
    "constructor_function",
    "modifier",
    "state_variable",
}

# 重要节点类型（默认保留）
IMPORTANT_NODE_TYPES = {
    "local_variable",
    "parameter",
    "expression",
    "if_statement",
    "for_statement",
    "while_statement",
    "return_statement",
    "struct_declaration",
    "enum_declaration",
    "event_definition",
}

# 辅助节点类型（可选保留）
AUXILIARY_NODE_TYPES = {
    "number_literal",
    "string_literal",
    "boolean_literal",
    "expression_statement",
    "block",
}

# 应该被过滤的节点类型（基于节点名称）
KEYWORD_PATTERNS = {
    "pragma", "solidity", "contract", "function", "public", "private",
    "internal", "external", "pure", "view", "payable", "constant",
    "memory", "storage", "calldata", "returns", "return", "if", "else",
    "for", "while", "do", "break", "continue", "throw", "require",
    "assert", "revert", "emit", "new", "delete", "struct", "enum",
    "mapping", "address", "uint", "int", "bool", "string", "bytes",
    "uint8", "uint16", "uint32", "uint64", "uint128", "uint256",
    "int8", "int16", "int32", "int64", "int128", "int256",
    "bytes1", "bytes2", "bytes4", "bytes8", "bytes16", "bytes32",
}

# 类型名称关键字
TYPE_KEYWORDS = {
    "uint", "int", "address", "bool", "string", "bytes",
    "uint8", "uint16", "uint32", "uint64", "uint128", "uint256",
    "int8", "int16", "int32", "int64", "int128", "int256",
    "bytes1", "bytes2", "bytes4", "bytes8", "bytes16", "bytes32",
    "mapping", "struct", "enum",
}

# 操作符
OPERATORS = {
    "+", "-", "*", "/", "%", "**",
    "==", "!=", "<", ">", "<=", ">=",
    "&&", "||", "!",
    "&", "|", "^", "~", "<<", ">>",
    "=", "+=", "-=", "*=", "/=", "%=",
    "++", "--",
    "?", ":",
}

# 标点符号
PUNCTUATION = {
    "(", ")", "{", "}", "[", "]",
    ";", ",", ".", "=>",
}


def get_node_priority(node_type: str, node_name: Optional[str] = None, node_text: Optional[str] = None) -> NodePriority:
    """
    确定节点的优先级
    
    Args:
        node_type: 节点类型
        node_name: 节点名称
        node_text: 节点文本
    
    Returns:
        NodePriority: 节点优先级
    """
    # 检查是否为核心节点
    if node_type in CRITICAL_NODE_TYPES:
        return NodePriority.CRITICAL
    
    # 检查是否为重要节点
    if node_type in IMPORTANT_NODE_TYPES:
        return NodePriority.IMPORTANT
    
    # 检查是否为辅助节点
    if node_type in AUXILIARY_NODE_TYPES:
        return NodePriority.AUXILIARY
    
    # 检查是否为关键字节点
    if node_type == "identifier" and node_text:
        text_lower = node_text.strip().lower()
        if text_lower in KEYWORD_PATTERNS:
            return NodePriority.DISCARD
        if text_lower in TYPE_KEYWORDS:
            return NodePriority.DISCARD
        if text_lower in OPERATORS:
            return NodePriority.DISCARD
        if text_lower in PUNCTUATION:
            return NodePriority.DISCARD
    
    # 默认为辅助节点
    return NodePriority.AUXILIARY


def should_keep_node(node_type: str, node_name: str, node_text: str, config: DFGConfig) -> bool:
    """
    判断是否应该保留节点
    
    Args:
        node_type: 节点类型
        node_name: 节点名称
        node_text: 节点文本
        config: DFG配置
    
    Returns:
        bool: 是否保留节点
    """
    # 如果指定了包含类型，只保留指定类型
    if config.include_node_types and node_type not in config.include_node_types:
        return False
    
    # 如果在跳过列表中，不保留
    if node_type in config.skip_node_types:
        return False
    
    # 获取节点优先级
    priority = get_node_priority(node_type, node_name, node_text)
    
    # 检查优先级阈值
    priority_order = {
        NodePriority.CRITICAL: 4,
        NodePriority.IMPORTANT: 3,
        NodePriority.AUXILIARY: 2,
        NodePriority.DISCARD: 1,
    }
    
    if priority_order[priority] < priority_order[config.min_node_priority]:
        return False
    
    # 特殊规则检查
    if node_type == "identifier" and node_text:
        text_lower = node_text.strip().lower()
        
        # 跳过关键字
        if config.skip_keywords and text_lower in KEYWORD_PATTERNS:
            return False
        
        # 跳过类型名称
        if config.skip_type_names and text_lower in TYPE_KEYWORDS:
            return False
        
        # 跳过操作符
        if config.skip_operators and text_lower in OPERATORS:
            return False
        
        # 跳过标点符号
        if config.skip_punctuation and text_lower in PUNCTUATION:
            return False
    
    # 跳过字面量节点
    if config.skip_literal_nodes and node_type.endswith("_literal"):
        return False
    
    return True
