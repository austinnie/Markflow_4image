@echo off
REM ControlNet 技能依赖安装脚本 (Windows)
REM 只安装必要的依赖，不安装 mediapipe

echo ============================================
echo   ControlNet 技能依赖安装
echo ============================================
echo.

echo [1/5] 安装 PyTorch...
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

echo.
echo [2/5] 安装 diffusers 和相关库...
pip install diffusers transformers accelerate

echo.
echo [3/5] 安装 OpenCV...
pip install opencv-python-headless

echo.
echo [4/5] 安装 controlnet_aux...
pip install controlnet-aux

echo.
echo [5/5] 安装 Pillow 和 numpy...
pip install Pillow numpy

echo.
echo ============================================
echo   ✅ 安装完成！
echo ============================================
echo.
echo 支持的 ControlNet 类型（无需 mediapipe）:
echo   - canny    边缘检测
echo   - hed      软边缘检测
echo   - lineart  线稿提取
echo   - depth    深度图
echo   - normal   法线图
echo   - mlsd     直线检测
echo.
echo 验证安装:
echo   python skills/controlnet/test_controlnet.py
pause