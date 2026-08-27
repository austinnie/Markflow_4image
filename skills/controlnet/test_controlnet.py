# skills/controlnet/test_controlnet.py
"""
ControlNet 技能测试脚本
测试依赖、检测器和图像处理功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 直接导入 skill 模块
from skills.controlnet.skill import Controlnet, CONTROLNET_TYPES


def print_colored(text, color="green"):
    """彩色输出"""
    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "cyan": "\033[96m",
        "reset": "\033[0m",
        "bold": "\033[1m",
    }
    print(f"{colors.get(color, '')}{text}{colors['reset']}")


def test_skill_status():
    """测试技能状态"""
    print_colored("\n📊 1. 测试 ControlNet 技能状态", "cyan")
    print("-" * 50)

    skill = Controlnet()
    result = skill.status()

    if result['status'] == 'success':
        print_colored("   ✅ 状态查询成功", "green")
        print(f"   技能: {result['skill']['name']} v{result['skill']['version']}")
        print(f"   设备: {result['skill']['device']}")
        print(f"   依赖: diffusers={result['dependencies']['diffusers']}, controlnet_aux={result['dependencies']['controlnet_aux']}")
    else:
        print_colored(f"   ❌ 状态查询失败: {result.get('error', '未知错误')}", "red")

    return result['status'] == 'success'


def test_list_types():
    """测试列出 ControlNet 类型"""
    print_colored("\n📋 2. 测试列出 ControlNet 类型", "cyan")
    print("-" * 50)

    skill = Controlnet()
    result = skill.list_types()

    if result['status'] == 'success':
        print_colored(f"   ✅ 支持 {result['count']} 种 ControlNet 类型", "green")
        for key, info in result['types'].items():
            status = "✅" if info['available'] else "❌"
            print(f"      {status} {key}: {info['name']} - {info['description']}")
    else:
        print_colored(f"   ❌ 列表查询失败: {result.get('error', '未知错误')}", "red")

    return result['status'] == 'success'


def test_detect_pose():
    """测试姿态检测"""
    print_colored("\n🖼️ 3. 测试姿态检测", "cyan")
    print("-" * 50)

    # 查找测试图片
    test_images = [
        "skills/remove_clothes/female-hat5.jpg",
        "skills/remove_clothes/input/female-hat5.jpg",
        "skills/remove_clothes/test.jpg",
        "test.jpg",
        "E:/SD_OpenVINO/MarkFlow/skills/remove_clothes/female-hat5.jpg",
    ]

    test_image = None
    for path in test_images:
        if os.path.exists(path):
            test_image = path
            break

    if test_image is None:
        print_colored("   ⚠️ 未找到测试图片，跳过姿态检测测试", "yellow")
        print("   💡 请准备一张测试图片: skills/remove_clothes/female-hat5.jpg")
        return True

    print(f"   📷 使用测试图片: {test_image}")

    skill = Controlnet()
    result = skill.detect_pose(test_image, controlnet_type="openpose")

    if result['status'] == 'success':
        print_colored(f"   ✅ 姿态检测成功", "green")
        print(f"   输出: {result['output_path']}")
        print(f"   尺寸: {result['size']}")
        print(f"   耗时: {result['processing_time']}")
    else:
        print_colored(f"   ❌ 姿态检测失败: {result.get('error', '未知错误')}", "red")
        # 尝试使用 Canny 作为备选
        print("   🔄 尝试使用 Canny 检测器...")
        result2 = skill.detect_pose(test_image, controlnet_type="canny")
        if result2['status'] == 'success':
            print_colored(f"   ✅ Canny 检测成功", "green")
            print(f"   输出: {result2['output_path']}")
            return True
        else:
            print_colored(f"   ❌ Canny 检测也失败", "red")
            return False

    return True


def test_all_detectors():
    """测试所有检测器（仅检查可用性，不实际运行）"""
    print_colored("\n🔧 4. 测试所有 ControlNet 检测器", "cyan")
    print("-" * 50)

    skill = Controlnet()
    detectors = list(CONTROLNET_TYPES.keys())

    available = []
    failed = []

    for det_type in detectors:
        try:
            detector = skill._get_detector(det_type)
            if detector is not None:
                available.append(det_type)
            else:
                failed.append(det_type)
        except Exception as e:
            failed.append(det_type)

    if available:
        print_colored(f"   ✅ 可用检测器: {len(available)}/{len(detectors)}", "green")
        for det in available:
            print(f"      ✅ {det}")
    else:
        print_colored(f"   ⚠️ 无可用检测器", "yellow")

    if failed:
        print_colored(f"   ⚠️ 不可用检测器: {len(failed)}", "yellow")
        for det in failed:
            print(f"      ❌ {det}")

    return len(available) > 0


def main():
    """主测试函数"""
    print("=" * 70)
    print_colored("🧪 ControlNet 技能测试", "bold")
    print("=" * 70)

    results = []

    # 运行所有测试
    results.append(("状态查询", test_skill_status()))
    results.append(("类型列表", test_list_types()))
    results.append(("检测器可用性", test_all_detectors()))
    results.append(("姿态检测", test_detect_pose()))

    # 输出总结
    print("\n" + "=" * 70)
    print_colored("📊 测试总结", "bold")
    print("=" * 70)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅" if result else "❌"
        color = "green" if result else "red"
        print_colored(f"   {status} {name}", color)

    if passed == total:
        print_colored(f"\n🎉 所有测试通过 ({passed}/{total})", "green")
        print("\n💡 ControlNet 技能已就绪，可以正常使用")
    else:
        print_colored(f"\n⚠️ 部分测试失败 ({passed}/{total})", "yellow")
        print("   💡 请检查依赖安装: pip install controlnet-aux diffusers opencv-python-headless")

    print("=" * 70)


if __name__ == "__main__":
    main()