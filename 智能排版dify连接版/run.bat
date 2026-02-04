@echo off
chcp 65001 > nul
title AI文档智能排版系统 v2.0 - 启动程序
cls

echo ============================================
echo   AI文档智能排版系统 v2.0 - 启动程序
echo ============================================
echo.

:: 保存当前目录
set "CURRENT_DIR=%CD%"

:: 检查是否在项目根目录运行
if not exist "main.py" (
    echo ⚠️  警告: 未找到 main.py
    echo 请确保在项目根目录运行此脚本
    echo 当前目录: %CURRENT_DIR%
    echo.
    pause
    exit /b 1
)

echo [1/4] 检查Python环境...
where python >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Python
    echo 请先安装Python 3.8或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

python --version
if errorlevel 1 (
    echo ❌ Python版本检测失败
    pause
    exit /b 1
)

python -c "import sys; sys.exit(0) if sys.version_info >= (3, 8) else sys.exit(1)" >nul 2>&1
if errorlevel 1 (
    echo ❌ 需要Python 3.8或更高版本
    echo 当前版本可能过低
    pause
    exit /b 1
)
echo ✅ Python环境检查通过

echo.

echo [2/4] 检查并安装依赖包...
if not exist "requirements.txt" (
    echo ❌ 未找到requirements.txt文件
    echo 正在创建默认requirements.txt...
    (
echo requests>=2.28.0
echo python-docx>=0.8.11
echo PyPDF2>=3.0.0
echo urllib3>=1.26.0
    ) > requirements.txt
    echo ✅ 已创建requirements.txt
)

echo 正在检查/安装依赖包，请稍候...
pip install --upgrade pip >nul 2>&1
if errorlevel 1 (
    echo ⚠️  pip升级失败，继续尝试安装依赖...
)

pip install -r requirements.txt 2>nul 1>nul
if errorlevel 1 (
    echo ❌ 依赖包安装失败
    echo 正在尝试逐个安装...
    
    for /f "tokens=1,2 delims==" %%i in (requirements.txt) do (
        echo 正在安装: %%i
        pip install %%i >nul 2>&1
        if errorlevel 1 (
            echo ❌ 安装失败: %%i
        ) else (
            echo ✅ 安装成功: %%i
        )
    )
    
    echo.
    echo ⚠️  部分依赖可能安装失败，但尝试继续运行...
    timeout /t 2 >nul
) else (
    echo ✅ 依赖包安装/检查完成
)

echo.

echo [3/4] 检查配置文件...
if not exist "config\" (
    md config
    echo ✅ 已创建config目录
)

if not exist "config\config.ini" (
    echo ⚠️  配置文件不存在
    echo 正在创建config\config.ini...
    (
echo [API]
echo key = sk-your-deepseek-api-key-here
echo api_base = https://api.deepseek.com/v1
echo model = deepseek-chat
echo.
echo [Settings]
echo default_mode = polish
echo keep_original_title = yes
echo auto_correct = yes
echo max_retries = 3
echo.
echo [MultiModel]
echo enable_multi_model = yes
echo default_model = deepseek
    ) > config\config.ini
    echo ⚠️  请编辑config\config.ini文件，填入正确的API密钥
    timeout /t 3 >nul
)

if not exist "config\model_configs.json" (
    echo ⚠️  模型配置文件不存在
    echo 正在创建config\model_configs.json...
    (
echo {
echo   "deepseek": {
echo     "name": "DeepSeek Chat",
echo     "api_base": "https://api.deepseek.com/v1",
echo     "model": "deepseek-chat",
echo     "max_tokens": 8192,
echo     "provider": "deepseek"
echo   }
echo }
    ) > config\model_configs.json
)

if not exist "templates\" (
    md templates
    echo ✅ 已创建templates目录
    echo ⚠️  模板目录为空，程序将自动创建默认模板
)

echo ✅ 配置文件检查完成

echo.

echo [4/4] 启动程序...
echo ============================================
echo   正在启动AI文档智能排版系统 v2.0...
echo   版本: TASK-002 界面控制增强与排版优化
echo ============================================
echo.

:: 设置PYTHONPATH
set "PYTHONPATH=%CURRENT_DIR%"

:: 运行主程序
python main.py

if errorlevel 1 (
    echo.
    echo ❌ 程序启动失败！
    echo.
    echo 可能的原因：
    echo 1. Python版本不是3.8+
    echo 2. 依赖包安装不完整
    echo 3. API密钥未配置（请编辑config\config.ini）
    echo 4. 程序代码有错误
    echo.
    echo 调试方法：
    echo 1. 手动运行：python main.py
    echo 2. 检查app.log文件
    echo 3. 确保在项目根目录运行
    echo.
    echo 按任意键退出...
    pause >nul
    exit /b 1
)

echo.
echo ============================================
echo   程序已正常退出
echo ============================================
echo 按任意键关闭窗口...
pause >nul