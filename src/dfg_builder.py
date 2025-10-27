"""
DFG构建器模块
从AST构建数据流图(DFG)
"""

from typing import Dict, List, Optional, Set, Any
import uuid

from .node_types import (
    ASTNode, DFG, DFGNode, DFGEdge, NodeType, EdgeType,
    FunctionNode, VariableNode, ExpressionNode, ContractNode
)


class DFGBuilder:
    """数据流图构建器"""
    
    def __init__(self, solidity_version: str = "0.4.x"):
        """初始化DFG构建器"""
        self.solidity_version = solidity_version
        self.legacy_handler = None
        # 暂时禁用legacy handler以避免导入问题
        # if solidity_version.startswith("0.4"):
        #     try:
        #         from .solidity_04x_handler import Solidity04xHandler
        #         self.legacy_handler = Solidity04xHandler()
        #     except ImportError:
        #         self.legacy_handler = None
        
        # 构建状态
        self.current_dfg: Optional[DFG] = None
        self.current_scope: Optional[str] = None
        self.scope_stack: List[str] = []
        self.variable_definitions: Dict[str, DFGNode] = {}
        self.function_definitions: Dict[str, DFGNode] = {}
        
        # 节点计数器
        self.node_counter = 0
        self.edge_counter = 0
    
    def generate_node_id(self) -> str:
        """生成唯一节点ID"""
        self.node_counter += 1
        return f"dfg_node_{self.node_counter}"
    
    def generate_edge_id(self) -> str:
        """生成唯一边ID"""
        self.edge_counter += 1
        return f"dfg_edge_{self.edge_counter}"
    
    def build_dfg(self, ast_root: ASTNode, contract_name: str) -> Optional[DFG]:
        """从AST根节点构建DFG"""
        if not ast_root:
            return None
        
        # 初始化DFG
        self.current_dfg = DFG(
            contract_name=contract_name,
            solidity_version=self.solidity_version,
            nodes={},
            edges={}
        )
        
        # 重置状态
        self.scope_stack = ["global"]
        self.current_scope = "global"
        self.variable_definitions = {}
        self.function_definitions = {}
        
        # 构建DFG
        self._build_node_dfg(ast_root)
        
        # 处理跨作用域的数据流
        self._build_inter_scope_flows()
        
        return self.current_dfg
    
    def _build_node_dfg(self, node: ASTNode) -> Optional[DFGNode]:
        """递归构建节点的DFG"""
        if not node or not self.current_dfg:
            return None
        
        dfg_node = self._create_dfg_node(node)
        if not dfg_node:
            return None
        
        # 根据节点类型处理
        if isinstance(node, ContractNode):
            self._build_contract_dfg(node, dfg_node)
        elif isinstance(node, FunctionNode):
            self._build_function_dfg(node, dfg_node)
        elif isinstance(node, VariableNode):
            self._build_variable_dfg(node, dfg_node)
        elif isinstance(node, ExpressionNode):
            self._build_expression_dfg(node, dfg_node)
        else:
            self._build_generic_dfg(node, dfg_node)
        
        return dfg_node
    
    def _create_dfg_node(self, ast_node: ASTNode) -> Optional[DFGNode]:
        """创建DFG节点"""
        if not ast_node:
            return None
        
        node_id = self.generate_node_id()
        
        # 确定节点类型和名称
        node_type = self._get_dfg_node_type(ast_node)
        node_name = self._get_node_name(ast_node)
        data_type = self._get_node_data_type(ast_node)
        
        dfg_node = DFGNode(
            node_id=node_id,
            ast_node=ast_node,
            node_type=node_type,
            name=node_name,
            data_type=data_type,
            scope=self.current_scope,
            properties=self._extract_node_properties(ast_node)
        )
        
        # 添加到DFG
        if self.current_dfg:
            self.current_dfg.add_node(dfg_node)
        
        return dfg_node
    
    def _get_dfg_node_type(self, ast_node: ASTNode) -> str:
        """获取DFG节点类型"""
        if isinstance(ast_node, FunctionNode):
            if ast_node.is_constructor:
                return "constructor_function"
            else:
                return "function"
        elif isinstance(ast_node, VariableNode):
            if ast_node.is_state_variable:
                return "state_variable"
            else:
                return "local_variable"
        elif isinstance(ast_node, ExpressionNode):
            return "expression"
        elif isinstance(ast_node, ContractNode):
            return "contract"
        else:
            return ast_node.node_type.value
    
    def _get_node_name(self, ast_node: ASTNode) -> Optional[str]:
        """获取节点名称"""
        if hasattr(ast_node, 'name') and ast_node.name:
            return ast_node.name
        return None
    
    def _get_node_data_type(self, ast_node: ASTNode) -> Optional[str]:
        """获取节点数据类型"""
        data_type = getattr(ast_node, 'data_type', None)
        return data_type if data_type else None
    
    def _extract_node_properties(self, ast_node: ASTNode) -> Dict[str, Any]:
        """提取节点属性"""
        properties = {}
        
        # 添加0.4.x特有属性
        if self.legacy_handler:
            self.legacy_handler.add_legacy_metadata(ast_node)
            if hasattr(ast_node, 'metadata') and ast_node.metadata:
                properties.update(ast_node.metadata)
        
        # 添加通用属性
        if hasattr(ast_node, 'source_location') and ast_node.source_location:
            properties['source_location'] = {
                'line': ast_node.source_location.line,
                'column': ast_node.source_location.column
            }
        
        return properties
    
    def _build_contract_dfg(self, contract_node: ContractNode, dfg_node: DFGNode) -> None:
        """构建合约的DFG"""
        # 进入合约作用域
        self._enter_scope(contract_node.name or "contract")
        
        # 处理合约的子节点
        if contract_node.children:
            for child in contract_node.children:
                child_dfg = self._build_node_dfg(child)
                if child_dfg:
                    # 添加合约到子节点的边
                    self._add_edge(dfg_node.node_id, child_dfg.node_id, EdgeType.DEFINITION)
        
        # 处理继承关系
        if contract_node.base_contracts:
            for base_contract in contract_node.base_contracts:
                properties = {"inheritance_type": "base_contract"}
                self._add_edge(dfg_node.node_id, f"contract_{base_contract}", EdgeType.DEFINITION, properties)
        
        # 退出合约作用域
        self._exit_scope()
    
    def _build_function_dfg(self, function_node: FunctionNode, dfg_node: DFGNode) -> None:
        """构建函数的DFG"""
        # 进入函数作用域
        function_scope = f"{function_node.name or 'anonymous'}_function"
        self._enter_scope(function_scope)
        
        # 记录函数定义
        if function_node.name:
            self.function_definitions[function_node.name] = dfg_node
        
        # 处理参数
        if function_node.parameters:
            for param in function_node.parameters:
                param_dfg = self._create_parameter_dfg(param, function_node)
                if param_dfg:
                    self._add_edge(dfg_node.node_id, param_dfg.node_id, EdgeType.DEFINITION)
        
        # 处理函数体
        if function_node.children:
            for child in function_node.children:
                child_dfg = self._build_node_dfg(child)
                if child_dfg:
                    self._add_edge(dfg_node.node_id, child_dfg.node_id, EdgeType.CONTROL_DEPENDENCY)
        
        # 处理返回值
        if function_node.return_parameters:
            for return_param in function_node.return_parameters:
                return_dfg = self._create_parameter_dfg(return_param, function_node, is_return=True)
                if return_dfg:
                    self._add_edge(dfg_node.node_id, return_dfg.node_id, EdgeType.DEFINITION)
        
        # 退出函数作用域
        self._exit_scope()
    
    def _build_variable_dfg(self, variable_node: VariableNode, dfg_node: DFGNode) -> None:
        """构建变量的DFG"""
        # 记录变量定义
        if variable_node.name:
            self.variable_definitions[f"{self.current_scope}.{variable_node.name}"] = dfg_node
        
        # 处理初始值表达式
        if variable_node.initial_value:
            # 这里需要解析初始值表达式，暂时简化处理
            properties = {"initialization": True}
            self._add_edge(dfg_node.node_id, f"init_{dfg_node.node_id}", EdgeType.DATA_DEPENDENCY, properties)
    
    def _build_expression_dfg(self, expression_node: ExpressionNode, dfg_node: DFGNode) -> None:
        """构建表达式的DFG"""
        # 处理操作数
        if expression_node.left_operand:
            left_dfg = self._build_node_dfg(expression_node.left_operand)
            if left_dfg:
                self._add_edge(left_dfg.node_id, dfg_node.node_id, EdgeType.DATA_DEPENDENCY)
        
        if expression_node.right_operand:
            right_dfg = self._build_node_dfg(expression_node.right_operand)
            if right_dfg:
                self._add_edge(right_dfg.node_id, dfg_node.node_id, EdgeType.DATA_DEPENDENCY)
        
        # 处理函数调用参数
        if expression_node.arguments:
            for arg in expression_node.arguments:
                if arg:
                    arg_dfg = self._build_node_dfg(arg)
                    if arg_dfg:
                        self._add_edge(arg_dfg.node_id, dfg_node.node_id, EdgeType.DATA_DEPENDENCY)
        
        # 处理变量引用
        self._handle_variable_reference(expression_node, dfg_node)
    
    def _build_generic_dfg(self, ast_node: ASTNode, dfg_node: DFGNode) -> None:
        """构建通用节点的DFG"""
        # 处理子节点
        if ast_node.children:
            for child in ast_node.children:
                child_dfg = self._build_node_dfg(child)
                if child_dfg:
                    self._add_edge(dfg_node.node_id, child_dfg.node_id, EdgeType.CONTROL_DEPENDENCY)
    
    def _create_parameter_dfg(self, param_info: Dict[str, Any], function_node: FunctionNode, is_return: bool = False) -> Optional[DFGNode]:
        """创建参数DFG节点"""
        if not param_info or not self.current_dfg:
            return None
        
        param_name = param_info.get('name', f"param_{self.node_counter}")
        param_type = param_info.get('type', 'unknown')
        
        # 创建虚拟AST节点
        from .node_types import ASTNode, NodeType, SourceLocation
        virtual_ast_node = ASTNode(
            node_id=self.generate_node_id(),
            node_type=NodeType.PARAMETER,
            name=param_name,
            metadata={"parameter_type": param_type, "is_return": is_return}
        )
        
        dfg_node = DFGNode(
            node_id=self.generate_node_id(),
            ast_node=virtual_ast_node,
            node_type="parameter",
            name=param_name,
            data_type=param_type,
            scope=self.current_scope,
            properties={"is_return": is_return, "function": function_node.name}
        )
        
        self.current_dfg.add_node(dfg_node)
        return dfg_node
    
    def _handle_variable_reference(self, expression_node: ExpressionNode, dfg_node: DFGNode) -> None:
        """处理变量引用"""
        if not expression_node.name:
            return
        
        # 查找变量定义
        var_key = f"{self.current_scope}.{expression_node.name}"
        if var_key in self.variable_definitions:
            def_node = self.variable_definitions[var_key]
            self._add_edge(def_node.node_id, dfg_node.node_id, EdgeType.DATA_DEPENDENCY, {"relation": "def-use"})
        
        # 查找状态变量
        global_var_key = f"global.{expression_node.name}"
        if global_var_key in self.variable_definitions:
            def_node = self.variable_definitions[global_var_key]
            self._add_edge(def_node.node_id, dfg_node.node_id, EdgeType.DATA_DEPENDENCY, {"relation": "state-var-use"})
    
    def _build_inter_scope_flows(self) -> None:
        """构建跨作用域的数据流"""
        if not self.current_dfg:
            return
        
        # 处理函数调用关系
        for func_name, func_node in self.function_definitions.items():
            # 查找函数调用
            for node_id, node in self.current_dfg.nodes.items():
                if node.node_type == "expression" and node.ast_node.text:
                    if f"{func_name}(" in node.ast_node.text:
                        self._add_edge(func_node.node_id, node_id, EdgeType.FUNCTION_CALL)
    
    def _add_edge(self, source_id: str, target_id: str, edge_type: EdgeType, properties: Optional[Dict[str, Any]] = None) -> None:
        """添加DFG边"""
        if not self.current_dfg:
            return
        
        edge_id = self.generate_edge_id()
        edge = DFGEdge(
            edge_id=edge_id,
            source_node_id=source_id,
            target_node_id=target_id,
            edge_type=edge_type,
            properties=properties or {}
        )
        
        self.current_dfg.add_edge(edge)
    
    def _enter_scope(self, scope_name: str) -> None:
        """进入新作用域"""
        self.scope_stack.append(scope_name)
        self.current_scope = scope_name
    
    def _exit_scope(self) -> None:
        """退出当前作用域"""
        if len(self.scope_stack) > 1:
            self.scope_stack.pop()
            self.current_scope = self.scope_stack[-1]
    
    def get_data_dependencies(self, node_id: str) -> List[DFGEdge]:
        """获取节点的数据依赖边"""
        if not self.current_dfg:
            return []
        
        return [edge for edge in self.current_dfg.get_incoming_edges(node_id) 
                if edge.edge_type == EdgeType.DATA_DEPENDENCY]
    
    def get_control_dependencies(self, node_id: str) -> List[DFGEdge]:
        """获取节点的控制依赖边"""
        if not self.current_dfg:
            return []
        
        return [edge for edge in self.current_dfg.get_incoming_edges(node_id) 
                if edge.edge_type == EdgeType.CONTROL_DEPENDENCY]
    
    def get_function_calls(self, node_id: str) -> List[DFGEdge]:
        """获取节点的函数调用边"""
        if not self.current_dfg:
            return []
        
        return [edge for edge in self.current_dfg.get_outgoing_edges(node_id) 
                if edge.edge_type == EdgeType.FUNCTION_CALL]
    
    def analyze_data_flow(self, start_node_id: str, end_node_id: str) -> List[str]:
        """分析两个节点之间的数据流路径"""
        if not self.current_dfg:
            return []
        
        # 简单的路径查找算法
        visited = set()
        path = []
        
        def dfs(current_id: str, target_id: str, current_path: List[str]) -> bool:
            if current_id == target_id:
                path.extend(current_path)
                return True
            
            if current_id in visited:
                return False
            
            visited.add(current_id)
            current_path.append(current_id)
            
            # 沿着数据依赖边搜索
            if self.current_dfg:
                outgoing_edges = self.current_dfg.get_outgoing_edges(current_id)
            else:
                outgoing_edges = []
            for edge in outgoing_edges:
                if edge.edge_type == EdgeType.DATA_DEPENDENCY:
                    if dfs(edge.target_node_id, target_id, current_path.copy()):
                        return True
            
            return False
        
        dfs(start_node_id, end_node_id, [])
        return path