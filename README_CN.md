# Homepage Backend - 聚合API系统

**语言选择:** [English](README.md) | [简体中文](README_CN.md)

<p>
    <a href="https://www.chenmo1212.cn?f=github-backend" target="_blank">
        <img alt="GitHub Workflow Status" src="https://img.shields.io/badge/Backend-Portfolio's--backend-orange">
    </a>
    <a href="https://github.com/Chenmo1212/homepage_backend" target="_blank">
        <img alt="GitHub repo size" src="https://img.shields.io/github/repo-size/Chenmo1212/homepage_backend">
    </a>
    <a href="https://github.com/Chenmo1212/homepage_backend/issues" target="_blank">
        <img alt="Issues" src="https://img.shields.io/github/issues/Chenmo1212/homepage_backend" />
    </a>
    <a href="https://github.com/Chenmo1212/homepage_backend/pulls" target="_blank">
        <img alt="GitHub pull requests" src="https://img.shields.io/github/issues-pr/Chenmo1212/homepage_backend" />
    </a>
    <a href="/">
        <img src="https://komarev.com/ghpvc/?username=chenmo1212-homepage-backend&label=Visitors&base=200" alt="Visitor" />
    </a>
    <a href="https://github.com/Chenmo1212/homepage_backend" target="_blank">
        <img alt="GitHub" src="https://img.shields.io/github/license/Chenmo1212/homepage_backend">
    </a>
<br/>
<br/>
    <a href="https://github.com/Chenmo1212/homepage_backend" target="_blank">
        <img alt="GitHub followers" src="https://img.shields.io/github/followers/pudongping?style=social">
    </a>
    <a href="https://github.com/Chenmo1212/homepage_backend" target="_blank">
        <img alt="GitHub forks" src="https://img.shields.io/github/forks/Chenmo1212/homepage_backend?style=social">
    </a>
    <a href="https://github.com/Chenmo1212/homepage_backend" target="_blank">
        <img alt="GitHub stars" src="https://img.shields.io/github/stars/Chenmo1212/homepage_backend?style=social">
    </a>
    <a href="https://github.com/Chenmo1212/homepage_backend" target="_blank">
        <img alt="GitHub watchers" src="https://img.shields.io/github/watchers/Chenmo1212/homepage_backend?style=social">
    </a>
</p>

## 📖 项目简介

这是一个基于 **Flask + MongoDB** 的**聚合API后端系统**。最初为个人主页的留言功能设计，现已升级为支持多种类型数据的通用API系统，可用于留言、反馈、通知等多种场景。

🌐 查看我的作品集：[https://www.chenmo1212.cn](https://www.chenmo1212.cn?f=github-backend)

### ✨ 核心特性

- 🎯 **多类型支持** - 支持message、feedback、notification等多种entry类型
- 🔧 **灵活的Schema验证** - 基于JSON Schema的动态字段验证
- 🔄 **向后兼容** - 原有的`/messages`端点继续可用
- 🏢 **多项目支持** - 通过`source`字段区分不同项目
- ⚙️ **动态类型系统** - 通过配置文件轻松添加新类型
- 📱 **企业微信通知** - 支持多模板的自动通知系统
- 🌍 **UTF-8支持** - 完美支持中文等多语言字符

---

## 🏗️ 架构设计

### 核心概念

系统采用**Entry**作为统一的数据模型，每个Entry包含：

```python
{
  "type": "message",           # 类型：message/feedback/notification
  "source": "homepage",        # 来源：区分不同项目
  "metadata": {...},           # 元数据：根据type不同而不同
  "status": {                  # 状态管理
    "is_show": false,          # 是否可见
    "is_delete": false,        # 是否删除
    "is_read": false           # 是否已读
  },
  "timestamps": {...},         # 时间戳
  "agent": "",                 # 用户代理
  "tags": []                   # 标签
}
```

### 目录结构

```
homepage_backend/
├── app/
│   ├── __init__.py                 # Flask应用初始化
│   ├── models/
│   │   ├── entry.py               # Entry统一模型
│   │   └── message.py             # Message模型（向后兼容）
│   ├── routes/
│   │   ├── entries.py             # 新API路由
│   │   ├── admin.py               # 管理API路由
│   │   └── messages_compat.py     # 兼容API路由
│   ├── config/
│   │   ├── type_manager.py        # 类型管理器
│   │   └── entry_types.json       # 类型配置文件
│   ├── validators/
│   │   └── schema_validator.py    # Schema验证器
│   └── notifications/
│       └── notification_service.py # 通知服务
├── migrations/
│   └── migrate_to_entries.py      # 数据迁移脚本
├── config_development.py           # 开发环境配置
├── config_production.py            # 生产环境配置
└── migrate_from_messages_db.py    # 跨数据库迁移工具
```

---

## 🎯 支持的Entry类型

### 1. Message（留言）

用于用户留言、评论等场景。

**必需字段：**
- `name` (string): 用户名称
- `email` (string): 邮箱地址
- `content` (string): 留言内容

**可选字段：**
- `website` (string): 个人网站

**示例：**
```bash
curl -X POST http://localhost:5001/messages \
  -H "Content-Type: application/json" \
  -d '{
    "name": "张三",
    "email": "zhangsan@example.com",
    "content": "你好，这是一条测试留言！",
    "website": "https://example.com"
  }'
```

### 2. Feedback（反馈）

用于项目反馈、bug报告、功能建议等。

**必需字段：**
- `project_name` (string): 项目名称
- `title` (string): 反馈标题
- `content` (string): 反馈内容
- `category` (enum): 类别 - "bug" | "feature" | "improvement" | "question"

**可选字段：**
- `rating` (integer, 1-5): 评分
- `contact` (string): 联系方式

**示例：**
```bash
curl -X POST http://localhost:5001/api/v1/entries \
  -H "Content-Type: application/json" \
  -d '{
    "type": "feedback",
    "source": "homepage",
    "metadata": {
      "project_name": "个人主页",
      "title": "功能建议",
      "content": "希望能添加深色模式",
      "category": "feature",
      "rating": 5,
      "contact": "user@example.com"
    }
  }'
```

### 3. Notification（通知）

用于系统通知、公告等。

**必需字段：**
- `title` (string): 通知标题
- `content` (string): 通知内容
- `level` (enum): 级别 - "info" | "warning" | "error" | "success"

**可选字段：**
- `target_users` (array): 目标用户列表
- `expire_time` (datetime): 过期时间

**示例：**
```bash
curl -X POST http://localhost:5001/api/v1/entries \
  -H "Content-Type: application/json" \
  -d '{
    "type": "notification",
    "source": "system",
    "metadata": {
      "title": "系统维护通知",
      "content": "系统将于今晚22:00进行维护，预计持续2小时",
      "level": "warning",
      "target_users": ["admin", "user123"]
    }
  }'
```

---

## 📡 API端点

### 新版聚合API (v1)

#### 公开端点

**获取可见entries**
```bash
GET /api/v1/entries
参数：
  - type: 类型过滤 (message/feedback/notification)
  - source: 来源过滤
  - tags: 标签过滤
  - page: 页码 (默认: 1)
  - limit: 每页数量 (默认: 20)

示例：
curl "http://localhost:5001/api/v1/entries?type=feedback&source=homepage"
```

**创建entry**
```bash
POST /api/v1/entries
Body: {
  "type": "message",
  "source": "homepage",
  "metadata": {...}
}
```

**获取单个entry**
```bash
GET /api/v1/entries/{id}
```

#### 管理端点

**获取所有entries（包括隐藏的）**
```bash
GET /api/v1/admin/entries
参数：
  - type: 类型过滤
  - source: 来源过滤
  - is_show: 可见性过滤
  - is_delete: 删除状态过滤
  - page: 页码
  - limit: 每页数量
```

**更新entry状态**
```bash
PUT /api/v1/admin/entries/{id}/status
Body: {
  "is_show": true,
  "is_delete": false,
  "is_read": true
}
```

**获取统计信息**
```bash
GET /api/v1/admin/entries/stats
返回：
{
  "total": 100,
  "by_type": {
    "message": 60,
    "feedback": 30,
    "notification": 10
  },
  "by_source": {...},
  "by_status": {...}
}
```

**类型管理**
```bash
# 获取所有类型
GET /api/v1/admin/types

# 获取特定类型的schema
GET /api/v1/admin/types/{type}/schema

# 创建新类型
POST /api/v1/admin/types
```

### 向后兼容API

原有的`/messages`端点继续可用：

```bash
# 获取可见留言
GET /messages

# 创建留言
POST /messages

# 管理端点
GET /admin/messages
PUT /admin/messages/{id}/status
DELETE /admin/messages/{id}
POST /admin/messages/delete
```

---

## 🚀 快速开始

### 1. 安装

```bash
# 克隆仓库
git clone https://github.com/Chenmo1212/homepage_backend.git
cd homepage_backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置

创建 `config_development.py`:

```python
# MongoDB连接URI
MONGO_URI = "mongodb://localhost:27017/homepage"

# 或使用远程MongoDB
# MONGO_URI = "mongodb://username:password@host:port/database"
```

创建 `.env` (可选，用于企业微信通知):

```env
FLASK_ENV=development
CORPID=your-corporate-id
AGENTID=your-agent-id
CORPSECRET=your-corporate-secret
ADMINURL=https://your-admin-url
```

### 3. 运行

```bash
# 开发环境
export FLASK_ENV=development
flask run --port 5001

# 或使用脚本
chmod +x run_dev.sh
./run_dev.sh
```

### 4. 测试

```bash
# 测试根路径
curl http://localhost:5001/

# 创建测试数据
curl -X POST http://localhost:5001/messages \
  -H "Content-Type: application/json" \
  -d '{"name":"测试","email":"test@test.com","content":"Hello"}'

# 查看数据
curl http://localhost:5001/admin/messages
```

---

## ⚙️ 自定义Entry类型

### 添加新类型

编辑 `app/config/entry_types.json`:

```json
{
  "custom_type": {
    "name": "自定义类型",
    "description": "这是一个自定义类型",
    "schema": {
      "type": "object",
      "required": ["field1", "field2"],
      "properties": {
        "field1": {
          "type": "string",
          "minLength": 1
        },
        "field2": {
          "type": "integer",
          "minimum": 0
        }
      }
    },
    "notification": {
      "enabled": true,
      "template": "custom_template"
    }
  }
}
```

### 使用新类型

```bash
curl -X POST http://localhost:5001/api/v1/entries \
  -H "Content-Type: application/json" \
  -d '{
    "type": "custom_type",
    "source": "my_project",
    "metadata": {
      "field1": "value1",
      "field2": 42
    }
  }'
```

---

## 📱 企业微信通知

### 配置通知

1. 在 `.env` 中配置企业微信参数
2. 在 `app/config/entry_types.json` 中启用通知
3. 在 `app/notifications/notification_service.py` 中自定义模板

### 通知模板

系统支持多种通知模板：

- `wechat_message`: 留言通知
- `wechat_feedback`: 反馈通知
- `wechat_notification`: 系统通知

可以根据需要添加自定义模板。

---

## 🧪 测试

```bash
# 运行所有测试
pytest test_api.py -v

# 运行完整API测试
chmod +x test_api_complete.sh
./test_api_complete.sh
```

---

## 📚 文档

- **[ARCHITECTURE_DESIGN.md](ARCHITECTURE_DESIGN.md)** - 完整的架构设计文档
- **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** - 详细的实现计划和代码示例
- **[QUICK_START_GUIDE.md](QUICK_START_GUIDE.md)** - 快速开始指南和API使用示例
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - 部署和迁移指南
- **[MONGODB_SETUP.md](MONGODB_SETUP.md)** - MongoDB设置和问题诊断

---

## 🔧 常见问题

### Q: API返回中文乱码？
A: 已在 `app/__init__.py` 中配置 `JSON_AS_ASCII = False`，重启Flask即可。

### Q: 如何查看所有数据（包括隐藏的）？
A: 使用管理员端点：`GET /api/v1/admin/entries`

### Q: 如何按类型过滤？
A: 添加 `type` 参数：`GET /api/v1/entries?type=feedback`

### Q: 如何支持多个项目？
A: 使用 `source` 字段区分：`GET /api/v1/entries?source=project_a`

### Q: 数据迁移失败怎么办？
A: 检查 `backups/` 目录中的JSON备份文件，可以手动恢复。

---

## 🤝 贡献

欢迎贡献！请随时提交Pull Request或Issue。

### 贡献方向

- 添加新的entry类型
- 增强验证规则
- 性能优化
- 添加新的通知渠道
- UI改进
- 文档完善

---

## 📄 许可证

本项目采用 MIT 许可证。

---

## 🙏 致谢

- Flask框架
- MongoDB
- 企业微信API
- JSON Schema验证
- 所有贡献者

---

## 📞 联系方式

- 作品集：[https://www.chenmo1212.cn](https://www.chenmo1212.cn?f=github-backend)
- GitHub：[@Chenmo1212](https://github.com/Chenmo1212)
- Issues：[提交问题](https://github.com/Chenmo1212/homepage_backend/issues)

---

**⭐ 如果这个项目对你有帮助，请给个Star！**
