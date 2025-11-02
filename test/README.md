# 测试脚本使用说明

本目录包含 AST-Solidity 项目的所有单元测试。

## 📋 测试文件列表

### 核心功能测试
- `test_result.py` - Result 类型（函数式错误处理）
- `test_config_manager.py` - 配置管理器
- `test_dfg_config.py` - DFG 配置模块
- `test_json_serializer.py` - JSON 序列化器
- `test_analyzer.py` - 主分析器
- `test_config.py` - 配置验证

### 工具类测试  
- `test_dataset_loader.py` - 数据集加载器（需要实现）
- `test_functional_helpers.py` - 功能性帮助函数（需要实现）

## 🚀 运行测试

### 运行所有测试

```bash
# 方式1: 使用测试运行脚本
python test/run_tests.py

# 方式2: 使用简化版本
python test_all.py

# 方式3: 使用 pytest (如果已安装)
pytest test/

# 方式4: 使用 unittest
python -m unittest discover -s test -p "test_*.py"
```

### 运行单个测试文件

```bash
# Result 类型测试
python test/test_result.py

# 配置管理器测试
python test/test_config_manager.py

# DFG配置测试
python test/test_dfg_config.py

# JSON序列化器测试
python test/test_json_serializer.py
```

### 运行特定测试用例

```bash
# 使用 unittest
python -m unittest test.test_result.TestResult.test_success_creation

# 使用 pytest
pytest test/test_result.py::TestResult::test_success_creation
```

## 📊 测试覆盖的模块

### ✅ 已完成测试
1. **Result 类型** (`src/utils/result.py`)
   - 成功/失败结果创建
   - 值和错误访问
   - map 和 flat_map 操作
   - unwrap_or 和 unwrap_or_else
   - 链式操作

2. **配置管理器** (`src/utils/config_manager.py`)
   - LLM 提供商配置
   - 检测配置
   - DFG 配置
   - 输出配置
   - 流水线配置
   - 从文件加载/保存配置
   - 从命令行参数加载

3. **DFG 配置** (`src/dfg_builder/dfg_config.py`)
   - 输出模式（compact/standard/verbose）
   - 节点优先级
   - 边优先级
   - 节点过滤规则
   - 关键字模式
   - 节点类型分类

4. **JSON 序列化器** (`src/json_serializer.py`)
   - DFG 序列化
   - 节点序列化
   - 边序列化
   - 文本包含和截断
   - 不同输出模式

### 🔄 待完善测试
5. **数据集加载器** (`src/utils/dataset_loader.py`)
6. **分析器** (`src/analyzer.py`)
7. **AST 构建器** (`src/ast_builder/`)
8. **DFG 构建器** (`src/dfg_builder/dfg_builder.py`)
9. **检测器** (`src/detector/`)
10. **可视化器** (`src/visualization/`)

## 🧪 测试统计

| 测试模块 | 测试用例数 | 状态 |
|---------|-----------|------|
| test_result.py | 18 | ✅ |
| test_config_manager.py | 15+ | ✅ |
| test_dfg_config.py | 20+ | ✅ |
| test_json_serializer.py | 10+ | ⚠️ |
| test_dataset_loader.py | 10+ | ⚠️ |
| test_analyzer.py | 5+ | ⚠️ |

## 💡 测试最佳实践

1. **每个测试应该独立**: 不依赖其他测试的结果
2. **使用描述性测试名**: `test_should_filter_keywords_in_standard_mode`
3. **测试边界情况**: 空值、None、极端值
4. **使用 setUp 和 tearDown**: 初始化和清理测试环境
5. **使用 Mock 对象**: 隔离被测试的组件

## 🐛 调试测试

```bash
# 详细输出
python test/test_result.py -v

# 只运行失败的测试
python test/test_result.py --verbose --failfast

# 显示完整的错误堆栈
python -m pytest test/test_result.py -v --tb=long
```

## 📝 添加新测试

1. 创建新测试文件 `test_<module>.py`
2. 导入 unittest 和被测试模块
3. 创建测试类继承 `unittest.TestCase`
4. 编写测试方法（以 `test_` 开头）
5. 使用断言验证结果

示例:
```python
import unittest

class TestMyModule(unittest.TestCase):
    def setUp(self):
        """每个测试前执行"""
        self.obj = MyClass()
    
    def test_my_feature(self):
        """测试某个功能"""
        result = self.obj.do_something()
        self.assertEqual(result, expected_value)
    
    def tearDown(self):
        """每个测试后执行"""
        pass

if __name__ == '__main__':
    unittest.main()
```

## 🎯 持续集成

测试可以集成到 CI/CD 流程中:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - run: pip install -r requirements.txt
      - run: python -m unittest discover test
```

## 📚 参考资源

- [Python unittest 文档](https://docs.python.org/3/library/unittest.html)
- [pytest 文档](https://docs.pytest.org/)
- [测试驱动开发](https://en.wikipedia.org/wiki/Test-driven_development)
