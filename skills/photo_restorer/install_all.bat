@echo off
chcp 65001 >nul
echo ========================================
echo 📦 photo_restorer 依赖一键安装
echo Python 3.9 版本
echo ========================================
echo.

echo 1. 安装 PyTorch (CPU 版本)...
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
echo.

echo 2. 安装基础依赖...
pip install opencv-python pillow addict future lmdb scikit-image
echo.

echo 3. 安装 basicsr...
pip install basicsr==1.4.2 --no-build-isolation --no-deps
echo.

echo 4. 修复 basicsr 兼容性...
python -c "from pathlib import Path; import site; [open(p := Path(path) / 'basicsr' / 'data' / 'degradations.py', 'w', encoding='utf-8').write(open(p, 'r', encoding='utf-8').read().replace('functional_tensor', 'functional')) for path in site.getsitepackages() if (Path(path) / 'basicsr' / 'data' / 'degradations.py').exists()]"
echo.

echo 5. 安装 facexlib...
pip install facexlib
echo.

echo 6. 安装 gfpgan...
pip install --no-deps git+https://github.com/TencentARC/GFPGAN.git
echo.

echo 7. 安装 realesrgan...
pip install --no-deps git+https://github.com/xinntao/Real-ESRGAN.git
echo.

echo 8. 验证所有依赖...
python -c "import basicsr, realesrgan, gfpgan, facexlib, cv2, torch; print('✅ 所有依赖已安装！')"
echo.

echo ========================================
echo ✅ 安装完成！
echo ========================================
pause