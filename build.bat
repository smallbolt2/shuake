@chcp 65001 >nul  &:: 强制切换为UTF-8编码
@echo off
setlocal

:: 关键修改：将 Python312 改为 Python39
set PYTHON_PATH=C:\Users\Administrator\AppData\Local\Programs\Python\Python39
set PROJECT_PATH=%~dp0

echo 正在安装依赖...
%PYTHON_PATH%\python.exe -m pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo [错误] 依赖安装失败！查看 error_log.txt
    echo %date% %time% 依赖安装失败 >> "%PROJECT_PATH%error_log.txt"
    goto :error
)

:: 关键修改：只记录错误信息（ERROR级别）[6,8](@ref)
echo 开始编译...
%PYTHON_PATH%\Scripts\pyinstaller "%PROJECT_PATH%build.spec" --clean --log-level ERROR 2> "%PROJECT_PATH%error_log.txt"
if errorlevel 1 (
    echo 错误：编译失败！查看 error_log.txt
    goto :error
)

echo 复制配置文件...
copy "%PROJECT_PATH%config.json" "%PROJECT_PATH%dist\smallbolt2\" >nul 2>&1
copy "%PROJECT_PATH%sample.config.json" "%PROJECT_PATH%dist\smallbolt2\" >nul 2>&1

echo 生成启动脚本...
(
    echo @echo off
    echo cd /d "%%~dp0smallbolt2"
    echo start "" smallbolt2.exe
) > "%PROJECT_PATH%dist\run.bat"

echo 编译成功！输出目录: %PROJECT_PATH%dist\smallbolt2
exit /b 0

:error
echo 编译过程中断！错误日志: %PROJECT_PATH%error_log.txt
endlocal