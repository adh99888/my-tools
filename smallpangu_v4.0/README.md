# 小盘古 4.0

轻量级、插件化的个人AI数字分身助手

## 🚀 项目理念

**轻装、轻灵、干净** - 构建一个真正模块化、可插拔的AI助手框架，让每个功能模块都像乐高积木一样可拆卸重组。

## ✨ 核心特性

### 🔌 插件化架构
- 所有功能均为独立插件，可热插拔、热重载
- 插件间零直接依赖，通过事件总线通信
- 支持运行时加载、卸载、替换插件

### 🧩 模块化设计
- 单一文件不超过500行，无"上帝类"
- 清晰的接口契约，实现可替换
- 配置驱动行为，避免硬编码

### ⚡ 轻量化核心
- 核心框架代码<1500行
- 启动时间<3秒，内存占用<200MB
- 无冗余依赖，按需加载

### 🛡️ 健壮性保障
- 插件沙箱隔离，错误不传播
- 自动回滚机制，更新安全可靠
- 完整的单元测试和集成测试

## 📁 项目结构

```
smallpangu_v4.0/
├── src/smallpangu/          # 核心框架
│   ├── app.py              # 应用主类
│   ├── core/               # 核心组件（事件总线、DI容器等）
│   ├── config/             # 配置管理
│   ├── plugins/            # 插件系统框架
│   ├── ui/                 # UI框架抽象
│   └── api/                # 公共API接口
├── plugins/                # 插件实现
│   ├── ai_providers/       # AI提供商插件
│   ├── ui_components/      # UI组件插件
│   ├── task_handlers/      # 任务处理器插件
│   └── tools/              # 工具插件
├── configs/                # 配置文件
├── tests/                  # 测试套件
└── docs/                   # 文档
```

## 🚀 快速开始

### 安装依赖
```bash
# 基础安装
pip install -e .

# 开发环境（包含测试和代码质量工具）
pip install -e ".[dev]"

# 完整功能（AI + UI）
pip install -e ".[dev,ai,ui]"
```

### 运行应用
```bash
python -m smallpangu
```

### 开发插件
```bash
# 创建新插件模板
python scripts/dev.py new-plugin --name my_plugin --type tool

# 运行测试
pytest tests/

# 代码质量检查
black src/
ruff check src/
mypy src/
```

## 🔌 插件开发

### 插件类型
1. **AI提供商插件** - 实现AI模型接口（DeepSeek、智谱等）
2. **UI组件插件** - 提供用户界面组件
3. **任务处理器插件** - 处理特定类型任务
4. **工具插件** - 提供实用工具功能

### 创建插件
```python
# plugins/tools/example_plugin.py
from smallpangu.plugins import Plugin

class ExamplePlugin(Plugin):
    name = "example_plugin"
    version = "1.0.0"
    
    def initialize(self, context):
        # 插件初始化逻辑
        context.event_bus.subscribe("chat.message", self.on_message)
    
    def on_message(self, message):
        # 处理事件
        print(f"收到消息: {message}")
```

## ⚙️ 配置系统

配置文件位于 `configs/` 目录，支持多环境：

```yaml
# configs/development.yaml
app:
  name: "小盘古"
  version: "4.0"
  log_level: "DEBUG"

plugins:
  enabled:
    - "ai_providers.deepseek"
    - "ui_components.development_ui"
    - "tools.token_counter"
```

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试  
pytest tests/integration/

# 生成测试覆盖率报告
pytest --cov=src/smallpangu tests/
```

## 📚 文档

- [架构设计](./docs/architecture.md) - 详细架构说明
- [插件开发指南](./docs/plugin_development.md) - 如何开发插件
- [API参考](./docs/api_reference.md) - 公共API接口文档

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 开发流程
1. Fork项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

### 代码规范
- 遵循PEP 8编码规范
- 使用类型提示（mypy验证）
- 编写单元测试（覆盖率>80%）
- 更新相关文档

## 📄 许可证

本项目采用 MIT 协议开源。详见 [LICENSE](LICENSE) 文件。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交Issue: [GitHub Issues](https://github.com/yourusername/smallpangu/issues)
- 邮件: smallpangu@example.com

---

**小盘古项目组** © 2026 - 追求极致的简洁与优雅