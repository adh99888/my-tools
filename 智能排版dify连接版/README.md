# AI文档智能排版系统 v2.0 - 智能排版 Dify 连接版

![版本](https://img.shields.io/badge/版本-v2.0-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![许可证](https://img.shields.io/badge/许可证-MIT-yellow)

> 多模型AI智能润色 + 动态模板编辑 + 一键导出 + Dify 智能连接

## 📋 项目简介

**AI文档智能排版系统**是一个基于多种国产AI模型的文档智能处理工具，能够自动润色、排版文档，并导出为专业Word格式。该系统特别集成了Dify平台，实现智能内容生成和文档处理的无缝连接。它如同一位"仙姑"般优雅地处理文档，让枯燥的排版工作变得智能高效。

### 🎯 项目特色
- **智能AI驱动**：集成DeepSeek、Kimi等6大国产AI模型
- **专业模板库**：7种预设模板，覆盖学术、政府、企业等场景
- **Dify集成**：无缝连接Dify工作流，实现智能内容生成
- **一键导出**：自动生成格式规范的Word文档
- **实时控制**：支持处理中断和状态重置
- **零基础友好**：图形化界面，操作简单直观

## ✨ 核心功能详解

### 🤖 多AI模型智能处理
- **支持6大国产AI模型**：DeepSeek、Kimi、通义千问、硅基流动、百川大模型、智谱GLM
- **智能模型选择**：根据文档长度自动推荐最适合的AI模型
- **API统一管理**：统一的API接口，支持热切换和配置更新

### 🎨 专业模板系统
- **7种内置模板**：
  - 学术论文模板（符合GB/T 7714规范）
  - 政府公文模板（符合GB/T 9704-2012标准）
  - 工作报告模板（企业级专业格式）
  - 标准文章模板（报刊杂志风格）
  - 书籍章节模板（适合长篇阅读）
  - 简洁现代模板（日常文档使用）
  - 灸道探微专用模板（中医养生领域专用）
- **自定义模板**：支持创建、编辑、删除自定义模板
- **实时预览**：模板效果实时预览和调整

### 📄 多格式文档支持
- **输入格式**：支持TXT纯文本、DOCX Word文档、PDF文档导入
- **智能识别**：自动识别文档结构和格式
- **内容提取**：准确提取文本内容，保持原有排版结构

### 🚀 AI智能排版
- **自动润色**：AI智能纠错、优化句子结构
- **标题识别**：自动识别和格式化文档标题层级
- **段落优化**：智能调整段落间距和排版格式
- **字符清理**：自动清理多余字符和格式标记

### 💾 一键专业导出
- **Word格式导出**：生成标准Word文档
- **样式应用**：自动应用选定模板的完整样式
- **格式规范**：符合专业文档排版标准

### ⚙️ 灵活配置系统
- **API密钥管理**：安全存储和管理多个AI模型的API密钥
- **模型参数配置**：可调整温度、最大token等参数
- **模板样式定制**：字体、颜色、间距等详细配置

### 🔄 实时控制功能
- **处理中断**：随时停止正在进行的AI处理
- **状态重置**：一键清空所有输入输出内容
- **进度监控**：实时显示处理进度和状态

## 📁 项目结构详解

以下是项目的完整目录结构，每个文件夹和文件的功能详细介绍，帮助零基础开发者理解项目架构：

### 🔧 根目录文件

| 文件名 | 功能描述 | 重要性 |
|--------|----------|--------|
| `__init__.py` | Python包初始化文件，定义包的基本信息 | 必须保留 |
| `main.py` | 应用程序主入口文件，负责程序启动和模块初始化 | **核心文件** |
| `requirements.txt` | Python依赖包列表，包含所有第三方库版本要求 | **必须安装** |
| `run.bat` | Windows启动脚本，自动设置环境并运行程序 | 便捷启动 |
| `test_day2.py` | 开发阶段的功能测试文件，验证核心功能 | 可选（测试用） |
| `app.log` | 程序运行日志文件，记录错误和调试信息 | 自动生成 |

### 📂 config/ 配置管理目录
负责整个应用程序的配置管理，是系统运行的基础：

| 文件名 | 功能描述 | 详细说明 |
|--------|----------|----------|
| `__init__.py` | 配置模块包初始化 | 标准Python包结构 |
| `config.ini` | 主配置文件（INI格式） | 包含API密钥、默认设置、系统参数 |
| `manager.py` | 配置管理器核心类 | 负责配置的加载、验证、保存和热更新 |
| `model_configs.json` | AI模型配置（JSON格式） | 定义各AI模型的API地址、参数、提供商信息 |
| `prompt_config.json` | 提示词配置（JSON格式） | 包含各模板的专用提示词和AI指令 |
| `__pycache__/` | Python字节码缓存 | 运行时自动生成，可删除 |

**核心功能**：
- 统一管理所有配置项
- 支持配置热加载，无需重启程序
- 自动验证配置格式和完整性
- 提供默认配置值

### 📂 core/ 核心业务逻辑目录
系统的核心功能实现，所有业务逻辑都在这里：

| 文件名 | 功能描述 | 详细说明 |
|--------|----------|----------|
| `__init__.py` | 核心模块包初始化 | - |
| `api_client.py` | 统一API客户端 | 与各种AI模型API通信，支持重试和错误处理 |
| `dify_client_final.py` | Dify客户端（最终版） | 专门处理Dify平台的API调用和数据解析 |
| `dify_client_simple.py` | Dify客户端（简化版） | **可删除**，与final版功能重复 |
| `document_processor.py` | 文档处理器 | 负责文档的加载、AI处理、格式转换 |
| `long_document_processor.py` | 长文档后处理器 | 优化排版结果，清理格式问题 |
| `model_manager.py` | 模型管理器 | 管理AI模型的配置、切换和推荐 |
| `prompt_manager.py` | 提示词管理器 | 管理AI提示词的加载和应用 |
| `template_manager.py` | 模板管理器 | 管理文档模板的加载和样式应用 |
| `__pycache__/` | 字节码缓存 | 自动生成，可删除 |

**核心功能**：
- AI模型通信和数据处理
- 文档格式转换和优化
- 模板样式应用
- Dify平台集成

### 📂 templates/ 模板目录
存放各种文档模板配置文件：

| 文件名 | 适用场景 | 特点 |
|--------|----------|------|
| `__init__.py` | - | 包初始化 |
| `academic.json` | 学术论文 | 符合GB/T 7714规范，严谨专业 |
| `article.json` | 标准文章 | 美观易读，适合出版 |
| `book_chapter.json` | 书籍章节 | 适合长篇阅读，舒适版式 |
| `official.json` | 政府公文 | 符合国家标准，正式规范 |
| `report.json` | 工作报告 | 企业级格式，层次清晰 |
| `simple.json` | 日常文档 | 简洁现代，快速使用 |
| `灸道探微专用.json` | 中医养生 | 专业领域定制格式 |

**模板配置包含**：
- 页面设置（边距、纸张大小）
- 字体样式（中英文字体、字号）
- 标题样式（各级标题格式）
- 段落格式（行距、缩进、对齐）

### 📂 ui/ 用户界面目录
基于Tkinter构建的图形用户界面：

| 文件名 | 功能描述 | 详细说明 |
|--------|----------|----------|
| `__init__.py` | UI模块包初始化 | - |
| `main_window.py` | 主窗口类 | 应用程序主界面，集成所有功能 |
| `__pycache__/` | 缓存目录 | 自动生成 |

#### 📂 ui/dialogs/ 对话框子目录
各种功能对话框：

| 文件名 | 功能描述 | 详细说明 |
|--------|----------|----------|
| `__init__.py` | 对话框模块初始化 | - |
| `base_dialog.py` | 对话框基类 | 提供通用对话框功能和样式 |
| `model_dialog.py` | 模型配置对话框 | AI模型的添加、编辑、删除界面 |
| `smart_generate_dialog_final.py` | 智能生成对话框（最终版） | Dify智能内容生成界面 |
| `smart_generate_dialog.py` | 智能生成对话框（简化版） | **可删除**，功能重复 |
| `template_dialog.py` | 模板编辑器对话框 | 模板的创建和编辑界面 |
| `__pycache__/` | 缓存目录 | 自动生成 |

#### 📂 ui/widgets/ 组件子目录
自定义UI组件：

| 文件名 | 功能描述 |
|--------|----------|
| `template_item_widget.py` | 模板选择项组件，支持预览和编辑 |

### 📂 utils/ 工具目录
提供基础工具功能：

| 文件名 | 功能描述 | 详细说明 |
|--------|----------|----------|
| `__init__.py` | 工具模块初始化 | - |
| `text_analyzer.py` | 文本分析工具 | 提供标题识别、文本清理、格式分析 |
| `title_extractor.py` | 标题提取器 | 基于置信度的复杂标题自动提取 |
| `__pycache__/` | 缓存目录 | 自动生成 |

## 🛠️ 环境配置

### 系统要求
- **操作系统**：Windows 10/11、macOS 10.15+、Ubuntu 18.04+
- **Python版本**：3.8.0 或更高版本（推荐3.9+）
- **内存**：至少4GB RAM（推荐8GB+）
- **磁盘空间**：至少500MB可用空间

### Python环境检查
```bash
# 检查Python版本
python --version
# 应该显示 Python 3.8.0 或更高

# 检查pip版本
pip --version
```

### 网络要求
- 稳定的互联网连接（用于AI API调用）
- 能够访问各大AI模型的API服务

## 📦 安装步骤

### 步骤1：获取项目
```bash
# 方法1：Git克隆（推荐）
git clone https://github.com/your-username/smart-typesetting-dify.git
cd smart-typesetting-dify

# 方法2：直接下载ZIP包并解压
# 从GitHub下载ZIP文件，解压到本地文件夹
```

### 步骤2：创建虚拟环境（推荐）
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 步骤3：安装依赖包
```bash
pip install -r requirements.txt
```

**依赖包说明**：
- `requests`：HTTP请求库，用于API调用
- `python-docx`：Word文档处理库
- `PyPDF2`：PDF文档读取库
- `configparser`：配置文件解析
- `urllib3`：网络连接库

### 步骤4：配置API密钥
1. **编辑配置文件**：
   ```bash
   # 打开config目录下的config.ini文件
   notepad config\config.ini
   ```

2. **配置DeepSeek API**（必需）：
   ```ini
   [API]
   key = sk-your-actual-api-key-here
   api_base = https://api.deepseek.com/v1
   model = deepseek-chat
   ```

3. **获取API密钥**：
   - 访问 [DeepSeek官网](https://platform.deepseek.com/)
   - 注册账号并获取API密钥
   - 密钥格式为 `sk-` 开头

### 步骤5：运行程序
```bash
# 方法1：使用启动脚本（Windows推荐）
run.bat

# 方法2：直接运行Python脚本
python main.py

# 方法3：激活虚拟环境后运行
venv\Scripts\activate  # Windows
python main.py
```

## 🎯 使用示例

### 示例1：处理学术论文
1. **启动程序**：双击 `run.bat` 或运行 `python main.py`
2. **输入文档**：点击"选择文档"按钮，选择你的论文TXT文件
3. **选择模板**：在模板下拉菜单中选择"学术论文"
4. **选择模型**：选择"DeepSeek Chat"模型
5. **开始处理**：点击"AI智能处理"按钮
6. **等待处理**：系统会显示处理进度
7. **导出结果**：点击"保存Word文档"，选择保存位置

### 示例2：创建自定义模板
1. **进入模板管理**：点击主界面上的"模板管理"标签页
2. **创建新模板**：点击"创建新模板"按钮
3. **设置基本信息**：
   - 模板名称：会议纪要
   - 描述：企业会议记录专用模板
4. **配置页面设置**：
   - 纸张大小：A4
   - 边距：上下左右各2.5cm
5. **设置字体样式**：
   - 正文字体：宋体 12号
   - 标题字体：黑体 16号
6. **保存模板**：点击"保存"按钮

### 示例3：配置新AI模型
1. **进入模型管理**：点击"模型管理"标签页
2. **添加新模型**：点击"配置模型"按钮
3. **填写模型信息**：
   - 模型ID：kimi
   - 模型名称：Kimi Chat
   - API地址：https://api.moonshot.cn/v1
   - 最大Token：65536
4. **配置API密钥**：在config.ini中添加对应配置
5. **测试连接**：点击"测试连接"验证配置

## 🔧 高级配置

### 多模型配置
在 `config/model_configs.json` 中添加更多模型：
```json
{
  "deepseek": {
    "name": "DeepSeek Chat",
    "api_base": "https://api.deepseek.com/v1",
    "model": "deepseek-chat",
    "max_tokens": 8192,
    "provider": "deepseek"
  },
  "kimi": {
    "name": "Kimi Chat",
    "api_base": "https://api.moonshot.cn/v1",
    "model": "kimi-chat",
    "max_tokens": 65536,
    "provider": "moonshot"
  }
}
```

### Dify集成配置
在 `config/config.ini` 中配置Dify：
```ini
[Dify]
api_key = your-dify-api-key
base_url = https://your-dify-instance.com/v1
response_mode = streaming
max_retries = 3
timeout = 60
```

## 🔍 故障排除

### 常见问题及解决方案

#### 问题1：程序无法启动
**现象**：双击run.bat无反应，或显示错误信息
**解决方案**：
1. 检查Python是否正确安装：`python --version`
2. 检查虚拟环境是否激活
3. 检查依赖包是否完整安装：`pip list`
4. 查看错误日志：`app.log`

#### 问题2：API调用失败
**现象**：处理文档时显示"API调用失败"
**解决方案**：
1. 检查API密钥是否正确配置
2. 检查网络连接是否正常
3. 确认API余额是否充足
4. 尝试切换其他AI模型
5. 查看日志文件获取详细错误信息

#### 问题3：文档处理失败
**现象**：无法读取或处理上传的文档
**解决方案**：
1. 检查文档格式（支持TXT、DOCX、PDF）
2. 确认文档大小不超过模型限制
3. 检查文档编码是否为UTF-8
4. 尝试转换为其他格式重新上传

#### 问题4：模板应用异常
**现象**：导出的Word文档样式不符合预期
**解决方案**：
1. 检查模板文件是否完整
2. 确认模板JSON格式正确
3. 尝试使用内置模板测试
4. 重启程序重新加载模板

### 日志文件位置
- **程序日志**：`app.log`（记录运行状态和错误）
- **安装日志**：`install.log`（仅Windows，记录安装过程）

### 获取帮助
1. 查看 `app.log` 文件获取详细错误信息
2. 在GitHub Issues中搜索相似问题
3. 提交新的Issue描述问题详情

## 📝 开发指南

### 项目架构说明
- **MVC模式**：Model（core/）-View（ui/）-Controller（main.py）
- **模块化设计**：各功能独立模块，便于维护和扩展
- **配置驱动**：通过配置文件灵活调整系统行为

### 添加新功能
1. **在core/中添加业务逻辑**
2. **在ui/中添加界面组件**
3. **更新配置管理**
4. **编写测试代码**

### 代码规范
- 使用UTF-8编码
- 遵循PEP 8代码风格
- 添加详细的文档字符串
- 异常处理要完善

## 📄 许可证

本项目采用 MIT 许可证 - 查看 LICENSE 文件了解详情。

## 🤝 贡献指南

我们欢迎各种形式的贡献！

### 贡献流程
1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/新功能`
3. 提交更改：`git commit -m '添加新功能'`
4. 推送到分支：`git push origin feature/新功能`
5. 提交 Pull Request

### 贡献类型
- 🐛 提交Bug修复
- ✨ 添加新功能
- 📚 改进文档
- 🎨 优化界面
- 🔧 性能优化

## 📞 支持与反馈

- **问题反馈**：在 [GitHub Issues](https://github.com/your-username/smart-typesetting-dify/issues) 中提交
- **功能建议**：通过 Issues 提出新功能需求
- **文档问题**：欢迎提交文档改进建议

## 🚀 未来规划

- [ ] 批量文档处理功能
- [ ] 历史记录管理
- [ ] PDF直接导出
- [ ] 插件系统支持
- [ ] 云端同步功能
- [ ] 多语言界面支持
- [ ] 移动端应用开发

---

<div align="center">
  <sub>❤️ 如果这个项目对你有帮助，请点个Star支持！</sub>
  <br>
  <sub>📧 联系我们：your-email@example.com</sub>
</div>