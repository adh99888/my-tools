@echo off
chcp 65001 >nul
echo ========================================
echo DeepSeek OCR翻译器启动脚本
echo ========================================
echo.

REM 检查是否在正确的虚拟环境中
python --version
echo.

REM 检查venv313虚拟环境是否存在
if exist "d:\deepseek ocr - 副本\DeepSeek-OCR\venv313\Scripts\activate.bat" (
    echo 检测到DeepSeek OCR虚拟环境 (venv313)
    echo 正在激活虚拟环境...
    call "d:\deepseek ocr - 副本\DeepSeek-OCR\venv313\Scripts\activate.bat"
    
    echo.
    echo 虚拟环境已激活，Python版本:
    python --version
    echo.
    
    echo 启动屏幕翻译助手增强版...
    echo ========================================
    python main.py
) else (
    echo 错误: 未找到DeepSeek OCR虚拟环境
    echo.
    echo 请确保以下路径存在:
    echo d:\deepseek ocr - 副本\DeepSeek-OCR\venv313
    echo.
    echo 如果虚拟环境不存在，请运行:
    echo cd "d:\deepseek ocr - 副本\DeepSeek-OCR"
    echo python -m venv venv313
    echo venv313\Scripts\activate
    echo pip install torch==2.7.1+cu118 --index-url https://download.pytorch.org/whl/cu118
    echo pip install transformers==4.46.3
    echo.
    pause
)