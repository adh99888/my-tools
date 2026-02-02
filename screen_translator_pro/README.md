# 屏幕翻译助手增强版

一个针对Windows环境优化的屏幕翻译工具，专注于解决旧版本的问题并优化用户体验。支持智能区域捕获、混合OCR识别和多模型翻译路由。

## 主要特性

- **智能屏幕捕获**: 支持变化检测，避免重复处理静态区域
- **混合OCR引擎**: Tesseract（英文优势）+ EasyOCR（中文优势）结合
- **视觉OCR支持**: 集成通义千问和DeepSeek视觉模型，识别准确率更高
- **多模型翻译**: 支持Kimi、DeepSeek、通义千问、智谱GLM、硅基流动等模型
- **智能侧边栏**: 自适应布局，解决原版侧边栏狭小问题
- **Windows优化**: 针对Windows系统特性深度优化
- **简化配置**: 扁平化配置结构，易于理解和修改

## 安装步骤

### 方式一：使用安装脚本（推荐）

1. 下载或克隆本仓库
2. 双击运行 `install.cmd`
3. 按照提示完成安装

### 方式二：手动安装

1. 确保已安装 Python 3.8+
2. 安装依赖包：
   ```bash
   pip install -r requirements.txt
   ```
3. （可选）安装Tesseract OCR以获得更好的OCR效果：
   - 下载地址：https://github.com/UB-Mannheim/tesseract/wiki
   - 安装后将安装路径添加到系统PATH环境变量

## 配置说明

首次运行会自动创建 `config.yaml` 配置文件。需要修改以下部分：

### API密钥配置

在 `config.yaml` 文件的 `apis` 部分配置至少一个翻译API密钥：

```yaml
apis:
  kimi:
    api_key: "您的Kimi API密钥"
    model: "kimi-k2-turbo-preview"
    base_url: "https://api.moonshot.cn/v1"
  
  deepseek:
    api_key: "您的DeepSeek API密钥"
    model: "deepseek-chat"
    base_url: "https://api.deepseek.com/v1"
  
  # ... 其他API配置
```

### 基本配置

- `capture.mode`: 捕获模式（smart/fixed/manual）
- `translation.primary`: 首选翻译模型
- `display.width`: 侧边栏宽度模式（adaptive/fixed）
- `ocr.primary`: OCR引擎类型（hybrid/tesseract_only/vision）
- `ocr.vision.provider`: 视觉OCR提供者（qwen/deepseek）

### 视觉OCR配置（可选）

如需使用视觉OCR（推荐），在 `config.yaml` 中添加：

```yaml
ocr:
  primary: vision  # 启用视觉OCR
  vision:
    enabled: true
    provider: qwen  # 或 deepseek
    model: qwen-vl-max  # 视觉模型名称
    enable_translation: true
    max_image_size: 2048
```

视觉OCR使用大模型进行OCR识别，准确率更高，特别适合复杂布局和多语言混合文本。

## 使用方法

### 启动程序
```bash
python main.py
```

### 默认快捷键

- `Ctrl+Shift+T`: 截图翻译
- `Alt+T`: 显示/隐藏侧边栏
- `Ctrl+P`: 暂停/继续捕获
- `Ctrl+L`: 清除翻译历史
- `Ctrl+,`: 打开设置

### 工作流程

1. 启动程序后，侧边栏会显示在屏幕右侧
2. 使用 `Ctrl+Shift+T` 捕获屏幕区域
3. 程序自动进行OCR识别和翻译
4. 翻译结果显示在侧边栏中
5. 可点击侧边栏中的条目查看详细内容

## 项目结构

```
screen_translator_pro/
├── engines/                    # 核心引擎
│   ├── capture/               # 屏幕捕获
│   ├── ocr/                   # OCR识别（传统+视觉）
│   └── translation/           # 翻译模块
├── ui/                        # 用户界面
├── utils/                     # 工具模块
├── config/                    # 配置目录
├── data/                      # 数据目录（缓存等）
├── debug_images/              # 调试用图片目录
├── config.yaml               # 主配置文件
├── main.py                   # 主程序入口
├── config_wizard.py          # 配置向导
├── requirements.txt          # 依赖包列表
├── install.cmd              # Windows安装脚本
├── README.md                # 项目说明
├── VISION_OCR_GUIDE.md      # 视觉OCR使用指南
├── VISION_OCR_SUMMARY.md    # 视觉OCR完成总结
└── CLEANUP_SUMMARY.md       # 清理总结
```

## 故障排除

### 常见问题

1. **导入错误**：确保所有依赖已安装 `pip install -r requirements.txt`
2. **OCR识别率低**：
   - 传统OCR：安装Tesseract OCR并确保路径正确
   - 视觉OCR：检查API密钥和余额，确保网络连接正常
3. **翻译失败**：检查API密钥是否有效，网络是否连通
4. **程序崩溃**：查看 `logs/app.log` 日志文件
5. **视觉OCR响应慢**：正常现象，视觉OCR需要1-3秒处理时间

### 性能优化建议

1. **对于传统OCR**：
   - 确保Tesseract语言包已安装
   - 调整 `ocr.preprocess` 参数

2. **对于视觉OCR**：
   - 减小捕获区域以提高速度
   - 调整 `ocr.vision.max_image_size` 参数
   - 选择响应更快的提供者（DeepSeek通常比通义千问快）

3. **通用优化**：
   - 使用 `Ctrl+P` 暂停不需要时的捕获
   - 定期清理 `data/translation_cache.db` 缓存

## 开发说明

### 添加新的翻译模型

1. 在 `engines/translation/apis/` 目录下创建新的翻译器类
2. 继承 `BaseTranslator` 基类
3. 实现 `initialize()` 和 `translate()` 方法
4. 在 `model_router.py` 中注册新模型

### 添加新的视觉OCR提供者

1. 在 `engines/ocr/` 目录下创建新的视觉OCR类
2. 继承 `VisionOCREngine` 基类
3. 实现 `initialize()`、`_call_vision_api()` 和 `_parse_response()` 方法
4. 在 `main.py` 中添加初始化逻辑
5. 在 `config.yaml` 中添加配置选项

### 修改界面样式

界面样式在 `ui/main_window.py` 和 `ui/smart_sidebar.py` 中定义，支持深色/浅色主题。

## 许可证

本项目仅供个人学习使用。

## 更新日志

### v1.1.0 (当前版本)
- ✅ 新增视觉OCR支持（通义千问 qwen-vl-max）
- ✅ 新增DeepSeek视觉OCR（通过SiliconFlow）
- ✅ 传统OCR与视觉OCR无缝切换
- ✅ 视觉OCR配置指南和文档
- ✅ 项目结构清理，减少90%冗余文件

### v1.0.0 (初始版本)
- 智能屏幕捕获引擎
- 混合OCR识别系统（Tesseract + EasyOCR）
- 多模型翻译路由（Kimi、DeepSeek、通义千问、GLM等）
- 自适应侧边栏界面
- Windows专用优化工具