"""
AST构建器模块
使用tree-sitter-solidity解析Solidity源码并构建AST
"""

import tree_sitter
from typing import Optional, List, Dict, Any
from pathlib import Path

from .node_types import (
    ASTNode, ContractNode, FunctionNode, VariableNode, ExpressionNode,
    NodeType, SourceLocation, Visibility, StateMutability
)


class ASTBuilder:
    """AST构建器"""
    
    def __init__(self):
        """初始化AST构建器"""
        try:
            # 使用已安装的tree-sitter-solidity
            import tree_sitter_solidity
            language_ptr = tree_sitter_solidity.language()
            self.language = tree_sitter.Language(language_ptr)
            self.parser = tree_sitter.Parser(self.language)
        except Exception as e:
            print(f"Warning: Failed to initialize tree-sitter language: {e}")
            self.language = None
            self.parser = tree_sitter.Parser()
        
        # 节点ID计数器
        self.node_counter = 0
        self.current_scope = None
        self.solidity_version = "0.4.0"  # 默认版本
        
    def generate_node_id(self) -> str:
        """生成唯一节点ID"""
        self.node_counter += 1
        return f"node_{self.node_counter}"
    
    def parse_source(self, source_code: str) -> Optional[tree_sitter.Node]:
        """解析源码并返回语法树根节点"""
        tree = self.parser.parse(bytes(source_code, "utf8"))
        return tree.root_node
    
    def extract_solidity_version(self, root_node: tree_sitter.Node) -> str:
        """从AST中提取Solidity版本"""
        for child in root_node.children:
            if child.type == "pragma_directive":
                for pragma_child in child.children:
                    if pragma_child.type == "solidity_pragma_token":
                        # 提取版本信息
                        version_text = self.get_node_text(pragma_child)
                        # 简单版本提取，实际可能需要更复杂的解析
                        if "0.4" in version_text:
                            return "0.4.x"
                        elif "0.5" in version_text:
                            return "0.5.x"
                        elif "0.6" in version_text:
                            return "0.6.x"
                        elif "0.7" in version_text:
                            return "0.7.x"
                        elif "0.8" in version_text:
                            return "0.8.x"
        return "0.4.0"  # 默认版本
    
    def get_node_text(self, node: tree_sitter.Node) -> str:
        """获取节点的文本内容"""
        if node is None:
            return ""
        return node.text.decode('utf8')
    
    def get_source_location(self, node: tree_sitter.Node) -> SourceLocation:
        """获取节点的源码位置"""
        return SourceLocation(
            line=node.start_point[0] + 1,  # tree-sitter使用0基索引
            column=node.start_point[1] + 1,
            end_line=node.end_point[0] + 1,
            end_column=node.end_point[1] + 1
        )
    
    def build_ast(self, source_code: str) -> Optional[ASTNode]:
        """构建完整的AST"""
        root_node = self.parse_source(source_code)
        if not root_node:
            return None
        
        # 提取Solidity版本
        self.solidity_version = self.extract_solidity_version(root_node)
        
        # 构建AST
        return self.build_node(root_node)
    
    def build_node(self, node: tree_sitter.Node, parent: Optional[ASTNode] = None) -> Optional[ASTNode]:
        """递归构建AST节点"""
        if node is None:
            return None
        
        node_id = self.generate_node_id()
        node_type_str = node.type
        
        # 根据节点类型创建相应的AST节点
        if node_type_str == "contract_declaration":
            return self.build_contract_node(node, node_id, parent)
        elif node_type_str == "function_definition":
            return self.build_function_node(node, node_id, parent)
        elif node_type_str == "constructor_definition":
            return self.build_constructor_node(node, node_id, parent)
        elif node_type_str == "state_variable_declaration":
            return self.build_state_variable_node(node, node_id, parent)
        elif node_type_str == "variable_declaration":
            return self.build_variable_node(node, node_id, parent)
        elif node_type_str in ["binary_expression", "unary_expression", "assignment_expression", "call_expression", "member_expression"]:
            return self.build_expression_node(node, node_id, parent)
        else:
            # 通用节点处理
            return self.build_generic_node(node, node_id, parent)
    
    def build_contract_node(self, node: tree_sitter.Node, node_id: str, parent: Optional[ASTNode]) -> ContractNode:
        """构建合约节点"""
        name = self.extract_contract_name(node)
        base_contracts = self.extract_base_contracts(node)
        
        contract_node = ContractNode(
            node_id=node_id,
            node_type=NodeType.CONTRACT_DECLARATION,
            name=name,
            source_location=self.get_source_location(node),
            parent=parent,
            text=self.get_node_text(node),
            base_contracts=base_contracts,
            metadata={"solidity_version": self.solidity_version}
        )
        
        # 处理子节点
        for child in node.children:
            if child.type == "contract_body":
                for body_child in child.children:
                    child_node = self.build_node(body_child, contract_node)
                    if child_node and contract_node.children is not None:
                        contract_node.children.append(child_node)
        
        return contract_node
    
    def build_function_node(self, node: tree_sitter.Node, node_id: str, parent: Optional[ASTNode]) -> FunctionNode:
        """构建函数节点"""
        name = self.extract_function_name(node)
        parameters = self.extract_parameters(node)
        return_parameters = self.extract_return_parameters(node)
        visibility = self.extract_visibility(node)
        state_mutability = self.extract_state_mutability(node)
        modifiers = self.extract_modifiers(node)
        
        function_node = FunctionNode(
            node_id=node_id,
            node_type=NodeType.FUNCTION_DEFINITION,
            name=name,
            source_location=self.get_source_location(node),
            parent=parent,
            text=self.get_node_text(node),
            parameters=parameters,
            return_parameters=return_parameters,
            visibility=visibility,
            state_mutability=state_mutability,
            modifiers=modifiers,
            is_constructor=False,
            metadata={"solidity_version": self.solidity_version}
        )
        
        # 处理函数体
        for child in node.children:
            if child.type == "function_body":
                for body_child in child.children:
                    child_node = self.build_node(body_child, function_node)
                    if child_node and function_node.children is not None:
                        function_node.children.append(child_node)
        
        return function_node
    
    def build_constructor_node(self, node: tree_sitter.Node, node_id: str, parent: Optional[ASTNode]) -> FunctionNode:
        """构建构造函数节点"""
        parameters = self.extract_parameters(node)
        visibility = self.extract_visibility(node)
        state_mutability = self.extract_state_mutability(node)
        modifiers = self.extract_modifiers(node)
        
        constructor_node = FunctionNode(
            node_id=node_id,
            node_type=NodeType.CONSTRUCTOR_DEFINITION,
            name="constructor",
            source_location=self.get_source_location(node),
            parent=parent,
            text=self.get_node_text(node),
            parameters=parameters,
            visibility=visibility,
            state_mutability=state_mutability,
            modifiers=modifiers,
            is_constructor=True,
            metadata={"solidity_version": self.solidity_version}
        )
        
        # 处理构造函数体
        for child in node.children:
            if child.type == "function_body":
                for body_child in child.children:
                    child_node = self.build_node(body_child, constructor_node)
                    if child_node and constructor_node.children is not None:
                        constructor_node.children.append(child_node)
        
        return constructor_node
    
    def build_state_variable_node(self, node: tree_sitter.Node, node_id: str, parent: Optional[ASTNode]) -> VariableNode:
        """构建状态变量节点"""
        name = self.extract_variable_name(node)
        data_type = self.extract_variable_type(node)
        is_constant = self.has_constant_modifier(node)
        visibility = self.extract_visibility(node)
        initial_value = self.extract_initial_value(node)
        
        return VariableNode(
            node_id=node_id,
            node_type=NodeType.STATE_VARIABLE_DECLARATION,
            name=name,
            source_location=self.get_source_location(node),
            parent=parent,
            text=self.get_node_text(node),
            data_type=data_type,
            is_constant=is_constant,
            is_state_variable=True,
            visibility=visibility,
            initial_value=initial_value,
            metadata={"solidity_version": self.solidity_version}
        )
    
    def build_variable_node(self, node: tree_sitter.Node, node_id: str, parent: Optional[ASTNode]) -> VariableNode:
        """构建局部变量节点"""
        name = self.extract_variable_name(node)
        data_type = self.extract_variable_type(node)
        initial_value = self.extract_initial_value(node)
        
        return VariableNode(
            node_id=node_id,
            node_type=NodeType.VARIABLE_DECLARATION,
            name=name,
            source_location=self.get_source_location(node),
            parent=parent,
            text=self.get_node_text(node),
            data_type=data_type,
            is_state_variable=False,
            initial_value=initial_value,
            metadata={"solidity_version": self.solidity_version}
        )
    
    def build_expression_node(self, node: tree_sitter.Node, node_id: str, parent: Optional[ASTNode]) -> ExpressionNode:
        """构建表达式节点"""
        operator = self.extract_operator(node)
        
        expression_node = ExpressionNode(
            node_id=node_id,
            node_type=NodeType(node.type),
            source_location=self.get_source_location(node),
            parent=parent,
            text=self.get_node_text(node),
            operator=operator,
            metadata={"solidity_version": self.solidity_version}
        )
        
        # 处理操作数
        for child in node.children:
            if child.type not in [";", ",", "(", ")", "{", "}"]:
                child_node = self.build_node(child, expression_node)
                if child_node:
                    if not expression_node.left_operand:
                        expression_node.left_operand = child_node
                    elif not expression_node.right_operand:
                        expression_node.right_operand = child_node
                    else:
                        if expression_node.arguments is not None:
                            expression_node.arguments.append(child_node)
        
        return expression_node
    
    def build_generic_node(self, node: tree_sitter.Node, node_id: str, parent: Optional[ASTNode]) -> ASTNode:
        """构建通用节点"""
        try:
            node_type = NodeType(node.type)
        except ValueError:
            node_type = NodeType.IDENTIFIER
            
        generic_node = ASTNode(
            node_id=node_id,
            node_type=node_type,
            source_location=self.get_source_location(node),
            parent=parent,
            text=self.get_node_text(node),
            metadata={"solidity_version": self.solidity_version}
        )
        
        # 处理子节点
        for child in node.children:
            child_node = self.build_node(child, generic_node)
            if child_node and generic_node.children is not None:
                generic_node.children.append(child_node)
        
        return generic_node
    
    # 辅助方法
    def extract_contract_name(self, node: tree_sitter.Node) -> str:
        """提取合约名称"""
        for child in node.children:
            if child.type == "identifier":
                return self.get_node_text(child)
        return ""
    
    def extract_base_contracts(self, node: tree_sitter.Node) -> List[str]:
        """提取继承的合约列表"""
        base_contracts = []
        for child in node.children:
            if child.type == "inheritance_specifier":
                for identifier in child.children:
                    if identifier.type == "identifier":
                        base_contracts.append(self.get_node_text(identifier))
        return base_contracts
    
    def extract_function_name(self, node: tree_sitter.Node) -> str:
        """提取函数名称"""
        for child in node.children:
            if child.type == "identifier":
                return self.get_node_text(child)
        return ""
    
    def extract_parameters(self, node: tree_sitter.Node) -> List[Dict[str, Any]]:
        """提取函数参数"""
        parameters = []
        for child in node.children:
            if child.type == "parameter_list":
                for param in child.children:
                    if param.type == "parameter":
                        param_info = self.extract_parameter_info(param)
                        if param_info:
                            parameters.append(param_info)
        return parameters
    
    def extract_return_parameters(self, node: tree_sitter.Node) -> List[Dict[str, Any]]:
        """提取返回参数"""
        return_parameters = []
        for child in node.children:
            if child.type == "return_type_definition":
                for param in child.children:
                    if param.type == "parameter":
                        param_info = self.extract_parameter_info(param)
                        if param_info:
                            return_parameters.append(param_info)
        return return_parameters
    
    def extract_parameter_info(self, param_node: tree_sitter.Node) -> Optional[Dict[str, Any]]:
        """提取参数信息"""
        param_info = {}
        for child in param_node.children:
            if child.type == "type_name":
                param_info["type"] = self.get_node_text(child)
            elif child.type == "identifier":
                param_info["name"] = self.get_node_text(child)
        return param_info if param_info else None
    
    def extract_visibility(self, node: tree_sitter.Node) -> Optional[Visibility]:
        """提取可见性修饰符"""
        for child in node.children:
            if child.type == "visibility":
                visibility_text = self.get_node_text(child)
                if visibility_text == "public":
                    return Visibility.PUBLIC
                elif visibility_text == "private":
                    return Visibility.PRIVATE
                elif visibility_text == "internal":
                    return Visibility.INTERNAL
                elif visibility_text == "external":
                    return Visibility.EXTERNAL
        return None
    
    def extract_state_mutability(self, node: tree_sitter.Node) -> Optional[StateMutability]:
        """提取状态可变性修饰符"""
        for child in node.children:
            if child.type == "state_mutability":
                mutability_text = self.get_node_text(child)
                if mutability_text == "pure":
                    return StateMutability.PURE
                elif mutability_text == "view":
                    return StateMutability.VIEW
                elif mutability_text == "payable":
                    return StateMutability.PAYABLE
                elif mutability_text == "constant":
                    return StateMutability.CONSTANT
        return None
    
    def extract_modifiers(self, node: tree_sitter.Node) -> List[str]:
        """提取修饰符列表"""
        modifiers = []
        for child in node.children:
            if child.type == "modifier_invocation":
                for modifier in child.children:
                    if modifier.type == "identifier":
                        modifiers.append(self.get_node_text(modifier))
        return modifiers
    
    def extract_variable_name(self, node: tree_sitter.Node) -> str:
        """提取变量名称"""
        for child in node.children:
            if child.type == "identifier":
                return self.get_node_text(child)
        return ""
    
    def extract_variable_type(self, node: tree_sitter.Node) -> str:
        """提取变量类型"""
        for child in node.children:
            if child.type == "type_name":
                return self.get_node_text(child)
        return ""
    
    def has_constant_modifier(self, node: tree_sitter.Node) -> bool:
        """检查是否有constant修饰符"""
        for child in node.children:
            if child.type == "state_mutability" and self.get_node_text(child) == "constant":
                return True
        return False
    
    def extract_initial_value(self, node: tree_sitter.Node) -> Optional[str]:
        """提取初始值"""
        for child in node.children:
            if child.type == "expression":
                return self.get_node_text(child)
        return None
    
    def extract_operator(self, node: tree_sitter.Node) -> Optional[str]:
        """提取操作符"""
        for child in node.children:
            if child.type in ["+", "-", "*", "/", "%", "==", "!=", "<", "<=", ">", ">=", "&&", "||", "!", "&", "|", "^", "<<", ">>", "=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<=", ">>="]:
                return self.get_node_text(child)
        return None