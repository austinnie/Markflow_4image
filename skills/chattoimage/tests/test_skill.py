"""
ChatToImage 单元测试
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from skills.chattoimage.skill import Chattoimage


class TestChattoimage(unittest.TestCase):
    """
    Chattoimage 测试类
    """

    def setUp(self):
        """测试前准备"""
        self.skill = Chattoimage()

    def test_execute_with_valid_params(self):
        """测试正常执行"""
        result = self.skill.execute(message="", image_path="", model='qwen2.5:7b', api_type='ollama', api_base='http://localhost:11434', api_key="", stream='false')
        self.assertEqual(result.get("status"), "success")
        self.assertIn("result", result)

    def test_skill_metadata(self):
        """测试技能元数据"""
        self.assertEqual(self.skill.name, "ChatToImage")
        self.assertIsInstance(self.skill.version, str)


if __name__ == "__main__":
    unittest.main()