@echo off
echo ============================================
echo   Remove Clothes / Change Clothes 依赖安装
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
echo [4/6] 安装 controlnet-aux...
pip install controlnet-aux

echo.
echo [5/6] 安装 YOLO...
pip install ultralytics

echo.
echo [6/6] 安装 Pillow 和 numpy...
pip install Pillow numpy

echo.
echo ============================================
echo   ✅ 安装完成！
echo ============================================
echo.
echo 支持的 ControlNet 类型:
echo   - canny    边缘检测
echo   - hed      软边缘检测
echo   - lineart  线稿提取
echo   - depth    深度图
echo   - normal   法线图
echo   - mlsd     直线检测
echo   - openpose 人体姿态（推荐换衣服）
echo   - openpose_full 完整姿态
echo.
echo 模型将在首次运行时自动下载。
pause