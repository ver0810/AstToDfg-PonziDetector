"""
Solidity 0.4.x特性处理器
处理Solidity 0.4.x版本的特有语法和语义特性
"""

from typing import Optional, List, Dict, Any
import re

from .node_types import (
    ASTNode, FunctionNode, VariableNode, NodeType,
    StateMutability, Visibility, ContractNode
)


class Solidity04xHandler:
    """Solidity 0.4.x特性处理器"""
    
    def __init__(self):
        """初始化处理器"""
        self.version = "0.4.x"
        self.legacy_keywords = {
            "constant", "view", "pure", "payable", "public", 
            "private", "internal", "external", "returns", "return"
        }
        
        # 0.4.x特有的全局变量
        self.legacy_global_vars = {
            "now", "msg", "block", "tx", "this", "super"
        }
        
        # 0.4.x特有的类型
        self.legacy_types = {
            "address", "uint", "int", "bool", "string", "bytes",
            "byte", "fixed", "ufixed"
        }
    
    def is_legacy_constructor(self, function_node: FunctionNode, contract_name: str) -> bool:
        """判断是否为0.4.x风格的构造函数（与合约同名）"""
        if not function_node or not function_node.name:
            return False
        
        # 0.4.x构造函数与合约同名
        return function_node.name == contract_name and not function_node.is_constructor
    
    def identify_constructor(self, contract_node: ASTNode) -> Optional[FunctionNode]:
        """识别合约中的构造函数（支持0.4.x和0.5.x+）"""
        if not contract_node or not contract_node.children:
            return None
        
        contract_name = contract_node.name if hasattr(contract_node, 'name') else ""
        constructor = None
        
        for child in contract_node.children:
            if isinstance(child, FunctionNode):
                # 0.5.x+ 使用constructor关键字
                if child.is_constructor:
                    return child
                # 0.4.x 使用与合约同名的函数
                elif contract_name and self.is_legacy_constructor(child, contract_name):
                    constructor = child
        
        return constructor
    
    def process_constant_modifier(self, variable_node: VariableNode) -> bool:
        """处理0.4.x的constant修饰符"""
        if not variable_node:
            return False
        
        # 检查是否有constant修饰符
        if hasattr(variable_node, 'metadata') and variable_node.metadata:
            return variable_node.metadata.get('has_constant', False)
        
        # 检查文本中是否包含constant
        if variable_node.text and 'constant' in variable_node.text:
            return True
        
        return False
    
    def process_legacy_state_mutability(self, function_node: FunctionNode) -> Optional[StateMutability]:
        """处理0.4.x的状态可变性修饰符"""
        if not function_node:
            return None
        
        # 0.4.x中constant等同于view
        if function_node.state_mutability == StateMutability.CONSTANT:
            return StateMutability.VIEW
        
        return function_node.state_mutability
    
    def identify_legacy_global_variables(self, node_text: str) -> List[str]:
        """识别0.4.x特有的全局变量"""
        if not node_text:
            return []
        
        found_vars = []
        for var in self.legacy_global_vars:
            # 使用正则表达式匹配完整的变量名
            pattern = r'\b' + re.escape(var) + r'\b'
            if re.search(pattern, node_text):
                found_vars.append(var)
        
        return found_vars
    
    def process_now_keyword(self, node_text: str) -> bool:
        """处理0.4.x的now关键字（等同于block.timestamp）"""
        return 'now' in node_text if node_text else False
    
    def process_suicide_keyword(self, node_text: str) -> bool:
        """处理0.4.x的suicide关键字（等同于selfdestruct）"""
        return 'suicide' in node_text if node_text else False
    
    def process_legacy_call_syntax(self, node_text: str) -> Dict[str, Any]:
        """处理0.4.x的调用语法"""
        if not node_text:
            return {}
        
        legacy_features = {}
        
        # 检查call.value语法（0.4.x风格）
        if '.call.value(' in node_text:
            legacy_features['call_value_syntax'] = True
        
        # 检查transfer语法
        if '.transfer(' in node_text:
            legacy_features['transfer_syntax'] = True
        
        # 检查send语法
        if '.send(' in node_text:
            legacy_features['send_syntax'] = True
        
        # 检查delegatecall语法
        if '.delegatecall(' in node_text:
            legacy_features['delegatecall_syntax'] = True
        
        return legacy_features
    
    def process_legacy_type_syntax(self, node_text: str) -> Dict[str, Any]:
        """处理0.4.x的类型语法"""
        if not node_text:
            return {}
        
        type_features = {}
        
        # 检查var关键字（0.4.x支持）
        if 'var ' in node_text:
            type_features['var_keyword'] = True
        
        # 检查类型转换语法
        if re.search(r'\buint\d*\b', node_text):
            type_features['uint_sized'] = True
        
        if re.search(r'\bint\d*\b', node_text):
            type_features['int_sized'] = True
        
        if re.search(r'\bbytes\d+\b', node_text):
            type_features['bytes_sized'] = True
        
        return type_features
    
    def add_legacy_metadata(self, node: ASTNode) -> None:
        """为节点添加0.4.x特有的元数据"""
        if not node or not hasattr(node, 'metadata'):
            return
        
        if node.metadata is None:
            node.metadata = {}
        
        node.metadata['solidity_version'] = self.version
        node.metadata['is_legacy'] = True
        
        # 根据节点类型添加特定的元数据
        if isinstance(node, FunctionNode):
            self._add_function_legacy_metadata(node)
        elif isinstance(node, VariableNode):
            self._add_variable_legacy_metadata(node)
        
        # 处理通用特性
        if node.text:
            legacy_globals = self.identify_legacy_global_variables(node.text)
            if legacy_globals:
                node.metadata['legacy_global_vars'] = legacy_globals
            
            if self.process_now_keyword(node.text):
                node.metadata['uses_now_keyword'] = True
            
            if self.process_suicide_keyword(node.text):
                node.metadata['uses_suicide_keyword'] = True
            
            call_syntax = self.process_legacy_call_syntax(node.text)
            if call_syntax:
                node.metadata['legacy_call_syntax'] = call_syntax
            
            type_syntax = self.process_legacy_type_syntax(node.text)
            if type_syntax:
                node.metadata['legacy_type_syntax'] = type_syntax
    
    def _add_function_legacy_metadata(self, function_node: FunctionNode) -> None:
        """为函数节点添加0.4.x特有的元数据"""
        if not function_node.metadata:
            function_node.metadata = {}
        
        # 检查是否为legacy构造函数
        if function_node.parent and hasattr(function_node.parent, 'name'):
            parent_name = function_node.parent.name
            if parent_name and self.is_legacy_constructor(function_node, parent_name):
                function_node.metadata['is_legacy_constructor'] = True
                function_node.is_constructor = True
        
        # 处理状态可变性
        legacy_mutability = self.process_legacy_state_mutability(function_node)
        if legacy_mutability and legacy_mutability != function_node.state_mutability:
            function_node.metadata['legacy_state_mutability'] = legacy_mutability.value
            function_node.state_mutability = legacy_mutability
        
        # 检查默认可见性（0.4.x中函数默认是public）
        if function_node.visibility is None:
            function_node.metadata['default_visibility'] = 'public'
            function_node.visibility = Visibility.PUBLIC
    
    def _add_variable_legacy_metadata(self, variable_node: VariableNode) -> None:
        """为变量节点添加0.4.x特有的元数据"""
        if not variable_node.metadata:
            variable_node.metadata = {}
        
        # 处理constant修饰符
        if self.process_constant_modifier(variable_node):
            variable_node.metadata['has_constant_modifier'] = True
            variable_node.is_constant = True
        
        # 检查默认可见性（0.4.x中状态变量默认是internal）
        if variable_node.is_state_variable and variable_node.visibility is None:
            variable_node.metadata['default_visibility'] = 'internal'
            variable_node.visibility = Visibility.INTERNAL
    
    def process_contract_inheritance(self, contract_node: ASTNode) -> Dict[str, Any]:
        """处理0.4.x的合约继承特性"""
        if not contract_node:
            return {}
        
        # 获取基础合约列表
        base_contracts = []
        if isinstance(contract_node, ContractNode) and contract_node.base_contracts:
            base_contracts = list(contract_node.base_contracts)
        
        inheritance_info = {
            'has_inheritance': len(base_contracts) > 0,
            'base_contracts': base_contracts,
            'multiple_inheritance': len(base_contracts) > 1
        }
        
        # 0.4.x特有的继承特性
        if contract_node.text:
            # 检查是否使用了is关键字
            if ' is ' in contract_node.text:
                inheritance_info['uses_is_keyword'] = True
            
            # 检查构造函数参数传递
            if re.search(r'\w+\([^)]*\)\s*is\s*\w+', contract_node.text):
                inheritance_info['constructor_args_inheritance'] = True
        
        return inheritance_info
    
    def validate_04x_syntax(self, node_text: str) -> List[str]:
        """验证0.4.x语法的有效性"""
        if not node_text:
            return []
        
        warnings = []
        
        # 检查已弃用的语法
        if 'suicide(' in node_text:
            warnings.append("suicide() is deprecated, use selfdestruct() instead")
        
        if 'var ' in node_text:
            warnings.append("var keyword is deprecated, specify explicit type instead")
        
        if 'callcode(' in node_text:
            warnings.append("callcode() is deprecated, use delegatecall() instead")
        
        # 检查版本不兼容的语法
        if 'constructor()' in node_text:
            warnings.append("constructor() keyword not available in 0.4.x, use contract name instead")
        
        return warnings
    
    def get_version_specific_features(self) -> Dict[str, Any]:
        """获取0.4.x版本特有的特性列表"""
        return {
            'constructor_style': 'contract_name_function',
            'default_visibility': {
                'functions': 'public',
                'state_variables': 'internal'
            },
            'deprecated_keywords': ['suicide', 'var', 'callcode'],
            'legacy_global_vars': ['now'],
            'constant_equals_view': True,
            'supports_implicit_conversion': True,
            'constructor_visibility': 'public'
        }