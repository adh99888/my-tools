@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   屏幕翻译助手增强版 - 安装程序
echo ========================================
echo.

REM 检查Python是否安装
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未找到Python，请先安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    echo 安装时请勾选"Add Python to PATH"
    pause
    exit /b 1
)

REM 检查pip是否安装
where pip >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未找到pip，请确保Python安装正确
    pause
    exit /b 1
)

REM 显示Python版本
python --version

echo.
echo 步骤1: 安装依赖包...
echo.
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [警告] 依赖安装过程中可能出现问题
    echo 请手动运行: pip install -r requirements.txt
)

echo.
echo 步骤2: 检查Tesseract OCR...
echo.
where tesseract >nul 2>nul
if %errorlevel% neq 0 (
    echo [提示] 未找到Tesseract OCR，建议安装以获得最佳OCR效果
    echo.
    echo Tesseract Windows安装方法:
    echo 1. 下载地址: https://github.com/UB-Mannheim/tesseract/wiki
    echo 2. 下载最新版tesseract-ocr-w64-setup-*.exe
    echo 3. 运行安装程序，记录安装路径（如C:\Program Files\Tesseract-OCR）
    echo 4. 将安装路径添加到系统PATH环境变量
    echo.
)

echo.
echo 步骤3: 检查配置文件...
echo.
if not exist config.yaml (
    echo [提示] 配置文件不存在，将运行程序自动生成默认配置
)

echo.
echo 步骤4: 创建桌面快捷方式（可选）...
echo.
set "script_path=%~dp0main.py"
set "desktop=%USERPROFILE%\Desktop\屏幕翻译助手.lnk"

echo 是否创建桌面快捷方式? (Y/N)
set /p create_shortcut=
if /i "%create_shortcut%"=="y" (
    echo 创建桌面快捷方式...
    REM 创建批处理文件作为启动器
    echo @echo off > "%USERPROFILE%\Desktop\启动屏幕翻译助手.bat"
    echo chcp 65001 >> "%USERPROFILE%\Desktop\启动屏幕翻译助手.bat"
    echo echo 正在启动屏幕翻译助手... >> "%USERPROFILE%\Desktop\启动屏幕翻译助手.bat"
    echo cd /d "%~dp0" >> "%USERPROFILE%\Desktop\启动屏幕翻译助手.bat"
    echo python main.py >> "%USERPROFILE%\Desktop\启动屏幕翻译助手.bat"
    echo pause >> "%USERPROFILE%\Desktop\启动屏幕翻译助手.bat"
    echo.
    echo 已创建桌面快捷方式: %USERPROFILE%\Desktop\启动屏幕翻译助手.bat
)

echo.
echo 步骤5: 测试运行...
echo.
echo 是否现在运行程序进行测试? (Y/N)
set /p run_test=
if /i "%run_test%"=="y" (
    echo 启动程序...
    python main.py
) else (
    echo.
    echo 安装完成!
    echo 手动启动命令: python main.py
)

echo.
echo ========================================
echo   安装完成!
echo ========================================
echo.
echo 使用说明:
echo 1. 首次运行会自动创建配置文件 config.yaml
echo 2. 请根据需要修改config.yaml中的API密钥
echo 3. 默认快捷键: Ctrl+Shift+T (截图翻译)
echo 4. 默认快捷键: Alt+T (显示/隐藏侧边栏)
echo.
echo 注意事项:
echo 1. 需要有效的API密钥才能使用翻译功能
echo 2. 建议安装Tesseract OCR提升识别准确率
echo 3. 如有问题请检查logs/app.log日志文件
echo.
pause