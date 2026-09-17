import unittest
from unittest.mock import patch

from smart_kit.testing.utils import Environment


class TestEnvironment(unittest.TestCase):
    @patch("smart_kit.configs.get_app_config")
    def test_initialization_and_type_casting(self, get_app_config):
        environment = Environment()
        self.assertIs(environment.config, get_app_config.return_value)
        environment.message_id = "42"
        environment.new_session = "false"
        environment.chat_id = 123
        environment.character_name = "Сбер"

        self.assertEqual(environment.message_id, 42)
        self.assertIs(environment.new_session, False)
        self.assertEqual(environment.chat_id, "123")
        self.assertEqual(environment.character_name, "Сбер")
        self.assertEqual(environment.as_dict["messageId"], 42)
