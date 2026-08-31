"""
ImageRecognizer 单元测试
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from skills.imagerecognizer.skill import Imagerecognizer


class TestImagerecognizer(unittest.TestCase):
    """
    Imagerecognizer 测试类
    """

    def setUp(self):
        """测试前准备"""
        self.skill = Imagerecognizer()

    def test_execute_with_valid_params(self):
        """测试正常执行"""
        result = self.skill.execute(image_path="", language='zh', detail_level='standard', translate_to="", save_result='true')
        self.assertEqual(result.get("status"), "success")
        self.assertIn("result", result)

    def test_skill_metadata(self):
        """测试技能元数据"""
        self.assertEqual(self.skill.name, "ImageRecognizer")
        self.assertIsInstance(self.skill.version, str)


if __name__ == "__main__":
    unittest.main()