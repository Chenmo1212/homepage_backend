# 测试说明 / Testing Guide

## 概述 / Overview

本项目使用 **mongomock** 来模拟 MongoDB 数据库，使得单元测试可以在没有真实 MongoDB 实例的环境中运行。这解决了本地开发和 CI/CD 环境中无法访问 MongoDB 的问题。

This project uses **mongomock** to simulate MongoDB database, allowing unit tests to run without a real MongoDB instance. This solves the problem of not having MongoDB access in local development and CI/CD environments.

## 技术方案 / Technical Solution

### 核心组件 / Core Components

1. **mongomock**: 纯 Python 实现的 MongoDB 模拟库
2. **pytest**: 测试框架
3. **conftest.py**: Pytest 配置文件，包含测试 fixtures
4. **test_api.py**: API 测试用例

### 工作原理 / How It Works

- `conftest.py` 使用 Python 的 `unittest.mock` 来拦截所有对 MongoDB 的调用
- 将真实的 `PyMongo` 替换为 `mongomock` 客户端
- 每个测试函数都会获得一个干净的数据库环境
- 测试结束后自动清理数据

## 安装依赖 / Install Dependencies

```bash
# 激活虚拟环境 / Activate virtual environment
source venv/bin/activate  # Linux/Mac
# 或 / or
venv\Scripts\activate  # Windows

# 安装依赖 / Install dependencies
pip install -r requirements.txt
```

## 运行测试 / Run Tests

### 基本运行 / Basic Run

```bash
pytest test_api.py
```

### 详细输出 / Verbose Output

```bash
pytest test_api.py -v
```

### 显示详细错误信息 / Show Detailed Errors

```bash
pytest test_api.py -v --tb=short
```

### 运行特定测试类 / Run Specific Test Class

```bash
pytest test_api.py::TestEntriesAPI -v
```

### 运行特定测试方法 / Run Specific Test Method

```bash
pytest test_api.py::TestEntriesAPI::test_create_message_entry -v
```

### 生成覆盖率报告 / Generate Coverage Report

```bash
# 安装 pytest-cov (如果还没安装)
pip install pytest-cov

# 运行测试并生成覆盖率报告
pytest test_api.py --cov=app --cov-report=html

# 查看报告
open htmlcov/index.html  # Mac
# 或 / or
start htmlcov/index.html  # Windows
```

## GitHub Actions 集成 / GitHub Actions Integration

项目已配置 GitHub Actions 工作流 (`.github/workflows/test.yml`)，会在以下情况自动运行测试：

The project has configured GitHub Actions workflow (`.github/workflows/test.yml`) that automatically runs tests when:

- Push 到 main 或 develop 分支 / Push to main or develop branch
- 创建 Pull Request 到 main 或 develop 分支 / Create Pull Request to main or develop branch

测试会在多个 Python 版本上运行：
Tests run on multiple Python versions:
- Python 3.8
- Python 3.9
- Python 3.10

## 测试覆盖范围 / Test Coverage

### 当前测试用例 / Current Test Cases

#### 1. Entries API 测试 (9 个测试)
- ✅ 创建 message 类型条目
- ✅ 创建 feedback 类型条目
- ✅ 创建 notification 类型条目
- ✅ 无效类型验证
- ✅ 必填字段验证
- ✅ 获取可见条目列表
- ✅ 按类型过滤
- ✅ 按来源过滤
- ✅ 分页功能

#### 2. Admin API 测试 (7 个测试)
- ✅ 获取所有条目（包括隐藏的）
- ✅ 管理员按类型过滤
- ✅ 更新条目状态
- ✅ 获取统计信息
- ✅ 获取所有支持的类型
- ✅ 获取类型 schema
- ✅ 批量删除条目

#### 3. 集成测试 (1 个测试)
- ✅ 多类型工作流测试

**总计: 17 个测试用例全部通过 ✅**

## 常见问题 / FAQ

### Q: 为什么使用 mongomock 而不是真实的 MongoDB？

A: 
1. **便携性**: 不需要安装和配置 MongoDB
2. **速度**: 内存数据库比真实数据库快得多
3. **隔离性**: 每个测试都有独立的数据库环境
4. **CI/CD 友好**: 在 GitHub Actions 等 CI 环境中无需额外配置

### Q: mongomock 的局限性是什么？

A: mongomock 不支持所有 MongoDB 功能，例如：
- 某些高级聚合操作
- 事务（transactions）
- 地理空间查询
- 全文搜索

但对于大多数 CRUD 操作和基本查询，mongomock 完全够用。

### Q: 如何添加新的测试用例？

A: 在 `test_api.py` 中添加新的测试方法：

```python
def test_your_new_feature(self, client):
    """Test description"""
    # 你的测试代码
    response = client.post('/api/v1/message/entries', json={...})
    assert response.status_code == 200
```

### Q: 测试失败了怎么办？

A: 
1. 查看详细错误信息：`pytest test_api.py -v --tb=long`
2. 检查是否所有依赖都已安装
3. 确保虚拟环境已激活
4. 查看 conftest.py 中的 mock 配置是否正确

## 最佳实践 / Best Practices

1. **每个测试应该独立**: 不要依赖其他测试的结果
2. **使用描述性的测试名称**: 测试名称应该清楚地说明测试的内容
3. **测试边界情况**: 不仅测试正常流程，也要测试错误情况
4. **保持测试简单**: 每个测试应该只测试一个功能点
5. **定期运行测试**: 在提交代码前运行所有测试

## 贡献 / Contributing

欢迎提交新的测试用例！请确保：
- 所有现有测试仍然通过
- 新测试有清晰的文档说明
- 遵循现有的代码风格

## 相关资源 / Resources

- [mongomock 文档](https://github.com/mongomock/mongomock)
- [pytest 文档](https://docs.pytest.org/)
- [Flask Testing 文档](https://flask.palletsprojects.com/en/2.0.x/testing/)

---

Made with ❤️ by Bob