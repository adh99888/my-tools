# 视觉OCR集成指南

## 概述

屏幕翻译助手增强版现已支持视觉OCR功能，使用大模型视觉能力进行OCR识别和翻译，提供比传统OCR更高的准确率。

## 支持的视觉OCR提供者

### 1. 通义千问 (Qwen)
- **模型**: `qwen-vl-max`
- **优势**: 中文识别和翻译效果优秀
- **成本**: 按API调用次数计费
- **官网**: https://dashscope.aliyun.com

### 2. DeepSeek (通过SiliconFlow)
- **模型**: `deepseek-ai/DeepSeek-OCR`
- **优势**: 英文和技术文本识别效果好
- **成本**: 按API调用次数计费
- **官网**: https://siliconflow.cn

## 配置方法

### 启用视觉OCR

编辑 `config.yaml` 文件：

```yaml
ocr:
  primary: vision  # 改为 vision 启用视觉OCR
  languages: ['en']  # 视觉OCR自动检测语言，此项可忽略
  preprocess: false  # 视觉OCR不需要预处理
  
  vision:
    enabled: true  # 启用视觉OCR
    provider: qwen  # 选择提供者: qwen 或 deepseek
    model: qwen-vl-max  # 视觉模型名称
    enable_translation: true  # 是否同时进行翻译
    max_image_size: 2048  # 最大图像尺寸
```

### API密钥配置

确保已配置相应的API密钥：

```yaml
apis:
  qwen:
    api_key: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # 通义千问API密钥
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    model: qwen-max  # 文本翻译模型
  
  siliconflow:
    api_key: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # SiliconFlow API密钥（用于DeepSeek）
    base_url: https://api.siliconflow.cn/v1
    model: deepseek-ai/DeepSeek-V3.1  # 文本翻译模型
```

## 使用指南

### 1. 启动应用

```bash
cd screen_translator_pro
python main.py
```

### 2. 捕获屏幕文本

- 按 `Ctrl+Shift+T` 激活捕获模式
- 用鼠标选择要翻译的文本区域
- 释放鼠标，自动进行OCR识别和翻译

### 3. 查看结果

翻译结果会显示在侧边栏中，包含：
- 原文识别结果
- 翻译后的文本
- 识别置信度

## 性能对比

### 传统OCR (Tesseract/EasyOCR)
- ✅ 本地运行，无需网络
- ✅ 免费使用
- ❌ 对复杂布局识别率低
- ❌ 多语言混合文本效果差
- ❌ 需要安装语言包

### 视觉OCR (大模型)
- ✅ 识别准确率极高
- ✅ 理解上下文和布局
- ✅ 多语言混合文本效果好
- ✅ 自动翻译一步到位
- ❌ 需要网络连接
- ❌ API调用有成本
- ❌ 响应速度较慢 (~1-3秒)

## 成本估算

### 通义千问 qwen-vl-max
- 图像识别: 约 0.05-0.1元/次
- 翻译: 约 0.01-0.02元/次
- **合计**: 约 0.06-0.12元/次

### DeepSeek-OCR (通过SiliconFlow)
- 图像识别: 约 0.03-0.05元/次
- 翻译: 约 0.01-0.02元/次
- **合计**: 约 0.04-0.07元/次

## 最佳实践

### 推荐使用场景

1. **高价值内容**: 翻译专业文档、技术资料
2. **复杂布局**: 表格、多栏文本、图文混排
3. **多语言混合**: 中英文混合的文本
4. **低质量图像**: 模糊、倾斜、背景复杂的截图

### 不适用场景

1. **频繁捕获**: 需要连续快速捕获的场景
2. **隐私敏感**: 涉及敏感信息的屏幕内容
3. **离线环境**: 无网络连接的情况

### 成本优化建议

1. **缓存机制**: 相同内容只识别一次
2. **区域选择**: 精确选择需要翻译的区域，避免无关内容
3. **混合模式**: 简单文本用传统OCR，复杂文本用视觉OCR

## 故障排除

### 问题1: API调用失败

**症状**: `Error code: 400` 或 `Error code: 401`

**解决**:
- 检查API密钥是否正确
- 检查API余额是否充足
- 检查模型名称是否正确

### 问题2: 识别结果为空

**症状**: 返回空文本或乱码

**解决**:
- 检查图像是否清晰
- 尝试调整 `max_image_size` 参数
- 检查提示词(prompt)是否合适

### 问题3: 响应速度慢

**症状**: 识别需要3秒以上

**解决**:
- 检查网络连接
- 减小捕获区域
- 降低 `max_image_size` 参数

## 高级配置

### 自定义提示词

可以在 `vision_ocr.py` 中修改 `_build_ocr_prompt` 方法，自定义识别和翻译的指令。

### 调整置信度阈值

在 `_extract_text_blocks` 方法中调整 `confidence` 参数：

```python
text_block = VisionTextBlock(
    text=line,
    confidence=0.95,  # 调整置信度
    bbox=(0, i*20, 200, (i+1)*20),
    language="auto"
)
```

### 添加新的视觉OCR提供者

1. 继承 `VisionOCREngine` 基类
2. 实现 `initialize()` 方法
3. 实现 `_call_vision_api()` 方法
4. 实现 `_parse_response()` 方法
5. 在 `main.py` 中添加初始化逻辑

## 版本历史

- **v1.0**: 初始版本，支持通义千问视觉OCR
- **v1.1**: 添加DeepSeek视觉OCR支持
- **v1.2**: 优化响应解析，提高准确率

## 支持与反馈

如有问题或建议，请提交Issue或联系开发团队。