# check_env.py
"""检查 remove_clothes 环境是否就绪"""

import sys

def check():
    print("=" * 50)
    print("  环境检测")
    print("=" * 50)

    modules = [
        ("torch", "PyTorch"),
        ("diffusers", "Diffusers"),
        ("transformers", "Transformers"),
        ("accelerate", "Accelerate"),
        ("PIL", "Pillow"),
        ("cv2", "OpenCV"),
        ("controlnet_aux", "controlnet_aux"),
        ("ultralytics", "Ultralytics"),
    ]

    all_ok = True
    for mod, name in modules:
        try:
            __import__(mod)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ❌ {name}")
            all_ok = False

    if all_ok:
        print("\n✅ 环境完整，可以运行 remove_clothes / change_clothes")
    else:
        print("\n❌ 部分依赖缺失，请运行: pip install -r requirements.txt")

if __name__ == "__main__":
    check()