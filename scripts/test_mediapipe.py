#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试新版 MediaPipe API 是否正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def test_mediapipe_import():
    """测试 MediaPipe 导入"""
    print("=" * 60)
    print("测试 1: 导入 mediapipe")
    print("=" * 60)
    
    try:
        import mediapipe as mp
        print(f"  ✅ mediapipe 版本: {mp.__version__}")
        print(f"  ✅ 可用模块: {[x for x in dir(mp) if not x.startswith('_')][:10]}...")
    except ImportError as e:
        print(f"  ❌ mediapipe 未安装: {e}")
        return False
    return True


def test_new_api():
    """测试新版 API"""
    print("\n" + "=" * 60)
    print("测试 2: 新版 mediapipe.tasks API")
    print("=" * 60)
    
    try:
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
        print("  ✅ mediapipe.tasks.python 导入成功")
    except ImportError as e:
        print(f"  ❌ 新版 API 导入失败: {e}")
        print("  💡 可能需要安装: pip install mediapipe")
        return False
    return True


def test_pose_landmarker():
    """测试姿态检测器"""
    print("\n" + "=" * 60)
    print("测试 3: 创建 PoseLandmarker")
    print("=" * 60)
    
    try:
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
        
        # 模型路径
        model_path = project_root / "skills/expand_to_full_body/pose_landmarker_heavy.task"
        
        if not model_path.exists():
            print(f"  ❌ 模型文件不存在: {model_path}")
            print("  💡 下载命令:")
            print(f"     python -c \"import urllib.request; urllib.request.urlretrieve('https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task', '{model_path}')\"")
            return False
        
        print(f"  ✅ 模型文件存在: {model_path}")
        
        # 创建检测器
        pose_options = vision.PoseLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
        )
        
        detector = vision.PoseLandmarker.create_from_options(pose_options)
        print("  ✅ PoseLandmarker 创建成功")
        return True
        
    except Exception as e:
        print(f"  ❌ 创建失败: {e}")
        return False


def test_detect_image():
    """测试实际检测图片"""
    print("\n" + "=" * 60)
    print("测试 4: 检测图片")
    print("=" * 60)
    
    try:
        import mediapipe as mp
        import numpy as np
        from PIL import Image
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
        
        # 找一张测试图片
        test_image = project_root / "input/girl_01.jpg"
        if not test_image.exists():
            # 尝试其他路径
            test_image = project_root / "input/girl.jpg"
        if not test_image.exists():
            print(f"  ⚠️ 找不到测试图片，跳过检测测试")
            return True
        
        print(f"  📸 测试图片: {test_image}")
        
        # 创建检测器
        model_path = project_root / "skills/expand_to_full_body/pose_landmarker_heavy.task"
        pose_options = vision.PoseLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
        )
        detector = vision.PoseLandmarker.create_from_options(pose_options)
        
        # 读取图片
        image = Image.open(test_image).convert("RGB")
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.array(image))
        
        # 检测
        result = detector.detect(mp_image)
        
        if result and result.pose_landmarks:
            landmarks = result.pose_landmarks[0]
            print(f"  ✅ 检测成功! 找到 {len(landmarks)} 个关键点")
            # 打印前几个关键点
            for i in range(min(5, len(landmarks))):
                print(f"     关键点 {i}: ({landmarks[i].x:.3f}, {landmarks[i].y:.3f}, {landmarks[i].z:.3f})")
            return True
        else:
            print("  ⚠️ 未检测到人物姿态")
            return True
            
    except Exception as e:
        print(f"  ❌ 检测失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_expand_to_full_body():
    """测试 expand_to_full_body 技能"""
    print("\n" + "=" * 60)
    print("测试 5: expand_to_full_body 技能")
    print("=" * 60)
    
    try:
        from skills.expand_to_full_body.skill import ExpandToFullBody
        
        skill = ExpandToFullBody(config={'device': 'cpu'})
        print("  ✅ ExpandToFullBody 初始化成功")
        
        # 找测试图片
        test_image = project_root / "input/girl_01.jpg"
        if not test_image.exists():
            test_image = project_root / "input/girl.jpg"
        if not test_image.exists():
            print("  ⚠️ 找不到测试图片，跳过执行测试")
            return True
        
        # 执行
        result = skill.execute(
            image_path=str(test_image),
            output_path=str(project_root / "output/test_mediapipe.png"),
            prompt="a beautiful woman standing",
        )
        
        if result.get('status') == 'success':
            print(f"  ✅ 执行成功!")
            print(f"     输出: {result.get('output_path')}")
            return True
        else:
            print(f"  ❌ 执行失败: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "=" * 60)
    print("🧪 MediaPipe 新版 API 测试")
    print("=" * 60)
    
    results = []
    
    # 运行所有测试
    results.append(("导入 mediapipe", test_mediapipe_import()))
    results.append(("新版 API", test_new_api()))
    results.append(("姿态检测器", test_pose_landmarker()))
    results.append(("图片检测", test_detect_image()))
    results.append(("技能测试", test_expand_to_full_body()))
    
    # 汇总
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")
    
    all_passed = all(passed for _, passed in results)
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过! MediaPipe 新版 API 正常工作")
    else:
        print("⚠️ 部分测试失败，请检查上面的错误信息")
    print("=" * 60)


if __name__ == "__main__":
    main()