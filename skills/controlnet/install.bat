@echo off
REM ControlNet 技能依赖安装脚本 (Windows)
REM v2.0.0 - 新增 gradio 支持

echo ============================================
echo   ControlNet 技能依赖安装 v2.0.0
echo ============================================
echo.

echo [1/6] 安装 PyTorch...
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

echo.
echo [2/6] 安装 diffusers 和相关库...
pip install diffusers transformers accelerate

echo.
echo [3/6] 安装 OpenCV...
pip install opencv-python-headless

echo.
echo [4/6] 安装 controlnet_aux...
pip install controlnet-aux

echo.
echo [5/6] 安装 Pillow 和 numpy...
pip install Pillow numpy

echo.
echo [6/6] 安装 Gradio (Web UI) ⭐ 新增...
pip install gradio

echo.
echo ============================================
echo   ✅ 安装完成！
echo ============================================
echo.
echo 支持的 ControlNet 类型 (v2.0.0):
echo   - canny       边缘检测
echo   - hed         软边缘检测
echo   - lineart     线稿提取
echo   - depth       深度图
echo   - normal      法线图
echo   - mlsd        直线检测
echo   - openpose    姿态检测
echo   - openpose_full 完整姿态
echo   - seg         语义分割 ⭐ 新增
echo   - scribble    涂鸦控制 ⭐ 新增
echo.
echo 验证安装:
echo   python skills/controlnet/test_controlnet.py
echo.
echo 启动 Gradio UI:
echo   python skills/controlnet/skill.py --action gui
pause